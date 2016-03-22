from sys import stderr
import numpy as np

from django.core.management.base import BaseCommand, make_option, CommandError

import logging
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

from emoticonvis.apps.corpus.models import Dataset
from emoticonvis.apps.enhance.models import get_message_connections, get_word_count_list

class Command(BaseCommand):
    help = "Live."
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

        message_connections = get_message_connections(dataset_id, has_emoticon=True, selected_participant_only=True).all()
        words = get_word_count_list(message_connections, top_num=500)
        emoticons = dataset.get_emoticons_from_selected_participants().all()

        word_map = {}
        emoticon_map = {}

        for idx, word in enumerate(words):
            word = word['tweet_word__text']
            word_map[word] = idx

        for idx, emoticon in enumerate(emoticons):
            emoticon_map[emoticon.text] = idx

        count_vectors = np.zeros((emoticons.count(), len(words)))

        # for idx, emoticon in enumerate(emoticons):
        #     for msg in emoticon.messages.all().prefetch_related('tweetword_connections'):
        #         for twc in msg.tweetword_connections.all():
        #             word_idx = word_map.get(twc.tweet_word.text)
        #             if word_idx:
        #                 count_vectors[idx, word_idx] += 1
        message_connections = message_connections.select_related('message', 'tweet_word').prefetch_related('message__emoticons')
        total_count = message_connections.count()
        for idx, msg_con in enumerate(message_connections):
            if idx % 1000 == 0:
                print >>stderr, "Finished %d/%d" %(idx, total_count)
            word_idx = word_map.get(msg_con.tweet_word.text)
            if word_idx:
                for emoticon in msg_con.message.emoticons.all():
                    emoticon_idx = emoticon_map.get(emoticon.text)
                    count_vectors[emoticon_idx, word_idx] += 1


        # import pdb
        # pdb.set_trace()
        #
        # import csv
        # with open('../datasets/emoticon-words.csv', 'wb') as csvfile:
        #     csvwriter = csv.writer(csvfile, delimiter=',',
        #                     quotechar='"', quoting=csv.QUOTE_ALL)
        #     csvwriter.writerow([word['tweet_word__text'] for word in words])
        #     output_ary = count_vectors.tolist()
        #     for idx, ary in enumerate(output_ary):
        #         csvwriter.writerow([emoticons[idx].text] + ary)

        import pdb
        pdb.set_trace()