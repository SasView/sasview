import sys
import uuid
from logging import getLogger
import hashlib

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

# do we want individual dbs for each perspective?


class Data(models.Model):
    id = models.BigAutoField(primary_key=True)

    #username
    username = models.ForeignKey(User, default=None, on_delete=models.CASCADE)

    #imported data
    file_string = models.CharField(max_length=200, null = False, help_text="The file string to the fit data")

    do_save = models.BooleanField(default=True, help_text="Should this model be saved?") #later boolean to add autosave?
    saved_file = models.BooleanField(default=False, help_text="is the model saved in files?") #should this exist, or do we always override files and save
    save_file_string = models.CharField(max_length=200, null = False, help_text="File location to save data")

    #creates hash for data

    opt_in = models.BooleanField(default = False, help_text= "opt in to submit your data into example pool")

    example_data = [
    ]

    user_data_ids = [

    ]

    public_file_ids = [

        
    ]

    analysis = models.ForeignKey("AnalysisBase.id", on_delete=models.CASCADE)

    errors = [

    ]


#TODO: view saswebcalc later