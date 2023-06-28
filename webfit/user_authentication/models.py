from django.db import models
from django.db import models
from logging import getLogger

models_logger = getLogger(__name__)

# Create your models here.
class user(models.Model):

    username = models.CharField(max_length=200, help_text="Username")
    password = models.CharField(max_length=200, help_text="password")

    anonymous = models.BooleanField(default = False, help_text="is this an anonymous user")