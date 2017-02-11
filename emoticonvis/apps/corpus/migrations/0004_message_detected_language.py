# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('corpus', '0003_auto_20160317_0533'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='detected_language',
            field=models.CharField(default=b'No', max_length=2, choices=[(b'No', b'Not specified'), (b'En', b'English'), (b'Fr', b'French')]),
            preserve_default=True,
        ),
    ]
