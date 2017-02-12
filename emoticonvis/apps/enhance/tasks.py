import logging

import codecs
import re
from time import time
import subprocess
import glob

from bulk_update.helper import bulk_update
from nltk.stem import WordNetLemmatizer
from langdetect import detect

from models import Dictionary, Feature, MessageFeature, TweetWord, TweetWordMessageConnection
from emoticonvis.apps.corpus.models import Dataset, Message

logger = logging.getLogger(__name__)

__all__ = ['get_twitter_context', 'get_chat_context', 'Dictionary']

_stoplist = None


def get_stoplist():
    global _stoplist
    if not _stoplist:
        from nltk.corpus import stopwords

        _stoplist = stopwords.words('english')
    return _stoplist


class DbTextIterator(object):
    def __init__(self, queryset):
        self.queryset = queryset
        self.current_position = 0
        self.current = None

    def __iter__(self):
        self.current_position = 0
        for msg in self.queryset.iterator():
            self.current = msg
            self.current_position += 1
            if self.current_position % 10000 == 0:
                logger.info("Iterating through database texts: item %d" % self.current_position)

            #yield msg.text
            yield msg


class DbWordVectorIterator(object):
    def __init__(self, dictionary, freq_field='tfidf'):
        self.dictionary = dictionary
        self.freq_field = freq_field
        self.current_message_id = None
        self.current_vector = None

    def __iter__(self):
        qset = MessageFeature.objects.filter(dictionary=self.dictionary).order_by('message')
        self.current_message_id = None
        self.current_vector = []
        current_position = 0
        for mw in qset.iterator():
            message_id = mw.message_id
            word_idx = mw.word_index
            freq = getattr(mw, self.freq_field)

            if self.current_message_id is None:
                self.current_message_id = message_id
                self.current_vector = []

            if self.current_message_id != message_id:
                yield self.current_vector
                self.current_vector = []
                self.current_message_id = message_id
                current_position += 1

                if current_position % 10000 == 0:
                    logger.info("Iterating through database word-vectors: item %d" % current_position)

            self.current_vector.append((word_idx, freq))

        # one more extra one
        yield self.current_vector

    def __len__(self):
        from django.db.models import Count

        count = MessageFeature.objects \
            .filter(dictionary=self.dictionary) \
            .aggregate(Count('message', distinct=True))

        if count:
            return count['message__count']


class Tokenizer(object):
    def __init__(self, texts, lemmatizer, *filters):
        """
        Filters is a list of objects which can be used like sets
        to determine if a word should be removed: if word in filter, then word will
        be ignored.
        """
        self.texts = texts
        self.lemmatizer = lemmatizer
        self.filters = filters
        self.max_length = Feature._meta.get_field('text').max_length

    def __iter__(self):
        if self.texts is None:
            raise RuntimeError("Tokenizer can only iterate if given texts")

        for text in self.texts:
            tokenized_words = self.tokenize(text)
            if self.lemmatizer:
                tokenized_words = map(lambda x: self.lemmatizer.lemmatize(x), tokenized_words)
            yield tokenized_words

    def tokenize(self, text):
        words = []

        for word in self.split(text.lower()):

            if self.lemmatizer:
                word = self.lemmatizer.lemmatize(word)

            filter_out = False
            for f in self.filters:
                if word in f:
                    filter_out = True
                    break

            if filter_out:
                # skip this word
                continue

            if len(word) >= self.max_length:
                word = word[:self.max_length - 1]

            words.append(word)

        return words

    def split(self, text):
        return text.split()

    def extend_to_ngram(self, tokens, n=3):
        results = tokens[:]
        for i in range(1, len(tokens)):
            bigram = "%s_%s" %(tokens[i - 1], tokens[i])
            results.append(bigram)
            if i >= 2:
                trigram = "%s_%s_%s" % (tokens[i - 2], tokens[i - 1], tokens[i])
                results.append(trigram)
        return results

class WordTokenizer(Tokenizer):
    def __init__(self, *args, **kwargs):
        super(WordTokenizer, self).__init__(*args, **kwargs)

        import nltk

        self._tokenize = nltk.word_tokenize

    def split(self, text):
        return self._tokenize(text)


class SimpleTokenizer(Tokenizer):
    def __init__(self, *args, **kwargs):
        super(SimpleTokenizer, self).__init__(*args, **kwargs)

        from nltk.tokenize import sent_tokenize, wordpunct_tokenize
        self._sent_tokenize = sent_tokenize
        self._tokenize = wordpunct_tokenize

        import re
        self._strip_punct = re.compile(r'[^\w\s]')

    def split(self, text):
        # split into sentence, then remove all punctuation
        sents = (self._strip_punct.sub('', sent) for sent in self._sent_tokenize(text))
        # then split on non-words
        return [token for sent in sents for token in self._tokenize(sent)]

class TweetParserTokenizer(Tokenizer):
    def __init__(self, *args, **kwargs):
        super(TweetParserTokenizer, self).__init__(*args, **kwargs)

    def tokenize(self, message):

        words = []

        for word in message.tweet_words.all():
            word = word.text

            filter_out = False
            for f in self.filters:
                if word in f:
                    filter_out = True
                    break

            if filter_out:
                # skip this word
                continue

            if len(word) >= self.max_length:
                word = word[:self.max_length - 1]

            words.append(word)

        # extend to n-gram (trigram by default)
        words = self.extend_to_ngram(words)

        return words

    def split(self, message):
        return self.tokenize(message)

class FeatureContext(object):
    def __init__(self, name, queryset, tokenizer, lemmatizer, filters, minimum_frequency=4):
        self.name = name
        self.queryset = queryset
        self.tokenizer = tokenizer
        self.lemmatizer = lemmatizer
        self.filters = filters
        self.minimum_frequency = minimum_frequency

    def queryset_str(self):
        return str(self.queryset.query)

    def get_dict_settings(self):
        settings = dict(
            name=self.name,
            tokenizer=self.tokenizer.__name__,
            dataset=self.queryset_str(),
            filters=repr(self.filters),
            minimum_frequency=self.minimum_frequency
        )

        import json

        return json.dumps(settings, sort_keys=True)

    # This method doesn't work in a different environment as the instances
    # of filters have a different string representation
    def find_dictionary(self):
        results = Dictionary.objects.filter(settings=self.get_dict_settings())
        return results.last()

    def find_dictionary_by_name_dataset(self, name, dataset_id):
        results = Dictionary.objects.filter(name=name, dataset_id=dataset_id)
        return results.last()


    def build_dictionary(self, dataset_id):
        texts = DbTextIterator(self.queryset)

        tokenized_texts = self.tokenizer(texts, self.lemmatizer, *self.filters)

        dataset = Dataset.objects.get(pk=dataset_id)
        return Dictionary._create_from_texts(tokenized_texts=tokenized_texts,
                                             name=self.name,
                                             dataset=dataset,
                                             minimum_frequency=self.minimum_frequency,
                                             settings=self.get_dict_settings())

    def bows_exist(self, dictionary):
        return MessageFeature.objects.filter(dictionary=dictionary).exists()


    def build_bows(self, dictionary):
        texts = DbTextIterator(self.queryset)
        tokenized_texts = self.tokenizer(texts, self.lemmatizer, *self.filters)

        dictionary._vectorize_corpus(queryset=self.queryset,
                                     tokenizer=tokenized_texts)


class LambdaWordFilter(object):
    def __init__(self, fn):
        self.fn = fn

    def __contains__(self, item):
        return self.fn(item)

def standard_features_pipeline(context, dataset_id):
    dictionary = context.find_dictionary()
    if dictionary is None:
        dictionary = context.build_dictionary(dataset_id=dataset_id)

    if not context.bows_exist(dictionary):
        context.build_bows(dictionary)

def default_feature_context(name, dataset_id):
    dataset = Dataset.objects.get(pk=dataset_id)
    queryset = dataset.message_set.all()#filter(language__code='en')

    filters = [
        set(get_stoplist()),
        ['ive', 'wasnt', 'didnt', 'dont'],
        LambdaWordFilter(lambda word: word == 'rt' or len(word) <= 2),
        LambdaWordFilter(lambda word: word.startswith('http') and len(word) > 4)
    ]

    return FeatureContext(name=name, queryset=queryset,
                        tokenizer=TweetParserTokenizer,
                        lemmatizer=None,#WordNetLemmatizer(),
                        filters=filters,
                        minimum_frequency=4)


def import_from_tweet_parser_results(dataset_id, filename):
    current_msg_id = -1
    current_msg = None
    word_list = []
    count = 0
    order = 0
    with codecs.open(filename, encoding='utf-8', mode='r') as f:
        print "Reading file %s" % filename

        start = time()
        for line in f:
            if re.search("ID=(\d+)", line):
                # save the previous word list
                if len(word_list) > 0:
                    TweetWordMessageConnection.objects.bulk_create(word_list)
                    word_list = []
                    count += 1
                    order = 0
                    if count % 1000 == 0:
                        print "Processed %d messages" % count
                        print "Time: %.2fs" % (time() - start)
                        start = time()

                results = re.match('ID=(\d+)', line)
                groups = results.groups()
                current_msg_id = int(groups[0])
                #print "current msg id = %d" %(current_msg_id)
                current_msg = Message.objects.get(id=current_msg_id)


            elif re.search("(.+)\t(.+)\t(.+)", line):
                results = re.match('(.+)\t(.+)\t(.+)', line)
                groups = results.groups()
                original_text = groups[0]
                pos = groups[1]
                text = groups[2]
                #if re.search('[,~U]', pos):
                #    continue
                #else:
                word_obj, created = TweetWord.objects.get_or_create(dataset_id=dataset_id, original_text=original_text, pos=pos, text=text)

                order += 1
                word_list.append(TweetWordMessageConnection(message=current_msg, tweet_word=word_obj, order=order))
        # save the previous word list
        if len(word_list) > 0:
            TweetWordMessageConnection.objects.bulk_create(word_list)
            count += 1
            word_list = []
        print "Processed %d messages" % count
        print "Time: %.2fs" % (time() - start)


def dump_tweets(dataset_id, save_path, mode='twitter_parser'):
    dataset = Dataset.objects.get(id=dataset_id)
    #messages = dataset.message_set.all()#.exclude(time__isnull=True)
    messages = dataset.message_set.exclude(participant__id=2)
    messages = messages.filter(type=0)
    total_count = messages.count()

    start = 0
    limit = 10000

    while start < total_count:
        filename = "%s/dataset_%d_message_%d_%d.txt" %(save_path, dataset_id, start, start + limit)
        with codecs.open(filename, encoding='utf-8', mode='w') as f:
            for msg in messages[start:start + limit]:

                try:
                    tweet_id = msg.id
                    #full_name = msg.sender.full_name.lower() if msg.sender.full_name is not None else ""
                    #username = msg.sender.username.lower() if msg.sender.username is not None else ""
                    if mode == 'twitter_parser':
                        text = msg.text.lower()

                        line = "TWEETID%dSTART\n" %(tweet_id)
                        f.write(line)

                        #line = "%s @%s" %(full_name, username)
                        #f.write(line)

                        line = "%s\n" %(text)
                        f.write(line)

                        line = "TWEETID%dEND\n" %(tweet_id)
                        f.write(line)
                    elif mode == 'lang_detection':
                        line = "%d\t%s\n" %(tweet_id, msg.text)
                        f.write(line)

                except:
                    pass

        start += limit

def parse_tweets(tweet_parser_path, input_path, output_path):
    parser_cmd = "%s/runTagger.sh" %tweet_parser_path
    input_files = glob.glob("%s/dataset_*.txt" % input_path)

    for input_file in input_files:
        results = re.search('(dataset_.+)\.txt', input_file)
        filename = results.groups()[0]

        output_file = "%s/%s.out" % (output_path, filename)

        with codecs.open(output_file, encoding='utf-8', mode='w') as f:
            cmd = "%s --output-format conll %s" %(parser_cmd, input_file)
            print cmd
            try:
                subprocess.call(cmd.split(" "), stdout=f, stderr=subprocess.PIPE)
            except:
                pass



def lemmatize_tweets(input_path, output_path):
    wordnet_lemmatizer = WordNetLemmatizer()

    input_files = glob.glob("%s/dataset_*.out" % input_path)

    for input_file in input_files:
        results = re.search('(dataset_.+)\.out', input_file)
        filename = results.groups()[0]

        output_file = "%s/%s_converted.out" % (output_path, filename)
        output_file2 = "%s/%s_converted.out.id" % (output_path, filename)

        with codecs.open(output_file, encoding='utf-8', mode='w') as out:
            with codecs.open(output_file2, encoding='utf-8', mode='w') as out2:
                print >>out, "<doc>"
                with codecs.open(input_file, encoding='utf-8', mode='r') as f:
                    for line in f:
                        if re.search('TWEETID(\d+)START', line):
                            results = re.match('TWEETID(\d+)START', line)
                            groups = results.groups()
                            print >>out, "<p>"
                            print >>out2, "ID=%d" %(int(groups[0]))

                        elif re.search('TWEETID(\d+)END', line):
                            print >>out, "<\p>"
                        elif re.search("(.+)\t(.+)\t(.+)\n", line):
                            results = re.match("(.+)\t(.+)\t(.+)\n", line)
                            groups = results.groups()
                            word = groups[0]
                            pos = groups[1]
                            lemma = wordnet_lemmatizer.lemmatize(word)
                            print >>out, "%s\t%s\t%s" %(word, pos, lemma)
                            print >>out2, "%s\t%s\t%s" %(word, pos, lemma)

                print >>out, "</doc>"


def run_lang_detection(ldig_path, input_path, output_path):
    ldi_cmd = "python %s/ldig.py" %ldig_path
    model_path = "%s/models/model.latin" %ldig_path
    input_files = glob.glob("%s/dataset_*.txt" % input_path)

    for input_file in input_files:
        results = re.search('(dataset_.+)\.txt', input_file)
        filename = results.groups()[0]

        output_file = "%s/%s.out" % (output_path, filename)

        with codecs.open(output_file, encoding='utf-8', mode='w') as f:
            cmd = "%s -m %s %s" %(ldi_cmd, model_path, input_file)
            print cmd
            try:
                subprocess.call(cmd.split(" "), stdout=f, stderr=subprocess.PIPE)
            except:
                pass

def ori_detect_language(dataset_id):

    dataset = Dataset.objects.get(id=dataset_id)
    total_count = dataset.message_set.count()
    messages = dataset.message_set.exclude(time__isnull=True)
    messages = messages.exclude(participant__id=2)
    messages = messages.filter(type=0)

    start = 0
    limit = 10000

    while start < total_count:

        current_batch = messages[start:start + limit]
        for msg in current_batch:

            try:
                #full_name = msg.sender.full_name.lower() if msg.sender.full_name is not None else ""
                #username = msg.sender.username.lower() if msg.sender.username is not None else ""
                text = msg.text
                detected_lang = detect(text)
                print "[%s] %s" %(detected_lang, text[:20])
                if detected_lang == 'en':
                    msg.detected_language = 'En'
                elif detected_lang == 'fr':
                    msg.detected_language = 'Fr'

            except:
                import traceback
                traceback.print_exc()
                import pdb
                pdb.set_trace()

        bulk_update(current_batch)
        start += limit