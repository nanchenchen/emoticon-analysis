import csv

from django.core.management.base import BaseCommand, make_option, CommandError

import logging
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

from emoticonvis.apps.corpus.models import Dataset
from emoticonvis.apps.enhance.tasks import calculate_word_entropy

class Command(BaseCommand):
    help = "Calculate monthly entropy."
    args = '<dataset_id> <output_file>'
    option_list = BaseCommand.option_list + (
    #    make_option('-a', '--action',
    #                default='all',
    #                dest='action',
    #                help='Action to run [all|similarity]'
    #    ),

    )

    def handle(self, dataset_id, output_file, **options):

        if not dataset_id:
            raise CommandError("Dataset id is required.")
        try:
            dataset_id = int(dataset_id)
        except ValueError:
            raise CommandError("Dataset id must be a number.")

        if not output_file:
            raise CommandError("Output filename is required.")

        final_results = {}

        all_entropy = calculate_word_entropy(dataset_id)
        for (month, H) in all_entropy:
            if month not in final_results:
                final_results[month] = {'month': month}
            final_results[month]['all'] = H


        en_entropy = calculate_word_entropy(dataset_id, lang_group='En')
        for (month, H) in en_entropy:
            if month not in final_results:
                final_results[month] = {'month': month}
            final_results[month]['English'] = H

        fr_entropy = calculate_word_entropy(dataset_id, lang_group='Fr')
        for (month, H) in fr_entropy:
            if month not in final_results:
                final_results[month] = {'month': month}
            final_results[month]['French'] = H

        print final_results

        with open(output_file, 'w') as fp:
            dw = csv.DictWriter(fp, delimiter=',', lineterminator='\n',
                                fieldnames=['month', 'all', 'English', 'French'])
            dw.writeheader()
            for month in final_results:
                dw.writerow(final_results[month])

