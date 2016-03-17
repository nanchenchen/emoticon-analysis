# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('corpus', '0002_auto_20160317_0033'),
    ]

    operations = [
        migrations.AlterField(
            model_name='languagesession',
            name='en_proportion',
            field=models.FloatField(default=0),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='languagesession',
            name='num_en',
            field=models.IntegerField(default=0),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='languagesession',
            name='num_fr',
            field=models.IntegerField(default=0),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='languagesession',
            name='type',
            field=models.CharField(default=None, max_length=8, null=True, choices=[(b'E only', b'E only'), (b'major E', b'major E'), (b'major F', b'major F'), (b'F only', b'F only'), (b'Empty', b'Empty')]),
            preserve_default=True,
        ),
    ]
