import os
import re
import logging
import django
from glob import glob

from sasmodels.core import ModelInfo
from sasmodels.sasview_model import load_custom_model, load_standard_models

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from analyze.fitting.models import FitModel

#should this be moved outside the webfit/django directory?
#^model marketplace does this for somereason? is it so that they can import withotu worrying 

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sasmarket.settings")
django.setup()

#about django's code interfering?
#should this be uploaded in fixtures?

"""
upload fit parameters:

get code to talk to sasmodels.modelinfo.py -> parameter table

directly import -> no use to go to json file then back

"""

created_json_parameters = open("example_data.json","w"),

def _remove_all():
    return 0

def parse_all_parameters():
    FitModel.SasModels.MODEL_CHOICES
    
    
#get all parameters as list, put into json
#make python parameter into json
