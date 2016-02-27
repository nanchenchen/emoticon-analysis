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
from msgvis.apps.corpus.models import Message, Dataset, Code
from msgvis.apps.base import models as base_models
from msgvis.apps.corpus import utils



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

    def load_to_scikit_learn_format(self, training_portion=0.80, use_tfidf=True, source=None):
        messages = map(lambda x: x, self.dataset.message_set.all().order_by('id'))
        count = len(messages)
        training_data_num = int(round(float(count) * training_portion))
        testing_data_num = count - training_data_num
        features = list(self.features.filter(source__isnull=True).all())
        if source is not None:
            features += list(source.features.filter(valid=True).all())
        features.sort(key=lambda x: x.index)
        feature_num = self.features.order_by('index').last().index + 1 
        codes = self.dataset.message_set.select_related('code').values('code_id', 'code__text').distinct()
        code_num = codes.count()

        random.shuffle(messages)

        training_data = messages[:training_data_num]
        testing_data = messages[training_data_num:]

        data = {
            'training': {
                'id': [],
                'X': numpy.zeros((training_data_num, feature_num), dtype=numpy.float64),
                'y': [],
                'group_by_codes': map(lambda x: [], range(code_num)),
                'mean': numpy.zeros((code_num, feature_num)),
                'var': numpy.zeros((code_num, feature_num)),
            },
            'testing': {
                'id': [],
                'X': numpy.zeros((testing_data_num, feature_num), dtype=numpy.float64),
                'y': [],
                'group_by_codes': map(lambda x: [], range(code_num)),
                'mean': numpy.zeros((code_num, feature_num)),
                'var': numpy.zeros((code_num, feature_num)),
            },
            'meta': {
                'features': [],
                'codes': []
            }
        }
        for idx, msg in enumerate(training_data):
            code_id = msg.code.id if msg.code else 0
            for feature_score in msg.feature_scores.filter(dictionary=self).all():
                if (feature_score.feature.source is None) \
                   or (( source is not None ) and (feature_score.feature.filter(source=source, valid=True))):
                   data['training']['X'][idx, feature_score.feature_index] = feature_score.tfidf if use_tfidf else feature_score.count
            data['training']['group_by_codes'][code_id - 1].append(data['training']['X'][idx])

            data['training']['y'].append(code_id)
            data['training']['id'].append(msg.id)

        for idx, msg in enumerate(testing_data):
            code_id = msg.code.id if msg.code else 0
            for feature_score in msg.feature_scores.filter(dictionary=self).all():
                if (feature_score.feature.source is None) \
                   or (( source is not None ) and (feature_score.feature.filter(source=source, valid=True))):
                    data['testing']['X'][idx, feature_score.feature_index] = feature_score.tfidf if use_tfidf else feature_score.count

            data['testing']['group_by_codes'][code_id - 1].append(data['testing']['X'][idx])
            data['testing']['y'].append(code_id)
            data['testing']['id'].append(msg.id)


        for code in codes:
            data['meta']['codes'].append({'index': code['code_id'] - 1,
                                          'text': code['code__text']})
            code_idx = code['code_id'] - 1
            data['training']['mean'][code_idx] = numpy.mean(data['training']['group_by_codes'][code_idx], axis=0)
            data['training']['var'][code_idx] = numpy.var(data['training']['group_by_codes'][code_idx], axis=0)
            data['testing']['mean'][code_idx] = numpy.mean(data['testing']['group_by_codes'][code_idx], axis=0)
            data['testing']['var'][code_idx] = numpy.var(data['testing']['group_by_codes'][code_idx], axis=0)

        for feature in features:
            text = feature.text
            if text.find('&') > 0:
                text = text.replace('&', ', ')
                text = '[' + text + ']'
            data['meta']['features'].append({'index': feature.index,
                                          'text': text.replace('_', ' '),
                                          'count': feature.document_frequency})

        return data

    def do_training(self, source=None):
        data = self.load_to_scikit_learn_format(training_portion=0.50, use_tfidf=False, source=source)

        from sklearn import svm
        lin_clf = svm.LinearSVC()
        trainingInput = data['training']['X']
        trainingOutput = data['training']['y']

        lin_clf.fit(trainingInput, trainingOutput)

        # get predictions
        prediction = lin_clf.predict(trainingInput)
        distances = lin_clf.decision_function(trainingInput)

        if hasattr(lin_clf, "predict_proba"):
            prob = lin_clf.predict_proba(trainingInput)[:, 1]
        else:  # use decision function
            prob = lin_clf.decision_function(trainingInput)
            min = prob.min()
            max = prob.max()
            prob = \
                (prob - min) / (max - min)

        results = {
            'codes': [],
            'features': [],
            'train_id': data['training']['id'],
            'test_id': data['testing']['id'],
            'accuracy': {
                'training': lin_clf.score(data['training']['X'], data['training']['y']),
                'testing': 0.0 # lin_clf.score(data['testing']['X'], data['testing']['y'])
            },
            'predictions': [x-1 for x in prediction],
            'probabilities': prob,
            'labels': [x-1 for x in trainingOutput]
        }

        for code in data['meta']['codes']:
            results['codes'].append({
                'index': code['index'],
                'text': code['text'],
                'train_count': len(data['training']['group_by_codes'][code['index']]),
                'test_count': len(data['testing']['group_by_codes'][code['index']]),
                'domain': [0, 0]
            })


        order = numpy.zeros(lin_clf.coef_.shape)
        for code in data['meta']['codes']:
            cl = sorted(map(lambda x: x, enumerate(lin_clf.coef_[code['index']])), key=itemgetter(1), reverse=True)
            for idx, item in enumerate(cl):
                order[code['index']][item[0]] = idx


        for feature in data['meta']['features']:
            in_top_features = 0

            row = {
                'feature_index': feature['index'],
                'feature': feature['text'],
                'count': feature['count'],
                'codes': {}
            }

            for idx, code in enumerate(data['meta']['codes']):
                row['codes'][code['text']] = {
                    'weight': lin_clf.coef_[code['index']][feature['index']],
                    'mean': data['training']['mean'][code['index']][feature['index']],
                    'var': data['training']['var'][code['index']][feature['index']],
                    'order': order[code['index']][feature['index']]
                }
                max_domain = data['training']['mean'][code['index']][feature['index']] + 3 * math.sqrt(data['training']['var'][code['index']][feature['index']])
                if max_domain > results['codes'][idx]['domain'][1]:
                   results['codes'][idx]['domain'][1] = max_domain
                in_top_features += 1 if order[code['index']][feature['index']] < 20 else 0
            row['in_top_features'] = in_top_features

            results['features'].append(row)

        return results

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


