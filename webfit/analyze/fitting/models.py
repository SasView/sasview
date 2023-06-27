import sys
from logging import getLogger
from types import ModuleType
from analyze.models import Base

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


class Fits(Base):

    import_example_data = [
    ]
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
        

    complete = models.BooleanField(default = False, help_text= "Completion status of analysis")


#TODO: view saswebcalc later