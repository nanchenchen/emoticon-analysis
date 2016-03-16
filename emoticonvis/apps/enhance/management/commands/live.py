from django.core.management.base import BaseCommand, make_option, CommandError
from time import time
import path
from django.db import transaction
import csv
import codecs
from operator import itemgetter

import logging
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Live."
    args = '<dictionary_id>'
    option_list = BaseCommand.option_list + (
    #    make_option('-a', '--action',
    #                default='all',
    #                dest='action',
    #                help='Action to run [all|similarity]'
    #    ),

    )

    def handle(self, dictionary_id, **options):

        if not dictionary_id:
            raise CommandError("Dataset id is required.")
        try:
            dictionary_id = int(dictionary_id)
        except ValueError:
            raise CommandError("Dataset id must be a number.")

        action = options.get('action')

        from emoticonvis.apps.enhance.models import Dictionary
        dictionary = Dictionary.objects.get(id=dictionary_id)
        data = dictionary.load_to_scikit_learn_format(training_portion=0.50, use_tfidf=False)

        from sklearn.multiclass import OneVsOneClassifier
        from sklearn.svm import LinearSVC
        OneVsOneClassifier(LinearSVC(random_state=0)).fit(data['training']['X'], data['training']['y'])

        from sklearn import svm
        clf = svm.SVC()
        clf.fit(data['training']['X'], data['training']['y'])
        lin_clf = svm.LinearSVC()
        lin_clf.fit(data['training']['X'], data['training']['y'])

        #import json
        #with open('../datasets/feature_weight.json', 'w') as fp:
        #    print >> fp, json.dumps(lin_clf.coef_.tolist())

        print "Training"
        print "=========="
        print "Distribution:"
        for code in data['meta']['codes']:
            print "%s: %d" % (code['text'], len(data['training']['group_by_codes'][code['index']]))
        print "Accuracy: %f" %lin_clf.score(data['training']['X'], data['training']['y'])

        print ""

        print "Testing"
        print "=========="
        print "Distribution:"
        for code in data['meta']['codes']:
            print "%s: %d" % (code['text'], len(data['testing']['group_by_codes'][code['index']]))
        print "Accuracy: %f" %lin_clf.score(data['testing']['X'], data['testing']['y'])

        summary = []
        header = ["word_index", "word", "count"]
        for code in data['meta']['codes']:
            header.append(code['text'] + '_weight')
            header.append(code['text'] + '_mean')
            header.append(code['text'] + '_var')
            header.append(code['text'] + '_order')
        header.append('#in_top_features')
        summary.append(header)

        import numpy
        order = numpy.zeros(lin_clf.coef_.shape)
        for code in data['meta']['codes']:
            cl = sorted(map(lambda x: x, enumerate(lin_clf.coef_[code['index']])), key=itemgetter(1), reverse=True)
            for idx, item in enumerate(cl):
                order[code['index']][item[0]] = idx


        for word in data['meta']['features']:
            row = [word['index'], word['text'], word['count']]
            in_top_features = 0
            for code in data['meta']['codes']:
                row.append(lin_clf.coef_[code['index']][word['index']]) # weight
                row.append(data['training']['mean'][code['index']][word['index']]) # mean
                row.append(data['training']['var'][code['index']][word['index']]) # var
                row.append(order[code['index']][word['index']]) # order
                in_top_features += 1 if order[code['index']][word['index']] < 10 else 0
            row.append(in_top_features)
            summary.append(row)

        with codecs.open('../datasets/summary_dict_%s.csv' %(dictionary_id), encoding='utf-8', mode='w') as csvfile:
            csvwriter = csv.writer(csvfile, delimiter=',',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for row in summary:
                csvwriter.writerow(row)

        import pdb
        pdb.set_trace()