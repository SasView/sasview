from django import forms
from .models import Data
from django.contrib.auth.models import User

# Create the form class.
class DataForm(forms.ModelForm):
    class Meta:
        model = Data
        fields = ["file", "is_public"]
