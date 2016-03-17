# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('corpus', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LanguageSession',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start_time', models.DateTimeField(default=None, null=True, blank=True)),
                ('end_time', models.DateTimeField(default=None, null=True, blank=True)),
                ('num_en', models.IntegerField()),
                ('num_fr', models.IntegerField()),
                ('en_proportion', models.FloatField()),
                ('type', models.CharField(default=0, max_length=8, choices=[(b'E only', b'E only'), (b'major E', b'major E'), (b'major F', b'major F'), (b'F only', b'F only'), (b'Empty', b'Empty')])),
                ('dataset', models.ForeignKey(to='corpus.Dataset')),
                ('participants', models.ManyToManyField(related_name='lang_sessions', to='corpus.Participant')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='message',
            name='lang_session',
            field=models.ForeignKey(related_name='messages', default=None, to='corpus.LanguageSession', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='participant',
            name='dataset',
            field=models.ForeignKey(default=1, to='corpus.Dataset'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='participant',
            name='is_selected',
            field=models.BooleanField(default=True),
            preserve_default=True,
        ),
    ]
