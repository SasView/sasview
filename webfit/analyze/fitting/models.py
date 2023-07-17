import sys
from enum import Enum
from logging import getLogger
from types import ModuleType
from analyze.models import AnalysisBase, AnalysisParameterBase

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

    Qminimum = models.FloatField(default = None, null=True, blank = True, help_text="Minimum Q value for the fit")
    Qmaximum = models.FloatField(default = None, null=True, blank = True, help_text="Maximum Q value for the fit")

    polydispersity = models.BooleanField(default=False, help_text="Is polydispersity being checked in this model")

    magnetism = models.BooleanField(default=False, help_text="Is magnetism being checked in this model?")

    model = models.CharField(default = None, max_length=256, help_text="model string")


class FitParameter(AnalysisParameterBase):
    polydisperse = models.BooleanField(default=False, help_text="Is this a polydisperse parameter?")

    magnetic = models.BooleanField(default=False, help_text="is this a magnetic parameter?")

