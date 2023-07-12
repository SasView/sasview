import sys
from enum import Enum
from logging import getLogger
from types import ModuleType
from analyze.models import AnalysisBase, AnalysisModelBase, AnalysisParameterBase

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

# do we want individual dbs for each perspective?

class Fit(AnalysisBase):
    results = models.CharField(max_length= 100, blank=True, help_text="the string result")
    results_trace = [
    ]

    # TODO optimizer

    class StatusChoices(models.IntegerChoices):
        QUEUED = 1, "Queued"
        RUNNING = 2, "Running"
        COMPLETE = 3, "Complete"

    status = models.IntegerField(default=False, choices=StatusChoices.choices)

class FitParameter(AnalysisParameterBase):
    polydisperse = models.BooleanField(default=False, help_text="Is this a polydisperse parameter?")

    magnetic = models.BooleanField(default=False, help_text="is this a magnetic parameter?")

class FitModel(AnalysisModelBase):
    #list of default parameters
    default_parameters = {
        #str name, float number
        #import in migrations, ignored otherwise
    }

    polydispersity = models.BooleanField(default=False, help_text="Is polydispersity being checked in this model")

    magnetism = models.BooleanField(default=False, help_text="Is magnetism being checked in this model?")

    Qminimum = models.FloatField(blank = True, help_text="Minimum Q value for the fit")
    Qmaximum = models.FloatField(blank = True, help_text="Maximum Q value for the fit")

    """
    import sasmodels or through models.py in fit (modelmanagerbase)<---- create choice list
    """
    class SasModels():
        model_manager = ModelManager()
        MODEL_CHOICES = model_manager.get_model_dictionary
    #TODO FIX THIS ADD MORE
    model = models.CharField(max_length=256, help_text="model string")

    class PlugInModels():
        #create plug in models <- grab by url
        online_model_url = models.CharField(max_length=100, help_text= "url link to model")
        
    #look at models.py in sasview -> sasmodel-marketplace
