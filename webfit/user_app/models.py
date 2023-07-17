from django.db import models
from django.db import models
from logging import getLogger
from django.contrib.auth.models import User

models_logger = getLogger(__name__)

# Create your models here.
#user model is django base model (will add on if needed)

"""class UserProfile(models.Model):
    # This field is required.
    user = models.OneToOneField(User, on_delete=models.CASCADE)
"""
