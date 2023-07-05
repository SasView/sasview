from logging import getLogger

from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from rest_framework.response import Response
from rest_framework.decorators import api_view

from sasdata.dataloader.loader import Loader
from serializers import FitSerializers
from .models import (
    AnalysisBase,
    AnalysisModelBase,
    AnalysisParameterBase,
)

analysis_logger = getLogger(__name__)

@api_view(["GET"])
def list_analysis(request, version = None):
    if request.user.is_authenticated:
        request.data_id

#takes DataInfo and saves it into to specified file location