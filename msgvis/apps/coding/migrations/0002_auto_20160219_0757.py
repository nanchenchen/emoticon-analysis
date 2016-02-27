# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('coding', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('corpus', '0003_auto_20160219_0743'),
        ('enhance', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='svmmodelweight',
            name='feature',
            field=models.ForeignKey(related_name='weights', to='enhance.Feature'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='svmmodelweight',
            name='svm_model',
            field=models.ForeignKey(related_name='weights', to='coding.SVMModel'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='svmmodel',
            name='user',
            field=models.ForeignKey(related_name='svm_models', to=settings.AUTH_USER_MODEL, unique=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='featureassignment',
            name='feature',
            field=models.ForeignKey(related_name='feature_assignments', to='enhance.Feature'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='featureassignment',
            name='user',
            field=models.ForeignKey(related_name='feature_assignments', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='codedefinition',
            name='code',
            field=models.ForeignKey(related_name='definitions', to='corpus.Code'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='codedefinition',
            name='examples',
            field=models.ManyToManyField(related_name='definitions', to='corpus.Message'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='codedefinition',
            name='source',
            field=models.ForeignKey(related_name='definitions', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='codeassignment',
            name='code',
            field=models.ForeignKey(related_name='code_assignments', to='corpus.Code'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='codeassignment',
            name='message',
            field=models.ForeignKey(related_name='code_assignments', to='corpus.Message'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='codeassignment',
            name='user',
            field=models.ForeignKey(related_name='code_assignments', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]
