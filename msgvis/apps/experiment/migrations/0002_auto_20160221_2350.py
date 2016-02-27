# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiment', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='messageselection',
            name='is_selected',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='messageselection',
            name='message',
            field=models.ForeignKey(related_name='message_selection', to='corpus.Message'),
            preserve_default=True,
        ),
    ]
