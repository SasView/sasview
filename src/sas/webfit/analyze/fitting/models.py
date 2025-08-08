from logging import getLogger

from django.db import models

from ..models import AnalysisBase, AnalysisParameterBase

models_logger = getLogger(__name__)

class Fit(AnalysisBase):
    results = models.CharField(max_length=1000000, blank=True,
                               null=True, help_text="the string result")
    results_trace = [
    ]

    class StatusChoices(models.IntegerChoices):
        QUEUED = 1, "Queued"
        RUNNING = 2, "Running"
        COMPLETE = 3, "Complete"

    status = models.IntegerField(default=StatusChoices.QUEUED, choices=StatusChoices.choices)

    q_minimum = models.FloatField(default=0.0005, null=True,
                                 blank=True, help_text="Minimum Q value for the fit")
    q_maximum = models.FloatField(default=0.5, null=True,
                                 blank=True, help_text="Maximum Q value for the fit")

    polydispersity = models.BooleanField(default=False,
                                         help_text="Is polydispersity being checked in this model")

    magnetism = models.BooleanField(default=False,
                                    help_text="Is magnetism being checked in this model?")

    model = models.CharField(blank=False, max_length=256,
                             help_text="model string")

    optimizer = models.CharField(blank=True, max_length=50,
                                 help_text="optimizer string")


class FitParameter(AnalysisParameterBase):
    polydisperse = models.BooleanField(default=False,
                                       help_text="Is this a polydisperse parameter?")

    magnetic = models.BooleanField(default=False,
                                   help_text="is this a magnetic parameter?")
