import sys
import uuid
from logging import getLogger
from types import ModuleType
import hashlib

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

# do we want individual dbs for each perspective?

loader = Loader()

class Data(models.Model):
    id = models.UUIDField(primary_key=True, default = uuid.uuid4, editable=False)

    #user id 
    user_id = models.ForeignKey(User, default=None, on_delete=models.CASCADE)

    #import
    #takes files string and turn it into DataInfo
    file_string = models.CharField(max_length=200, null = False, help_text="The name for all the fit data")
    if file_string != False:
        data = loader.load(file_string)

    #export
    #takes DataInfo and saves it into to specified file location
    do_save = models.BooleanField(default = True, help_text="Does user want to save data?")
    if do_save == True:
        saved_file_string = models.CharField(max_length=200, null = False, help_text="file name to data saved")
        Try:loader.save(loader, file = saved_file_string, data = data)
        Except:print(KeyError)

    #save data under user

    #creates hash for data

    #opt in to uploading to example data pool
    opt_in = models.BooleanField(default = False, help_text= "opt in to submit your data into example pool")
    if opt_in == True:
        #upload data to example data pool
        #TODO loader.save(loader, file = "PUT FILE STRING HERE LATER", data = data)
        x=1

    import_example_data = [
    ]

    analysis = models.ForeignKey("AnalysisBase.id", on_delete=models.CASCADE)


#TODO: view saswebcalc later