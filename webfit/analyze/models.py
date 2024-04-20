import sys
import uuid
from logging import getLogger
from types import ModuleType
from data.models import Data
from user_app.models import UserProfile

from sas.sascalc.fit.models import ModelManager
from sasdata.dataloader.loader import Loader
from sasdata.data_util.loader_exceptions import NoKnownLoaderException, DefaultReaderException

#do i need these if we have loader exceptions^^
from django.db import models
from django.contrib.auth.models import User
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
    current_user = models.ForeignKey(User, default = None, on_delete=models.CASCADE)
    data_id = models.ForeignKey(Data, default = None, on_delete=models.CASCADE)
    
    #TODO add gpu_requested into analysis views
    gpu_requested = models.BooleanField(default = False, help_text= "use GPU rather than CPU")
    #TODO create gpu_used

    time_recieved = models.DateTimeField(auto_now_add=True, help_text="analysis requested")
    #TODO write in view to start these
    time_started = models.DateTimeField(auto_now=False, blank = True, null=True, help_text="analysis initiated")
    time_complete = models.DateTimeField(auto_now=False, blank = True, null=True, help_text="analysis stopped")

    #write a func in analysis.views to check if fit status is complete
    analysis_success = models.BooleanField(default = False, help_text="Successful completion of analysis")
    #TODO write a list of errors

    if User:
        is_public = models.BooleanField(default = False, help_text="does the user want their data to be public")

    
class AnalysisParameterBase(models.Model):
    base_id = models.ForeignKey(AnalysisBase, default = None, on_delete=models.CASCADE)

    name = models.CharField(max_length=100, help_text="Parameter Name")

    value=models.FloatField(blank=False, help_text="the value of the parameter")

    data_type = models.CharField(max_length=100, help_text="parameter type (int/double)")

    unit = models.CharField(max_length=100, blank=False, help_text = "string for what unit the parameter is")

    lower_limit = models.FloatField(blank = True, help_text="optional lower limit")

    upper_limit = models.FloatField(blank = True, help_text="optional upper limit")

    value_trace = [
    ]

    #constraints in parameter relative to another parameter
    #TODO fix this to hold fit parameters, see: foriegnkey?
    constraints = {
        "fit parameters" : (),
    }