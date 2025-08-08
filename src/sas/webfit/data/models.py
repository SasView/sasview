from logging import getLogger

from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.db import models

models_logger = getLogger(__name__)

class Data(models.Model):
    #username
    current_user = models.ForeignKey(User, blank=True,
                                     null=True, on_delete=models.CASCADE)

    #file name
    file_name = models.CharField(max_length=200, default=None,
                                 blank=True, null=True, help_text="File name")

    #imported data
    #user can either import a file path or actual file
    #TODO upload_to should instead create a new directory using user.id to name
    file = models.FileField(blank=False, default=None, help_text="This is a file",
                            upload_to="uploaded_files", storage=FileSystemStorage())

    #TODO creates hash for data

    #is the data public?
    is_public = models.BooleanField(default=False,
                                    help_text= "opt in to submit your data into example pool")

    #TODO add date,received, expiration_data, expired boolean, delete if expired
