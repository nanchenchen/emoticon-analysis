# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiment', '0003_auto_20160222_0230'),
        ('coding', '0005_auto_20160221_2358'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='featureassignment',
            name='feature',
        ),
        migrations.RemoveField(
            model_name='featureassignment',
            name='source',
        ),
        migrations.DeleteModel(
            name='FeatureAssignment',
        ),
    ]
