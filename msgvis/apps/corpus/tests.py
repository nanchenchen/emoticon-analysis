from datetime import datetime

from unittest import skip
from django.test import TestCase

from msgvis.apps.corpus import models as corpus_models
from msgvis.apps.dimensions import registry

class DatasetModelTest(TestCase):
    def test_created_at_set(self):
        """Dataset.created_at should get set automatically."""
        dset = corpus_models.Dataset.objects.create(name="Test Corpus", description="My Dataset")
        self.assertIsInstance(dset.created_at, datetime)
