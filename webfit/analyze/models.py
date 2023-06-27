import sys
from logging import getLogger
from types import ModuleType

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

class Base(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    use_GPU = models.BooleanField(default = False, help_text= "use GPU rather than CPU")


    