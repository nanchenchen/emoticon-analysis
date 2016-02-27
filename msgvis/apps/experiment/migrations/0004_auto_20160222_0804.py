# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('experiment', '0003_auto_20160222_0230'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pair',
            name='user1',
        ),
        migrations.RemoveField(
            model_name='pair',
            name='user2',
        ),
        migrations.AddField(
            model_name='pair',
            name='users',
            field=models.ManyToManyField(related_name='pair', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]
