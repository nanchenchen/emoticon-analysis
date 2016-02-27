from django.core.management.base import BaseCommand, make_option, CommandError

class Command(BaseCommand):
    help = "Extract topics for a dataset."
    args = "<dataset id>"
    option_list = BaseCommand.option_list + (
        make_option('--name',
                    dest='name',
                    default='my topic model',
                    help="The name for your keyword dictionary"),
    )

    def handle(self, dataset_id, *args, **options):
        name = options.get('name')

        if not dataset_id:
            raise CommandError("Dataset id is required.")
        try:
            dataset_id = int(dataset_id)
        except ValueError:
            raise CommandError("Dataset id must be a number.")

        from msgvis.apps.enhance.tasks import default_feature_context, standard_features_pipeline

        context = default_feature_context(name=name, dataset_id=dataset_id)
        standard_features_pipeline(context=context, dataset_id=dataset_id)

