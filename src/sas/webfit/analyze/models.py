from logging import getLogger

from data.models import Data
from django.contrib.auth.models import User
from django.db import models

models_logger = getLogger(__name__)

class AnalysisBase(models.Model):
    name = models.CharField(max_length=300, blank=True,
                            help_text="name used for multiple fits")
    current_user = models.ForeignKey(User, blank=True,
                                     null=True, on_delete=models.CASCADE)
    data_id = models.ForeignKey(Data, blank=True,
                                null=True, on_delete=models.CASCADE)

    #TODO add gpu_requested into analysis views
    gpu_requested = models.BooleanField(default=False,
                                        help_text="use GPU rather than CPU")
    #TODO create gpu_used

    time_received = models.DateTimeField(auto_now_add=True,
                                         help_text="analysis requested")
    #TODO write in view to start these
    time_started = models.DateTimeField(auto_now=False, blank=True,
                                        null=True, help_text="analysis initiated")
    time_complete = models.DateTimeField(auto_now=False, blank=True,
                                        null=True, help_text="analysis stopped")

    #write a func in analysis.views to check if fit status is complete
    analysis_success = models.BooleanField(default=False,
                                           help_text="Successful completion of analysis")
    #TODO write a list of errors

    is_public = models.BooleanField(default=False,
                                    help_text="does the user want their data to be public")


class AnalysisParameterBase(models.Model):
    base_id = models.ForeignKey(AnalysisBase, default=None,
                                on_delete=models.CASCADE)

    name = models.CharField(max_length=100, help_text="Parameter Name")

    value=models.FloatField(blank=True, null=True,
                            default=None, help_text="the value of the parameter")

    data_type = models.CharField(max_length=100, blank=True,
                                 null=True, default=None, help_text="parameter type (int/double)")

    unit = models.CharField(max_length=100, blank=True,
                            null=True, help_text="string for what unit the parameter is")

    lower_limit = models.FloatField(null=True, blank=True,
                                    default=None, help_text="optional lower limit")

    upper_limit = models.FloatField(null=True, blank=True,
                                    default=None, help_text="optional upper limit")

    value_trace = [
    ]

    analyze = models.BooleanField(default=False,
                                  help_text="Should this parameter be analyzed?")
