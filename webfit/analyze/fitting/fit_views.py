import json
from logging import getLogger

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import api_view

from sas.sascalc.fit.models import ModelManager
from sasmodels.core import load_model
from sasdata.dataloader.loader import Loader
from bumps import fitters
from serializers import FitSerializers
from .models import (
    Fit,
    FitModel,
    FitParameter,
)


fit_logger = getLogger(__name__)


@api_view(["GET"])
def start(request, version = None):
    if request.method == "GET":
        fit_data = get_object_or_404(FitModel.SasModels)
        if not request.data["MODEL_CHOICES"] in fit_data: 
            return HttpResponseBadRequest("No model selected for fitting")
    
    return HttpResponseBadRequest()


@api_view(["GET"])
def fit_status(request, fit_id, version = None):
    fit_obj = get_object_or_404(Fit, id = fit_id)
    if request.method == "GET":
        #figure out private later <- probs write in Fit model
        if fit_id is private and not request.user.is_authenticated:
            return HttpResponseBadRequest("user isn't logged in")
        return_info = {"fit_id" : fit_id, "status" : Fit.status}
        if Fit.results:
            return_info+={"results" : Fit.results}
        return return_info
    
    return HttpResponseBadRequest()


@api_view(["GET"])
def list_optimizers(request, version = None)
    if request.method == "GET":
        return_info = {"optimizers" : [fitters]}
        return return_info
    return HttpResponseBadRequest()


@api_view(["GET"])
def list_models(request, version = None):
    model_manager = ModelManager()
    if request.method == "GET":
        unique_models = {"models": []}
        if request.kind:
            unique_models["models"] += [{request.kind : ADDLATER}]
        elif request.categories:
            with open('FINDJSONNAMELATER.json') as cat_file:
                file_contents = cat_file.read()
            spec_cat = file_contents[request.categories]
            unique_models["models"] += [spec_cat]
        else:
            unique_models["models"] = [model_manager.get_model_list()]
        return unique_models
        """ requires discussion:
        if request.username:
            if request.user.is_authenticated:
                user_models = 
                listed_models += {"plugin_models": user_models}
                """
    return HttpResponseBadRequest()


def get_parameters(request, ):
    kernel = load_model()

#takes DataInfo and saves it into to specified file location
