from django.core.management.base import BaseCommand, make_option, CommandError

from emoticonvis.apps.base.utils import check_or_create_dir


class Command(BaseCommand):
    help = "Detect the language of a given set of messages"
    args = '<dataset_id> <file_save_path>'
    option_list = BaseCommand.option_list + (
        make_option('-a', '--action',
                    default='all',
                    dest='action',
                    help='Action to run [all | dump | parse | lemmatize]'
        ),
        make_option('-p', '--path',
                    default='/home/vagrant/emoticon-analysis/datasets/ldig',
                    dest='ldig_path',
                    help='LDIG path'
        ),
    )


    def handle(self, dataset_id, save_path, **options):
        action = options.get('action')
        ldig_path = options.get('ldig_path')

        if not dataset_id:
            raise CommandError("Dataset id is required.")
        try:
            dataset_id = int(dataset_id)
        except ValueError:
            raise CommandError("Dataset id must be a number.")

        if not save_path:
            raise CommandError("File save path is required.")

        check_or_create_dir(save_path)

        if action == 'all' or action == 'dump':
            from emoticonvis.apps.enhance.tasks import dump_tweets
            print "Dumping messages..."
            dump_tweets(dataset_id, save_path, 'lang_detection')

        if action == 'all' or action == 'detect':
            from emoticonvis.apps.enhance.tasks import run_lang_detection
            output_path = "%s/lang_detection_results" %save_path
            check_or_create_dir(output_path)

            print "Detect message languages..."
            run_lang_detection(ldig_path, save_path, output_path)
