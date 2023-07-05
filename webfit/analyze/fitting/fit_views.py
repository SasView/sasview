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
    Fit,
    FitModel,
    FitParameter,
)

fit_logger = getLogger(__name__)

def start(request, version = None):
    fit_data = get_object_or_404(FitModel.SasModels)
    if not request.data["MODEL_CHOICES"] in fit_data: 
        return HttpResponseBadRequest("No model selected for fitting")
    
    return Response("test")

#takes DataInfo and saves it into to specified file location