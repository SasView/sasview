import os
import re
import sys
import logging
from glob import glob

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from data.models import Data

#should this be moved outside the webfit/django directory?
#^model marketplace does this for somereason? is it so that they can import withotu worrying 
#about django's code interfering?

"""
where does the example data get loaded inside of sasview?
the files aren't in json so what format should it be in?
^ ask about how the data files look like when imported (all one file or a folder?) <- reformat models to fit

"""

"""
f = open("myfile.txt", "w")
"""

#possibly just create 

def parse_file_names():
    

def get_file_name():
    for x in example_data :
        put in 
