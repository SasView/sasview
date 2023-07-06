import json
from logging import getLogger

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import api_view

from sasmodels.core import load_model
from sas.sascalc.fit.models import ModelManager
from sasdata.dataloader.loader import Loader
from bumps import fitters
from bumps.formatnum import format_uncertainty
#TODO categoryinstallers should belong in SasView.Systen rather than in QTGUI
from sas.qtgui.Utilities.CategoryInstaller import CategoryInstaller

from serializers import FitSerializers
from data.models import Data
from .models import (
    Fit,
    FitModel,
    FitParameter,
)


fit_logger = getLogger(__name__)

#start() only puts all the request data into the db, the function underneath actually runs the fit
#TODO add authentication -> figure out how to do this without multiplying
@api_view(["PUT"])
def start(request, version = None):
    fit = get_object_or_404(Fit)
    fit_model = get_object_or_404(FitModel)
    fit_parameters = get_object_or_404(FitParameter)
    serializer = FitSerializers(fit)

    #TODO reduce redundancies!!!
    if request.method == "PUT":
        if not request.data["MODEL_CHOICES"] in fit_model: 
            return HttpResponseBadRequest("No model selected for fitting")
        #save model somewhere: 

        if request.data.data_id:
            if not fit.opt_in and not request.user.is_authenticated:
                return HttpResponseBadRequest("data isn't public and user isn't logged in")
            data_obj = get_object_or_404(Data, id = request.data.data_id)

        if request.data.parameters:
            fit_parameters.Units += {request.data.parameters}

        if request.data.opt_in:
            fit.opt_in = request.data.opt_in
        #TODO figure out how to load parameters
        start_fit()
        return {"authenticated":request.user.is_authenticated, "fit_id":fit.id, "warnings":uhhhhhhh}
    return HttpResponseBadRequest()


def start_fit(data_obj):

    return 0


def status():
    return 0


@api_view(["GET"])
def fit_status(request, fit_id, version = None):
    fit_obj = get_object_or_404(Fit, id = fit_id)
    if request.method == "GET":
        #TODO figure out private later <- probs write in Fit model
        if not fit_obj.opt_in and not request.user.is_authenticated:
            return HttpResponseBadRequest("user isn't logged in")
        return_info = {"fit_id" : fit_id, "status" : Fit.status}
        if Fit.results:
            return_info+={"results" : Fit.results}
        return return_info
    
    return HttpResponseBadRequest()


@api_view(["GET"])
def list_optimizers(request, version = None):
    if request.method == "GET":
        return_info = {"optimizers" : [fitters.FIT_ACTIVE_IDS]}
        return return_info
    return HttpResponseBadRequest()


@api_view(["GET"])
def list_models(request, version = None):
    model_manager = ModelManager()
    if request.method == "GET":
        unique_models = {"models": []}
        if request.categories:
            user_file = CategoryInstaller.get_user_file()
            with open(user_file) as cat_file:
                file_contents = cat_file.read()
            spec_cat = file_contents[request.data.categories]
            unique_models["models"] += [spec_cat]
        else:
            unique_models["models"] = [model_manager.get_model_list()]
        return unique_models
        """TODO requires discussion:
        if request.username:
            if request.user.is_authenticated:
                user_models = 
                listed_models += {"plugin_models": user_models}
        """
    return HttpResponseBadRequest()

#takes DataInfo and saves it into to specified file location
