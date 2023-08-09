from django.db import models
from django.db import models
from logging import getLogger
from django.contrib.auth.models import User

models_logger = getLogger(__name__)

#TODO current user model is django base model, create specific User model

"""class UserProfile(models.Model):
    # This field is required.
    user = models.OneToOneField(User, on_delete=models.CASCADE)
"""
