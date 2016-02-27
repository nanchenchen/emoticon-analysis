# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('coding', '0004_auto_20160221_0915'),
    ]

    operations = [
        migrations.RenameField(
            model_name='codeassignment',
            old_name='user',
            new_name='source',
        ),
        migrations.RenameField(
            model_name='featureassignment',
            old_name='user',
            new_name='source',
        ),
        migrations.RenameField(
            model_name='svmmodel',
            old_name='user',
            new_name='source',
        ),
    ]
