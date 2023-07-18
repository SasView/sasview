# Create your tests here.
from django.test import TestCase
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework.test import APIRequestFactory

from sasmodels.data import empty_data1D
from sasdata.dataloader.loader import Loader
import numpy as np

from data.models import Data
from .models import (
    Fit,
    FitParameter
)
from .fit_views import (
    start,
    start_fit,
)

factory = APIRequestFactory()

# Create your tests here.
class TestStart(TestCase):
    def setUp(self):
        User.objects.create(username="test_user", )

    fixtures = ['data/fixtures/example_data.json',]
    def can_fit_start(self):
        start_fit("cylinder", get_object_or_404(Data, is_public = True))

class TestFitStart(TestCase):
    def setUp(self):
        User.objects.create(username="test_user", )

    def is_fit_giving_correct_results(self):
        factory.put()

class TestLoader(TestCase):
    fixtures = ['example_data.json', ]

    def testing_loader(self):
        test_data = get_object_or_404(Data, is_public=True)
        loader = Loader()
        loader.load(test_data.file.path)
