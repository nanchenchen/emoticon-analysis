import operator
from django.db import models
from django.db.models import Q
from caching.base import CachingManager, CachingMixin

from msgvis.apps.base import models as base_models
from msgvis.apps.corpus import utils

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

    def get_messages_with_golden_code(self):
        return self.message_set.filter(has_golden_code=True).all()

    def get_messages_without_golden_code(self):
        return self.message_set.filter(has_golden_code=False).all()


class Code(models.Model):
    """A code of a message"""

    text = base_models.Utf8CharField(max_length=200)
    """The text of the code"""

    def __repr__(self):
        return self.text

    def __unicode__(self):
        return self.__repr__()

    def get_definition(self, source):
        if not self.definitions.filter(source=source).exists():
            return None

        definition = self.definitions.get(source=source, valid=True)
        return {
            "code": self.text,
            "source": source,
            "text": definition.text,
            "examples": definition.examples.all()
        }


class Message(models.Model):
    """
    The Message is the central data entity for the dataset.
    """
            
    dataset = models.ForeignKey(Dataset)
    """Which :class:`Dataset` the message belongs to"""

    ref_id = models.BigIntegerField(null=True, blank=True, default=None)
    """A reference id for the message"""

    text = base_models.Utf8TextField(null=True, blank=True, default="")
    """The actual text of the message."""

    code = models.ForeignKey(Code, null=True, blank=True, default=None)

    has_golden_code = models.BooleanField(default=False)

    def __repr__(self):
        return self.text

    def __unicode__(self):
        return self.__repr__()

    def get_feature_vector(self, dictionary, source=None):
        feature_scores = list(self.feature_scores.filter(feature__source__isnull=True).all())
        if source is not None:
            feature_scores += list(self.feature_scores.filter(feature__source=source, feature__valid=True).all())
        vector = []
        for feature_score in feature_scores:
            vector.append({"text": feature_score.feature.text,
                           "feature_index": feature_score.feature_index,
                           "count": feature_score.count})
        return vector


