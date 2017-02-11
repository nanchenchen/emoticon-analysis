from django.core.management.base import BaseCommand, make_option, CommandError

from emoticonvis.apps.base.utils import check_or_create_dir


class Command(BaseCommand):
    help = "Detect the language of a given set of messages"
    args = '<dataset_id>'
    option_list = BaseCommand.option_list + (
    )


    def handle(self, dataset_id, **options):

        if not dataset_id:
            raise CommandError("Dataset id is required.")
        try:
            dataset_id = int(dataset_id)
        except ValueError:
            raise CommandError("Dataset id must be a number.")


        from emoticonvis.apps.enhance.tasks import detect_language
        print "Detect message languages..."
        detect_language(dataset_id)
