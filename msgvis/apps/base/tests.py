from django.test import TestCase

import mock
from templatetags import active

from msgvis.apps.corpus import models as corpus_models
from django.utils import timezone as tz
from datetime import timedelta
