# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('enhance', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('corpus', '0003_auto_20160219_0743'),
        ('coding', '0002_auto_20160219_0757'),
    ]

    operations = [
        migrations.CreateModel(
            name='Assignment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Condition',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(default=None, max_length=250, blank=True)),
                ('description', models.TextField(default=b'', blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Experiment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(default=None, max_length=250, blank=True)),
                ('description', models.TextField(default=b'', blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('saved_path_root', models.FilePathField(default=None, null=True, blank=True)),
                ('dictionary', models.ForeignKey(related_name='experiments', default=None, to='enhance.Dictionary', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MessageSelection',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField()),
                ('message', models.ForeignKey(to='corpus.Message')),
            ],
            options={
                'ordering': ['order'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Pair',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('user1', models.OneToOneField(related_name='pairA', to=settings.AUTH_USER_MODEL)),
                ('user2', models.OneToOneField(related_name='pairB', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Progress',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_updated', models.DateTimeField(auto_now=True, auto_now_add=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Stage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('experiment', models.ForeignKey(related_name='stages', to='experiment.Experiment')),
                ('feature_assignment', models.ManyToManyField(related_name='source_stage', to='coding.FeatureAssignment')),
                ('messages', models.ManyToManyField(related_name='stages', through='experiment.MessageSelection', to='corpus.Message')),
                ('svm_models', models.ManyToManyField(related_name='source_stage', to='coding.SVMModel')),
            ],
            options={
                'ordering': ['order'],
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='progress',
            name='current_stage',
            field=models.ForeignKey(related_name='progress', to='experiment.Stage'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='progress',
            name='user',
            field=models.ForeignKey(related_name='progress', to=settings.AUTH_USER_MODEL, unique=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='messageselection',
            name='stage',
            field=models.ForeignKey(to='experiment.Stage'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='condition',
            name='experiment',
            field=models.ForeignKey(related_name='conditions', to='experiment.Experiment'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assignment',
            name='condition',
            field=models.ForeignKey(related_name='assignments', to='experiment.Condition'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assignment',
            name='experiment',
            field=models.ForeignKey(related_name='assignments', to='experiment.Experiment'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assignment',
            name='pair',
            field=models.OneToOneField(related_name='assignment', to='experiment.Pair'),
            preserve_default=True,
        ),
    ]
