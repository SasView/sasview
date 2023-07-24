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

models_logger = getLogger(__name__)

# do we want individual dbs for each perspective?


class Data(models.Model):
    #username
    current_user = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)

    #might need to create a file_name so that users can figure out file_name for public files (opt of course)

    #imported data
    #user can either import a file path or actual file
    file = models.FileField(blank = True, null = True, help_text="This is a file")

    #creates hash for data
    if User:
        is_public = models.BooleanField(default = False, help_text= "opt in to submit your data into example pool")

    """
    date_recieved

    expiration_date = date_recieved + .... time etc

    expired = models.BooleanField(default = False, help_text="is the date expired")
    
    if expired is True:
        blah blah delete
    """
