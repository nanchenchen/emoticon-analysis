# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('corpus', '0002_message_has_golden_code'),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name='message',
            index_together=set([]),
        ),
    ]
