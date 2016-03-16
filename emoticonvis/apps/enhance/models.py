import random
import math
import re
import numpy

from operator import itemgetter

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Count

from fields import PositiveBigIntegerField
from emoticonvis.apps.corpus.models import Message, Dataset
from emoticonvis.apps.base import models as base_models
from emoticonvis.apps.corpus import utils



# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


class Dictionary(models.Model):
    name = models.CharField(max_length=100)
    dataset = models.ForeignKey(Dataset, related_name="dictionary", null=True, blank=True, default=None)
    settings = models.TextField()

    time = models.DateTimeField(auto_now_add=True)

    num_docs = PositiveBigIntegerField(default=0)
    num_pos = PositiveBigIntegerField(default=0)
    num_nnz = PositiveBigIntegerField(default=0)

    @property
    def feature_count(self):
        return self.features.filter(source__isnull=True).count()

    def get_user_feature_count(self, source):
        feature_num = 0
        if source is not None:
            feature_num += source.features.filter(valid=True).count()
        return feature_num

    def get_feature_list(self, source=None):
        features = []
        if source is None:
            features = list(self.features.filter(source__isnull=True).all())
        else:
            features = list(source.features.filter(valid=True).all())
        return features

    @property
    def gensim_dictionary(self):
        if not hasattr(self, '_gensim_dict'):
            setattr(self, '_gensim_dict', self._make_gensim_dictionary())
        return getattr(self, '_gensim_dict')

    def get_feature_id(self, bow_index):
        if not hasattr(self, '_index2id'):
            g = self.gensim_dictionary
        try:
            return self._index2id[bow_index]
        except KeyError:
            return None

    def _make_gensim_dictionary(self):

        logger.info("Building gensim dictionary from database")

        setattr(self, '_index2id', {})

        from gensim import corpora

        gensim_dict = corpora.Dictionary()
        gensim_dict.num_docs = self.num_docs
        gensim_dict.num_pos = self.num_pos
        gensim_dict.num_nnz = self.num_nnz

        for feature in self.features.all():
            self._index2id[feature.index] = feature.id
            gensim_dict.token2id[feature.text] = feature.index
            gensim_dict.dfs[feature.index] = feature.document_frequency

        logger.info("Dictionary contains %d features" % len(gensim_dict.token2id))

        return gensim_dict


    @classmethod
    def _create_from_texts(cls, tokenized_texts, name, dataset, settings, minimum_frequency=2):
        from gensim.corpora import Dictionary as GensimDictionary

        # build a dictionary of features
        logger.info("Creating features (including n-grams) from texts")
        gemsim_dictionary = GensimDictionary(tokenized_texts)

        # Remove extremely rare features
        logger.info("Features dictionary contains %d features. Filtering..." % len(gemsim_dictionary.token2id))
        gemsim_dictionary.filter_extremes(no_below=minimum_frequency, no_above=1, keep_n=None)
        gemsim_dictionary.compactify()
        logger.info("Features Dictionary contains %d features." % len(gemsim_dictionary.token2id))

        dict_model = cls(name=name,
                         dataset=dataset,
                         settings=settings)
        dict_model.save()

        dict_model._populate_from_gensim_dictionary(gemsim_dictionary)

        return dict_model


    def _populate_from_gensim_dictionary(self, gensim_dict):

        self.num_docs = gensim_dict.num_docs
        self.num_pos = gensim_dict.num_pos
        self.num_nnz = gensim_dict.num_nnz
        self.save()

        logger.info("Saving gensim dictionary '%s' in the database" % self.name)

        batch = []
        count = 0
        print_freq = 10000
        batch_size = 1000
        total_features = len(gensim_dict.token2id)

        for token, id in gensim_dict.token2id.iteritems():
            feature = Feature(dictionary=self,
                        text=token,
                        index=id,
                        document_frequency=gensim_dict.dfs[id])
            batch.append(feature)
            count += 1

            if len(batch) > batch_size:
                Feature.objects.bulk_create(batch)
                batch = []

                if settings.DEBUG:
                    # prevent memory leaks
                    from django.db import connection

                    connection.queries = []

            if count % print_freq == 0:
                logger.info("Saved %d / %d features in the database dictionary" % (count, total_features))

        if len(batch):
            Feature.objects.bulk_create(batch)
            count += len(batch)

            logger.info("Saved %d / %d features in the database dictionary" % (count, total_features))

        return self


    def _vectorize_corpus(self, queryset, tokenizer):

        import math

        logger.info("Saving document features vectors in corpus.")

        total_documents = self.num_docs
        gdict = self.gensim_dictionary
        count = 0
        total_count = queryset.count()
        batch = []
        batch_size = 1000
        print_freq = 10000

        for msg in queryset.iterator():
            tokens = tokenizer.tokenize(msg)
            bow = gdict.doc2bow(tokens)

            for feature_index, feature_freq in bow:
                feature_id = Feature.objects.filter(index=feature_index).first()

                document_freq = gdict.dfs[feature_index]

                num_tokens = len(tokens)
                tf = float(feature_freq) / float(num_tokens)
                idf = math.log(total_documents / document_freq)
                tfidf = tf * idf
                batch.append(MessageFeature(dictionary=self,
                                         feature=feature_id,
                                         feature_index=feature_index,
                                         count=feature_freq,
                                         tfidf=tfidf,
                                         message=msg))
            count += 1

            if len(batch) > batch_size:
                MessageFeature.objects.bulk_create(batch)
                batch = []

                if settings.DEBUG:
                    # prevent memory leaks
                    from django.db import connection

                    connection.queries = []

            if count % print_freq == 0:
                logger.info("Saved feature-vectors for %d / %d documents" % (count, total_count))

        if len(batch):
            MessageFeature.objects.bulk_create(batch)
            logger.info("Saved feature-vectors for %d / %d documents" % (count, total_count))

        logger.info("Created %d feature vector entries" % count)


    def load_sparse_matrix(self, use_tfidf=True):

        message_id_list = []
        results = []

        messages = self.dataset.message_set.all()

        for msg in messages:
            message_id_list.append(msg.id)
            results.append(map(lambda x: x.to_tuple(use_tfidf), msg.feature_scores.filter(dictionary=self).all()))

        return message_id_list, results

    def add_feature(self, token_list, source=None):

        clean_token_list = []
        for f in token_list:
            clean_f =  re.sub('[\s+]', ' ', f)
            clean_token_list.append(clean_f)

        dataset = self.dataset
        queryset = dataset.message_set.all()

        # 1. Calculate the document_frequency
        document_freq = 0
        for msg in queryset.iterator():
            found = self.is_user_feature_in_message(clean_token_list, msg)
            if found:
                document_freq += 1

        # 2. Create a new instance of Feature
        index = self.get_last_feature_index() + 1
        token = "&".join(clean_token_list)
        feature = Feature(dictionary=self,
                        text=token,
                        index=index,
                        source=source,
                        document_frequency=document_freq)
        feature.save()

        # 3. Connect Features with Message through MessageFeature
        total_documents = self.num_docs
        count = 0
        total_count = queryset.count()
        batch = []
        batch_size = 1000
        print_freq = 10000
        for msg in queryset.iterator():
            found = self.is_user_feature_in_message(clean_token_list, msg)
            if found is False:
                continue

            feature_freq = 1 # For now
            num_tokens = msg.tweet_words.count()
            tf = float(feature_freq) / float(num_tokens)
            idf = math.log(total_documents / document_freq)
            tfidf = tf * idf
            batch.append(MessageFeature(dictionary=self,
                                        feature=feature,
                                        feature_index=feature.index,
                                        count=feature_freq,
                                        tfidf=tfidf,
                                        message=msg))

            count += 1

            if len(batch) > batch_size:
                MessageFeature.objects.bulk_create(batch)
                batch = []

                if settings.DEBUG:
                    # prevent memory leaks
                    from django.db import connection
                    connection.queries = []

            if count % print_freq == 0:
                logger.info("Saved feature-vectors for %d / %d documents" % (count, total_count))

        if len(batch):
            MessageFeature.objects.bulk_create(batch)
            logger.info("Saved feature-vectors for %d / %d documents" % (count, total_count))

        logger.info("Created %d feature vector entries" % count)

        return feature

    def get_last_feature_index(self):
        last_feature = Feature.objects.filter(dictionary_id=self.id).order_by('-index').first()
        return last_feature.index

    def is_user_feature_in_message(self, token_list, message):
        found = True
        clean_message = str(message).replace('\n', ' ')
        for s in token_list:
            pattern_string = '.*'
            s_re = s.replace(' ', '[\s]+')
            pattern_string += s_re + '.*'
            p = re.compile(pattern_string, re.IGNORECASE)
            found &= (p.search(clean_message) is not None)
        return found

class Feature(models.Model):
    dictionary = models.ForeignKey(Dictionary, related_name='features')
    index = models.IntegerField()
    text = base_models.Utf8CharField(max_length=150)
    document_frequency = models.IntegerField()

    messages = models.ManyToManyField(Message, through='MessageFeature', related_name='features')
    source = models.ForeignKey(User, related_name="features", default=None)

    created_at = models.DateTimeField(auto_now_add=True, default=None)
    """The code created time"""

    last_updated = models.DateTimeField(auto_now_add=True, auto_now=True, default=None)
    """The code updated time"""

    valid = models.BooleanField(default=True)
    """ Whether this code is valid (False indicate the feature has been removed) """

    def __repr__(self):
        return self.text

    def __unicode__(self):
        return self.__repr__()

    def get_distribution(self, code_source=None):

        codes = Code.objects.all()
        distribution = []
        for code in codes:
            count = self.messages.filter(code_assignments__code=code, code_assignments__source=code_source, code_assignments__valid=True).count()
            distribution.append({"code_id": code.id,
                           "code_text": code.text,
                           "count": count})

        return {"feature_index": self.index,
                "feature_text": self.text,
                "distribution": distribution}



class MessageFeature(models.Model):
    class Meta:
        index_together = (
            ('message', 'feature'),
        )

    dictionary = models.ForeignKey(Dictionary, db_index=False)

    feature = models.ForeignKey(Feature, related_name="message_scores")
    message = models.ForeignKey(Message, related_name='feature_scores', db_index=False)

    feature_index = models.IntegerField()
    count = models.FloatField()
    tfidf = models.FloatField()

    def to_tuple(self, use_tfidf=True):
        return (self.feature_index, self.tfidf) if use_tfidf else (self.dic_token_index, self.count)

    def to_libsvm_tuple(self, use_tfidf=True):
        if use_tfidf:
            return"%d:%f" %(int(self.feature_id), float(self.tfidf))
        else:
            return"%d:%f" %(int(self.feature_id), float(self.count))



class TweetWord(models.Model):
    dataset = models.ForeignKey(Dataset, related_name="tweet_words", null=True, blank=True, default=None)
    original_text = base_models.Utf8CharField(max_length=100, db_index=True, blank=True, default="")
    pos = models.CharField(max_length=4, null=True, blank=True, default="")
    text = base_models.Utf8CharField(max_length=100, db_index=True, blank=True, default="")
    messages = models.ManyToManyField(Message, related_name='tweet_words', through="TweetWordMessageConnection")

    def __repr__(self):
        return self.text

    def __unicode__(self):
        return self.__repr__()

    @property
    def related_features(self):
        return TweetWord.objects.filter(dataset=self.dataset, text=self.text).all()

    @property
    def all_messages(self):
        queryset = self.dataset.message_set.all()
        queryset = queryset.filter(utils.levels_or("tweet_words__id", map(lambda x: x.id, self.related_features)))
        return queryset

class TweetWordMessageConnection(models.Model):
    message = models.ForeignKey(Message, related_name="tweetword_connections")
    tweet_word = models.ForeignKey(TweetWord, related_name="tweetword_connections")
    order = models.IntegerField()

    class Meta:
        ordering = ["message", "order", ]
        unique_together = ('message', 'tweet_word', 'order', )


