# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('enhance', '0002_auto_20160222_0230'),
        ('experiment', '0002_auto_20160221_2350'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='stage',
            name='feature_assignment',
        ),
        migrations.AddField(
            model_name='stage',
            name='features',
            field=models.ManyToManyField(related_name='source_stage', to='enhance.Feature'),
            preserve_default=True,
        ),
    ]
