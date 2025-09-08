from django import forms

from .models import Data


# Create the form class.
class DataForm(forms.ModelForm):
    class Meta:
        model = Data
        fields = ["file", "is_public"]
