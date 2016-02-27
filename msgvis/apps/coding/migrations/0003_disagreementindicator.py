# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('corpus', '0003_auto_20160219_0743'),
        ('coding', '0002_auto_20160219_0757'),
    ]

    operations = [
        migrations.CreateModel(
            name='DisagreementIndicator',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(default=b'N', max_length=1, choices=[(b'N', b'Not specified'), (b'U', b'I am correct'), (b'D', b'My partner and I disagree'), (b'P', b'My partner is correct')])),
                ('valid', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(default=None, auto_now_add=True)),
                ('message', models.ForeignKey(related_name='disagreement_indicators', to='corpus.Message')),
                ('partner_assignment', models.ForeignKey(related_name='partner_disagreement_indicators', to='coding.CodeAssignment')),
                ('user_assignment', models.ForeignKey(related_name='user_disagreement_indicators', to='coding.CodeAssignment')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
