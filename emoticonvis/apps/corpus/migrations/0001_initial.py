# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import emoticonvis.apps.base.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Dataset',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=150)),
                ('description', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('start_time', models.DateTimeField(default=None, null=True, blank=True)),
                ('end_time', models.DateTimeField(default=None, null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Emoticon',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('text', emoticonvis.apps.base.models.Utf8CharField(max_length=200)),
                ('valence', models.CharField(default=b'U', max_length=1, choices=[(b'P', b'Positive'), (b'N', b'Negative'), (b'O', b'Neutral'), (b'U', b'Unknown')])),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('idx', models.IntegerField(default=None, null=True, blank=True)),
                ('time', models.DateTimeField(default=None, null=True, blank=True)),
                ('session_id', models.IntegerField(default=None, null=True, blank=True)),
                ('type', models.IntegerField(default=0, max_length=1, choices=[(0, b'Normal message'), (1, b'Someone joined'), (2, b'Someone left'), (3, b'Bert message'), (4, b'Starting log')])),
                ('text', emoticonvis.apps.base.models.Utf8TextField(default=b'', null=True, blank=True)),
                ('dataset', models.ForeignKey(to='corpus.Dataset')),
                ('emoticons', models.ManyToManyField(related_name='messages', to='corpus.Emoticon')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Participant',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, blank=True)),
                ('language', models.CharField(default=b'No', max_length=2, choices=[(b'No', b'Not specified'), (b'En', b'English'), (b'Fr', b'French')])),
                ('status', models.CharField(default=b'No', max_length=2, choices=[(b'No', b'Not specified'), (b'Jr', b'Junior'), (b'Sr', b'Senior')])),
                ('position', models.CharField(default=None, max_length=32, null=True)),
                ('is_selected', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='message',
            name='participant',
            field=models.ForeignKey(related_name='messages', default=None, to='corpus.Participant', null=True),
            preserve_default=True,
        ),
    ]
