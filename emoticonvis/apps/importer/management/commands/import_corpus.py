import sys
import os.path
import traceback
from time import time
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction

from emoticonvis.apps.corpus.models import Dataset
from emoticonvis.apps.importer.models import *


class Command(BaseCommand):
    """
    Import a corpus of message data into the database.

    .. code-block :: bash

        $ python manage.py import_corpus <corpus_directory>

    """
    args = '<corpus_directory> [...]'
    help = "Import a corpus into the database."
    option_list = BaseCommand.option_list + (
        make_option('-d', '--dataset',
                    action='store',
                    dest='dataset',
                    help='Set a target dataset to add to'
        ),
    )

    def handle(self, directory_path, **options):

        if directory_path is None:
            raise CommandError('Corpus directory must be provided.')

        dataset = options.get('dataset', None)
        if not dataset:
            dataset = os.path.basename(os.path.normpath(directory_path))

        start = time()
        dataset_obj, created = Dataset.objects.get_or_create(name=dataset, description=dataset)
        if created:
            print "Created dataset '%s' (%d)" % (dataset_obj.name, dataset_obj.id)
        else:
            print "Adding to existing dataset '%s' (%d)" % (dataset_obj.name, dataset_obj.id)

        importer = Importer(dataset=dataset_obj)

        if created:
            filename = directory_path + '/data_participants.json'
            if os.path.exists(filename):
                importer.run(filename, create_a_participant_from_json)
            else:
                # newly created dataset has to contain data_participants.json
                raise CommandError("Filename %s does not exist" % filename)

            filename = directory_path + '/data_points.json'
            if os.path.exists(filename):
                importer.run(filename, create_a_message_from_json)
            else:
                # newly created dataset has to contain data_point.json
                raise CommandError("Filename %s does not exist" % filename)

            filename = directory_path + '/emoticons.json'
            if os.path.exists(filename):
                importer.run(filename, create_an_emoticon_from_json)
            else:
                # newly created dataset has to contain emoticons.json
                raise CommandError("Filename %s does not exist" % filename)

        filename = directory_path + '/lang_sessions.json'
        if os.path.exists(filename):
            importer.run(filename, create_a_lang_session_from_json)

        filename = directory_path + '/lang_session_participants.json'
        if os.path.exists(filename):
            importer.run(filename, update_a_lang_session_participant_from_json)

        filename = directory_path + '/lang_session_proportion.json'
        if os.path.exists(filename):
            importer.run(filename, update_a_lang_session_info_from_json)

        filename = directory_path + '/data_point_language_sessions.json'
        if os.path.exists(filename):
            importer.run(filename, update_message_lang_session_from_json)

        filename = directory_path + '/participant_background_full.json'
        if os.path.exists(filename):
            importer.run(filename, update_full_participant_background_from_json)

        filename = directory_path + '/participant_background.json'
        if os.path.exists(filename):
            importer.run(filename, update_participant_background_from_json)

        filename = directory_path + '/emoticon_valence.json'
        if os.path.exists(filename):
            importer.run(filename, update_emoticon_valence_from_json)

        filename = directory_path + '/emoticon_label.json'
        if os.path.exists(filename):
            importer.run(filename, update_message_emotions_from_json)


        print "Time: %.2fs" % (time() - start)


class Importer(object):
    commit_every = 10000
    print_every = 10000

    def __init__(self, dataset):
        self.dataset = dataset
        self.line = 0
        self.imported = 0
        self.not_messages = 0
        self.errors = 0

    def _import_group(self, lines, import_func):
        with transaction.atomic(savepoint=False):
            for json_str in lines:

                if len(json_str) > 0:
                    try:
                        message = import_func(json_str, self.dataset)
                        if message:
                            self.imported += 1
                        else:
                            self.not_messages += 1
                    except:

                        self.errors += 1
                        print >> sys.stderr, "Import error on line %d" % self.line
                        traceback.print_exc()
                        import pdb
                        pdb.set_trace()

        #if settings.DEBUG:
            # prevent memory leaks
        #    from django.db import connection
        #    connection.queries = []

    def run(self, filename, import_func):
        print >> sys.stderr, "Processing %s" %filename

        self.line = 0
        self.imported = 0
        self.not_messages = 0
        self.errors = 0

        transaction_group = []

        start = time()

        with open(filename, 'r') as fp:
            for json_str in fp:
                self.line += 1
                json_str = json_str.strip()
                transaction_group.append(json_str)

                if len(transaction_group) >= self.commit_every:
                    self._import_group(transaction_group, import_func)
                    transaction_group = []

                if self.line > 0 and self.line % self.print_every == 0:
                    print "%6.2fs | Reached line %d. Imported: %d; Non-tweets: %d; Errors: %d" % (
                    time() - start, self.line, self.imported, self.not_messages, self.errors)

            if len(transaction_group) >= 0:
                self._import_group(transaction_group, import_func)

        print "%6.2fs | Finished %d lines. Imported: %d; Non-tweets: %d; Errors: %d" % (
        time() - start, self.line, self.imported, self.not_messages, self.errors)
