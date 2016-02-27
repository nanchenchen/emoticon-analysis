# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('coding', '0003_disagreementindicator'),
    ]

    operations = [
        migrations.AddField(
            model_name='codeassignment',
            name='is_ambiguous',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='codeassignment',
            name='is_example',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='codeassignment',
            name='is_saved',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='codedefinition',
            name='last_updated',
            field=models.DateTimeField(default=None, auto_now=True, auto_now_add=True),
            preserve_default=True,
        ),
    ]
