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

# do we want individual dbs for each perspective?

loader = Loader()

class fits(models.Model):

    #import
    #takes files string and turn it into DataInfo
    file_string = models.CharField(max_length=200, null = False, help_text="The name for all the fit data")
    data = Loader.load(file_string)

    #export
    #takes DataInfo and saves it into to specified file location
    saved_file_string = models.CharField(max_length=200, null = False, help_text="file name to data saved")
    Loader.save(saved_file_string, data)

    """create opt in feature to upload data to example pool
        create option to add to open list of data
        can opt in to save data into example data pool

        1 api, takes data and creates unique Hash (algorithm and calculates unique 260 char string)
    """
    opt_in = models.BooleanField(default = False)
    if opt_in == True:
        #upload data to example data pool
        Loader.save("PUT FILE STRING HERE LATER", data)

    """
    import sasmodels or through models.py in fit (modelmanagerbase)<---- create choice list
    """
    class sasmodels():
        manager = ModelManager()
        model_list = manager.get_model_list
        MODEL_CHOICES = [
            model_list
        ]


#TODO: view saswebcalc later