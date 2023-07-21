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



class TestFitStart(TestCase):
    def setUp(self):
        User.objects.create(username="test_user", )

    fixtures = ['data/fixtures/example_data.json',]
    def can_fit_start_give_correct_answer(self):
        pars_limit = { 
                        "radius":{
                            "lower_limit":1,
                            "upper_limit":50
                        },
                        "length":{
                            "lower_limit":1,
                            "upper_limit":500
                        },
        }
        params = dict(
            radius = 35,
            length = 350,
            background = 0.0,
            scale = 1.0,
            sld = 4.0,
            sld_solvent = 1.0
        )
        data = Data.objects.get(is_public = True)
        chisq = start_fit("cylinder", params=params)
        self.assertEqual(chisq, "0.03(13)")

class TestLoader(TestCase):
    fixtures = ['data/fixtures/example_data.json',]

    def testing_loader(self):
        test_data = get_object_or_404(Data, is_public=True)
        loader = Loader()
        loader.load(test_data.file.path)
