from django.core.management.base import BaseCommand, CommandError
from optparse import make_option

from msgvis.apps.corpus.models import Dataset, Message, Code
from django.db import transaction
import traceback
import sys
import path
from time import time
from django.conf import settings
import csv

class Command(BaseCommand):
    """
    Import a corpus of message data into the database.

    .. code-block :: bash

        $ python manage.py import_corpus <file_path>

    """
    args = '<corpus_filename> [...]'
    help = "Import a corpus into the database."
    option_list = BaseCommand.option_list + (
        make_option('-d', '--dataset',
                    action='store',
                    dest='dataset',
                    help='Set a target dataset to add to'
        ),
    )

    def handle(self, *filenames, **options):

        if len(filenames) == 0:
            raise CommandError('At least one filename must be provided.')

        dataset = options.get('dataset', None)
        if not dataset:
            dataset = filenames[0]

        for f in filenames:
            if not path.path(f).exists():
                raise CommandError("Filename %s does not exist" % f)

        start = time()
        dataset_obj, created = Dataset.objects.get_or_create(name=dataset, description=dataset)
        if created:
            print "Created dataset '%s' (%d)" % (dataset_obj.name, dataset_obj.id)
        else:
            print "Adding to existing dataset '%s' (%d)" % (dataset_obj.name, dataset_obj.id)


        for i, corpus_filename in enumerate(filenames):
            with open(corpus_filename, 'rb') as fp:
                if len(filenames) > 1:
                    print "Reading file %d of %d %s" % (i + 1, len(filenames), corpus_filename)
                else:
                    print "Reading file %s" % corpus_filename

                csvreader = csv.reader(fp, delimiter=',', quotechar='"')
                importer = Importer(csvreader, dataset_obj)
                importer.import_codes()
                importer.run()


        dataset_obj.save()
        
        print "Time: %.2fs" % (time() - start)


class Importer(object):
    commit_every = 100
    print_every = 1000

    def __init__(self, csvreader, dataset):
        self.csvreader = csvreader
        self.dataset = dataset
        self.line = 0
        self.imported = 0
        self.not_tweets = 0
        self.errors = 0
        self.codes = []

    def _import_group(self, rows):
        with transaction.atomic(savepoint=False):
            for cols in rows:

                if len(cols) > 0:
                    try:
                        message = self.create_an_instance_from_csv_cols(cols)
                        if message:
                            self.imported += 1
                        else:
                            self.not_tweets += 1
                    except:
                        self.errors += 1
                        print >> sys.stderr, "Import error on line %d" % self.line
                        traceback.print_exc()

        #if settings.DEBUG:
            # prevent memory leaks
        #    from django.db import connection
        #    connection.queries = []

    def import_codes(self):
        header = self.csvreader.next()
        for i in range(2, len(header)):
            code, created = Code.objects.get_or_create(text=header[i])
            self.codes.append(code)

    def create_an_instance_from_csv_cols(self, cols):
        try:
            message = Message(dataset=self.dataset, ref_id=int(cols[0]), text=cols[1])
            message.save()
            for i in range(2, len(cols)):
                if cols[i] == 'x':
                    message.code = self.codes[i - 2]
            message.save()
            return True
        except:
            return False

    def run(self):
        transaction_group = []

        start = time()

        for cols in self.csvreader:
            self.line += 1

            transaction_group.append(cols)

            if len(transaction_group) >= self.commit_every:
                self._import_group(transaction_group)
                transaction_group = []

            if self.line > 0 and self.line % self.print_every == 0:
                print "%6.2fs | Reached line %d. Imported: %d; Non-tweets: %d; Errors: %d" % (
                time() - start, self.line, self.imported, self.not_tweets, self.errors)

        if len(transaction_group) >= 0:
            self._import_group(transaction_group)

        print "%6.2fs | Finished %d lines. Imported: %d; Non-tweets: %d; Errors: %d" % (
        time() - start, self.line, self.imported, self.not_tweets, self.errors)
