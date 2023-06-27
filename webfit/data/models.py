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

class Data(models.Model):
    #import
    #takes files string and turn it into DataInfo
    file_string = models.CharField(max_length=200, null = False, help_text="The name for all the fit data")
    data = Loader.load(file_string)

    #export
    #takes DataInfo and saves it into to specified file location
    saved_file_string = models.CharField(max_length=200, null = False, help_text="file name to data saved")
    Loader.save(saved_file_string, data)

    #save data under user
    #uhhh get db for user
    """
    user = models.ForeignKey("user", on_delete=models.CASCADE)
    save via user id (unique)
    look at models.py in sasview -> sasmodel-marketplace
    """

    """create opt in feature to upload data to example pool
        create option to add to open list of data
        can opt in to save data into example data pool

        1 api, takes data and creates unique Hash (algorithm and calculates unique 260 char string)
    """
    #find user id (auto generated)
    opt_in = models.BooleanField(default = False, help_text= "opt in to submit your data into example pool")
    if opt_in == True:
        #upload data to example data pool
        Loader.save("PUT FILE STRING HERE LATER", data)

    import_example_data = [
    ]


#TODO: view saswebcalc later