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

loader = Loader()

class FitParameter(AnalysisParameterBase):
    Units = models.CharField(default=False, help_text = "string for what unit the parameter is")

    polydisperse = models.BooleanField(default=False, help_text="Is this a polydisperse parameter?")

    magnetic = models.BooleanField(default=False, help_text="is this a magnetic parameter?")

    #polydispersity parameters (might change to list)
    polydispersity_parameter = {

    }

    upper_limit = models.FloatField(help_text="upper limit for parameter")
    lower_limit = models.FloatField(help_text="lower limit for parameter")

class FitModel(AnalysisModelBase):
    #list of default parameters
    default_parameters = {
        #str name, float number
        #import in migrations, override in fit_views.py
     }

    polydispersity = models.BooleanField(default=False, help_text="Is polydispersity being checked in this model")
    #list of polydispersity parameters
    polydispersity_parameters = FitParameter.polydispersity_parameter

    magnetism = models.BooleanField(default=False, help_text="Is magnetism being checked in this model?")
    #list of magnitism parameters
    magnetic_parameters = {}

    Qminimum = models.FloatField(default = False, help_text="Minimum Q value for the fit")
    Qmaximum = models.FloatField(help_text="Maximum Q value for the fit")
    if Qmaximum is True:
        AnalysisParameterBase.maximum = Qmaximum
    if Qminimum is True:
        AnalysisParameterBase.minimum = Qminimum

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

class Fit(AnalysisBase):
    fit_model = models.ForeignKey(FitModel, default = None, on_delete=models.CASCADE)
    results = thing
    opt_in = models.BooleanField(default = False, help_text= "opt in to have fit be public")
 
    class StatusChoices(models.IntegerChoices):

        QUEUED = 1
        RUNNING = 2
        COMPLETE = 3

    status = models.IntegerField(choices=StatusChoices)

#TODO: view saswebcalc later