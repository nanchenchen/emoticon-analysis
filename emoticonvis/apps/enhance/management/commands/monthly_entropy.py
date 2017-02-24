from sys import stderr
import numpy as np

from django.db.models import Count
from django.core.management.base import BaseCommand, make_option, CommandError

import logging
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

from emoticonvis.apps.corpus.models import Dataset
from emoticonvis.apps.enhance.models import TweetWord

class Command(BaseCommand):
    help = "Calculate monthly entropy."
    args = '<dataset_id>'
    option_list = BaseCommand.option_list + (
    #    make_option('-a', '--action',
    #                default='all',
    #                dest='action',
    #                help='Action to run [all|similarity]'
    #    ),

    )

    def handle(self, dataset_id, **options):

        if not dataset_id:
            raise CommandError("Dataset id is required.")
        try:
            dataset_id = int(dataset_id)
        except ValueError:
            raise CommandError("Dataset id must be a number.")

        dataset = Dataset.objects.get(id=dataset_id)

        messages = dataset.message_set.filter(participant__is_selected=True)
        messages = messages.filter(type=0)
        group_by_month = messages.extra(select={'year': "EXTRACT(year FROM time)",
                                                'month': "EXTRACT(month FROM time)"})\
                                 .values('year','month')\
                                 .annotate(count_items=Count('id'))
        total_count = messages.count()



        import pdb
        pdb.set_trace()