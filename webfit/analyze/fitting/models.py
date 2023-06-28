import sys
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

class FitBase(AnalysisBase):
    import_example_data = [
    ]
    success = models.BooleanField(default = False, help_text= "Successful completion status of fit")

class FitParameter(AnalysisParameterBase):
    Units = [

    ]

    polydisperse = models.BooleanField(default=False)

    magnetic = models.BooleanField(default=False)

    class PolydispersityParameter():
        x = 0

class FitModel(AnalysisModelBase):
    default_parameter = [
        FitParameter
    ]

    polydispersity = models.BooleanField(default=False)
    polydispersity_parameters = [
        FitParameter
    ]

    magnitism = models.BooleanField(default=False)
    magnitic_parameters = [
        FitParameter
    ]

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
        manager = ModelManager()
        MODEL_CHOICES = [
            manager.get_model_list
        ]

    class PlugInModels():
        #create plug in models <- grab by url
        online_model_url = models.CharField(max_length=100, help_text= "url link to model")
        imported_model = loader.load(online_model_url)
        
    #look at models.py in sasview -> sasmodel-marketplace

    


#TODO: view saswebcalc later