import operator
from django.db import models
from django.db.models import Q
from caching.base import CachingManager, CachingMixin

from emoticonvis.apps.base import models as base_models
from emoticonvis.apps.corpus import utils

import numpy


class Dataset(models.Model):
    """A top-level dataset object containing messages."""

    name = models.CharField(max_length=150)
    """The name of the dataset"""

    description = models.TextField()
    """A description of the dataset."""

    created_at = models.DateTimeField(auto_now_add=True)
    """The :py:class:`datetime.datetime` when the dataset was created."""

    start_time = models.DateTimeField(null=True, default=None, blank=True)
    """The time of the first real message in the dataset"""

    end_time = models.DateTimeField(null=True, default=None, blank=True)
    """The time of the last real message in the dataset"""

    @property
    def message_count(self):
        return self.message_set.count()

    def __unicode__(self):
        return self.name


class Emoticon(models.Model):
    """A code of a message"""

    text = base_models.Utf8CharField(max_length=200)
    """The text of the emoticon"""

    VALENCE_CHOICES = (
        ('P', 'Positive'),
        ('N', 'Negative'),
        ('O', 'Neutral'),
        ('U', 'Unknown'),
    )
    valence = models.CharField(max_length=1, choices=VALENCE_CHOICES, default='U')

    def __repr__(self):
        return self.text

    def __unicode__(self):
        return self.__repr__()


class Participant(models.Model):
    """A code of a message"""

    name = models.CharField(max_length=100, blank=True)
    """The name of the participant"""

    LANG_CHOICES = (
        ('No', 'Not specified'),
        ('En', 'English'),
        ('Fr', 'French'),
    )
    language = models.CharField(max_length=2, choices=LANG_CHOICES, default='No')

    STATUS_CHOICES = (
        ('No', 'Not specified'),
        ('Jr', 'Junior'),
        ('Sr', 'Senior'),
    )
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default='No')

    position = models.CharField(max_length=32, default=None, null=True)

    is_selected = models.BooleanField(default=True)

    def __repr__(self):
        return self.text

    def __unicode__(self):
        return self.__repr__()


class Message(models.Model):
    """
    The Message is the central data entity for the dataset.
    """
            
    dataset = models.ForeignKey(Dataset)
    """Which :class:`Dataset` the message belongs to"""

    idx = models.IntegerField(null=True, blank=True, default=None)
    """The index of the message"""

    time = models.DateTimeField(null=True, blank=True, default=None)
    """The :py:class:`datetime.datetime` (in UTC) when the message was sent"""

    session_id = models.IntegerField(null=True, blank=True, default=None)
    """The session of the message"""

    TYPE_CHOICES = (
        (0, 'Normal message'),
        (1, 'Someone joined'),
        (2, 'Someone left'),
        (3, 'Bert message'),
        (4, 'Starting log'),
    )
    type = models.IntegerField(max_length=1, choices=TYPE_CHOICES, default=0)

    participant = models.ForeignKey(Participant, related_name="messages", default=None, null=True)

    text = base_models.Utf8TextField(null=True, blank=True, default="")
    """The actual text of the message."""

    emoticons = models.ManyToManyField(Emoticon, related_name="messages")


    def __repr__(self):
        return self.text

    def __unicode__(self):
        return self.__repr__()