import os
import re
import sys
import json
import logging
import django
from glob import glob

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from data.models import Data

# Initialise the Django environment. This must be done before importing anything
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sasmarket.settings")
django.setup()

EXAMPLE_DATA_DIR = os.environ.get("EXAMPLE_DATA_DIR", "../src/sas/example_data")

def parse_1D():
    dir_1d = os.path.join(EXAMPLE_DATA_DIR, "example_data", "1d_data")
    if not os.path.isdir(dir_1d):
        logging.error("1D Data directory not found at: {}".format(dir_1d))
        return
    for file_path in glob(os.path.join(dir_1d)):
        file_name = os.path.basename(file_path)[0]
        file_name = "1d_data" + file_name
        write_file(file_name)

def parse_2D():
    dir_2d = os.path.join(EXAMPLE_DATA_DIR, "example_data", "2d_data")
    if not os.path.isdir(dir_2d):
        logging.error("2D Data directory not found at: {}".format(dir_2d))
        return
    for file_path in glob(os.path.join(dir_2d)):
        file_name = os.path.basename(file_path)[0]
        file_name = "2d_data" + file_name
        write_file(file_name)


def write_file(file):
    file_content = [
        {
            "model": "data.Data",
            "fields": {
                "file" : file,
                "is_public" : True
            }
        }
    ]
    json_obj = json.dumps(file_content, indent=4)
    with open("/data/fixtures/{file}.js", "w") as f:
        f.write(json_obj)
    