# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('enhance', '0001_initial'),
        (b'auth', b'__first__'),        # This line and the next line is for fixing the "Lookup failed auth.User" error
        (b'contenttypes', b'__first__'),
    ]

    operations = [
        migrations.AddField(
            model_name='feature',
            name='created_at',
            field=models.DateTimeField(default=None, auto_now_add=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='feature',
            name='last_updated',
            field=models.DateTimeField(default=None, auto_now=True, auto_now_add=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='feature',
            name='valid',
            field=models.BooleanField(default=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='feature',
            name='source',
            field=models.ForeignKey(related_name='features', default=None, to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]
