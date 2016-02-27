from django.core.management.base import BaseCommand, make_option, CommandError
import os

def check_or_create_dir(dir_path):
    if os.path.exists(dir_path):
            if not os.path.isdir(dir_path):
                raise CommandError("The given path is not a folder.")
    else:
        try:
            os.mkdir(dir_path)
        except OSError:
            raise CommandError("Weird path error happens.")