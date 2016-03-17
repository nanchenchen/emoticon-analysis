# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import emoticonvis.apps.enhance.fields
from django.conf import settings
import emoticonvis.apps.base.models


class Migration(migrations.Migration):

    dependencies = [
        ('corpus', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Dictionary',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('settings', models.TextField()),
                ('time', models.DateTimeField(auto_now_add=True)),
                ('num_docs', emoticonvis.apps.enhance.fields.PositiveBigIntegerField(default=0)),
                ('num_pos', emoticonvis.apps.enhance.fields.PositiveBigIntegerField(default=0)),
                ('num_nnz', emoticonvis.apps.enhance.fields.PositiveBigIntegerField(default=0)),
                ('dataset', models.ForeignKey(related_name='dictionary', default=None, blank=True, to='corpus.Dataset', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Feature',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('index', models.IntegerField()),
                ('text', emoticonvis.apps.base.models.Utf8CharField(max_length=150)),
                ('document_frequency', models.IntegerField()),
                ('created_at', models.DateTimeField(default=None, auto_now_add=True)),
                ('last_updated', models.DateTimeField(default=None, auto_now=True, auto_now_add=True)),
                ('valid', models.BooleanField(default=True)),
                ('dictionary', models.ForeignKey(related_name='features', to='enhance.Dictionary')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MessageFeature',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('feature_index', models.IntegerField()),
                ('count', models.FloatField()),
                ('tfidf', models.FloatField()),
                ('dictionary', models.ForeignKey(to='enhance.Dictionary', db_index=False)),
                ('feature', models.ForeignKey(related_name='message_scores', to='enhance.Feature')),
                ('message', models.ForeignKey(related_name='feature_scores', to='corpus.Message', db_index=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TweetWord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('original_text', emoticonvis.apps.base.models.Utf8CharField(default=b'', max_length=100, db_index=True, blank=True)),
                ('pos', models.CharField(default=b'', max_length=4, null=True, blank=True)),
                ('text', emoticonvis.apps.base.models.Utf8CharField(default=b'', max_length=100, db_index=True, blank=True)),
                ('dataset', models.ForeignKey(related_name='tweet_words', default=None, blank=True, to='corpus.Dataset', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TweetWordMessageConnection',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField()),
                ('message', models.ForeignKey(related_name='tweetword_connections', to='corpus.Message')),
                ('tweet_word', models.ForeignKey(related_name='tweetword_connections', to='enhance.TweetWord')),
            ],
            options={
                'ordering': ['message', 'order'],
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='tweetwordmessageconnection',
            unique_together=set([('message', 'tweet_word', 'order')]),
        ),
        migrations.AddField(
            model_name='tweetword',
            name='messages',
            field=models.ManyToManyField(related_name='tweet_words', through='enhance.TweetWordMessageConnection', to='corpus.Message'),
            preserve_default=True,
        ),
        migrations.AlterIndexTogether(
            name='messagefeature',
            index_together=set([('message', 'feature')]),
        ),
        migrations.AddField(
            model_name='feature',
            name='messages',
            field=models.ManyToManyField(related_name='features', through='enhance.MessageFeature', to='corpus.Message'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='feature',
            name='source',
            field=models.ForeignKey(related_name='features', default=None, to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]
