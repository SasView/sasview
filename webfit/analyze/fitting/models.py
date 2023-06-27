import sys
from logging import getLogger
from types import ModuleType

from sasdata.data_util.registry import ExtensionRegistry
from sasdata.dataloader.loader import Loader
from sasdata.data_util.loader_exceptions import NoKnownLoaderException, DefaultReaderException

from django.db import models
from django.core.exceptions import (
    NON_FIELD_ERRORS,
    FieldDoesNotExist,
    FieldError,
    MultipleObjectsReturned,
    ObjectDoesNotExist,
    ValidationError,
)

models_logger = getLogger(__name__)

# do we want individual dbs for each perspective
# for each 

loader = Loader()
#    username = models.CharField(max_length=100, blank=False, null=False)
# password = models.CharField(max_length=100, blank=False, null=False)
   #fin later : category = models.ForeignKey()

class fits(models.Model):

    #create uploade files
        #create option to add to open list of data
        #can opt in to save data into example data pool

    #1 api, takes data and creates unique Hash (algorithm and calculates unique 260 char string)
    #importing 

    #import sasmodels or through models.py in fit (modelmanagerbase)<---- create choice list
    #view saswebcalc
    file_string = models.CharField(max_length=200, null = False, help_text="The name for all the fit data")
    data = Loader.load(file_string)

    #export
    saved_file_string = models.CharField(max_length=200, null = False, help_text="file name to data saved")
    Loader.save(saved_file_string, data)

    #pagestate has a list of data_attributes