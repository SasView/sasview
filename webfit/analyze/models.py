import sys
import uuid
from logging import getLogger
from types import ModuleType
from data.models import Data
from user_authentication.models import User

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

class AnalysisBase(models.Model):
    username = models.ForeignKey(User.username, default=None, on_delete=models.CASCADE)
    data_id = models.ForeignKey(Data.id, default = None, on_delete=models.CASCADE)
    
    GPU_enabled = models.BooleanField(default = False, help_text= "use GPU rather than CPU")

    time_recieved = models.DateTimeField(auto_now_add=True, help_text="analysis requested")
    #TODO fix these to actually update when initiated/ended
    time_started = models.DateTimeField(auto_now=True, blank = True, help_text="analysis initiated")
    time_ended = models.DateTimeField(auto_now=True, blank = True, help_text="analysis stopped")

    analysis_success = models.BooleanField(default = False, help_text="Successful completion of analysis")
    #list of errors
    errors = [
        "error1",
        "error2"
    ]

    if User:
        is_public = models.BooleanField(default = False, help_text="does the user want their data to be public")

class AnalysisParameterBase(models.Model):
    name = models.CharField(max_length=100, help_text="Parameter Name")
    """datatype = models.FloatField()

    minimum = datatype(default = False, blank = True, help_text = "Minimum constraint")
    maximum = datatype(default = False, blank = True, help_text = "Maximum constraint")
    """
    #constraints in parameter relative to another parameter
    constraints = [
        #fit parameters
        (),
    ]


class AnalysisModelBase(models.Model):
    name = models.CharField(max_length=300, help_text="name of analysis model")
    #list of analysis parameters
    parameters = [
        AnalysisParameterBase
    ]