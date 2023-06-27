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

#    username = models.CharField(max_length=100, blank=False, null=False)
# password = models.CharField(max_length=100, blank=False, null=False)
   #fin later : category = models.ForeignKey()

class fits(models.Model):

    name = models.CharField(max_length=200, help_text="The name for all the fit data")
    server = models.CharField(max_length=200)
    enabled = models.BooleanField(blank=False, null=False, default=True)
    
    def get_loader(self, ext: str, module: ModuleType = type(sys), loader, ):
        if Loader.associate_file_type == 
        modelcategory = 
    
    loader = models.ForeignKey()


    #pagestate has a list of data_attributes
    #should just be an equation 