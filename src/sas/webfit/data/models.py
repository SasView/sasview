import sys
import uuid
from logging import getLogger
import hashlib

from django.db import models
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage 
from django.utils.deconstruct import deconstructible

models_logger = getLogger(__name__)

class Data(models.Model):
    #username
    current_user = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)

    #file name
    file_name = models.CharField(max_length=200, default = "", blank = True, null = True, help_text="File name")

    #imported data
    #user can either import a file path or actual file
    file = models.FileField(blank = False, default = None, help_text="This is a file", upload_to="uploaded_files", storage=FileSystemStorage())

    #TODO creates hash for data

    #is the data public?
    is_public = models.BooleanField(default = False, help_text= "opt in to submit your data into example pool")

    #TODO add date,recieved, expiration_data, expired boolean, delete if expired
