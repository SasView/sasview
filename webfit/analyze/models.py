import sys
from logging import getLogger
from types import ModuleType
from data.models import Data
from user_authentication.models import user

from sas.sascalc.fit.models import ModelManager
from sasdata.dataloader.loader import Loader
from sasdata.data_util.loader_exceptions import NoKnownLoaderException, DefaultReaderException

#do i need these if we have loader exceptions^^
from django.db import models
from django.core.exceptions import (
    NON_FIELD_ERRORS,
    FieldDoesNotExist,
    FieldError,
    MultipleObjectsReturned,
    ObjectDoesNotExist,
    ValidationError,
)
#models.CharField(max_length=100, blank=False, null=False)
#models.CharField(max_length=200, help_text="")
#models.ForeignKey("other model class name", on_delete=models.CASCADE) <--- used for refering to other models in other apps
"""CHOICES= [
   "choice",
    (
        ("choice1", "choice2),
        ("group choice","2nd choice in group"),
    ),
 ]"""

models_logger = getLogger(__name__)


class AnalysisParameterBase(models.Model):
    #id... for smth
    id = id()
    name = models.CharField(max_length=100, help_text="Parameter Name")
    datatype = models.FloatField()

    minimum = datatype(default = False, blank = True)
    maximum = datatype(default = False, blank = True)

    constraints = [
        ("Units", "Polydisperse", "Magnetic"),
    ]


class AnalysisModelBase(models.Model):
    id = id()
    name = models.CharField(max_length=300, help_text="name of analysis model")


class AnalysisBase(models.Model):
    id = id()
    user_id = Data.user_id
    
    GPU_enabled = models.BooleanField(default = False, help_text= "use GPU rather than CPU")

    #analysis requested
    time_recieved = models.DateTimeField(auto_now_add=True)
    #TODO fix these to actually update when initiated/ended
    #analysis initiated
    time_started = models.DateTimeField(auto_now=True, blank = True, required = False)
    #analysis stopped
    time_ended = models.DateTimeField(auto_now=True, blank = True, required = False)

    success = models.BooleanField(default = False)
    errors = [
        "error1",
        "error2"
    ]

    if user.anonymous == True:
        is_public = models.BooleanField(default = False)

    parameters = [
        AnalysisParameterBase
    ]