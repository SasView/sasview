import json
from logging import getLogger

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser

from bumps.names import *
from sasmodels.core import load_model
from sasmodels.bumps_model import Model, Experiment
from sas.sascalc.fit.models import ModelManager
from sasdata.dataloader.loader import Loader
from bumps import fitters
from bumps.formatnum import format_uncertainty
#TODO categoryinstallers should belong in SasView.Systen rather than in QTGUI
from sas.qtgui.Utilities.CategoryInstaller import CategoryInstaller

from serializers import (
    FitSerializer,
    FitParameterSerializer,
    FitModelSerializer,
)
from data.models import Data
from .models import (
    Fit,
    FitModel,
    FitParameter,
)


fit_logger = getLogger(__name__)

#start() only puts all the request data into the db, start_fit() runs calculations
@api_view(["PUT"])
def start(request, version = None):
    base_serializer = FitSerializer(is_public = request.data.is_public)
    model_serializer = FitModelSerializer(base_id = base_serializer.id)
    parameter_serializer = FitParameterSerializer(model_id = model_serializer.id)
    
    #TODO WIP not sure if this works yet
    if request.method == "PUT":
        #set status

        #try to create model for check if the modelstring is valid
        #TODO figure out if I need a parcer here or not
        if load_model(request.data.model):
            model_serializer(model = request.data.model)
        else:
            return HttpResponseBadRequest("No model selected for fitting")

        if request.data.data_id:
            if Data.objects.filter(is_public = True, id = request.data.data_id).get():
                return HttpResponseBadRequest("data isn't public")
            if not (request.user.is_authenticated and 
                    request.user is Data.objects.get(id=request.data.data_id).current_user):
                return HttpResponseBadRequest("data is not user's")
            #search online to see how to add serializers.PrimaryKeyRelatedField
            base_serializer(data_id = request.data.data_id)

        if request.data.parameters:
            parameters = JSONParser().parse(request.data.parameters)
            parameter_serializer(data = parameters)
            #{str: name, value}
            pars = {}
            for x in parameter_serializer.data:
                num = eval(f"{x.datatype}({x.value})")
                #TODO check if x.name is a valid parameter else return blah
                #pars = {x.name: num for x in parameter_serializer.data for num = eval(...)}
                pars[x.name] += {num,}


        if base_serializer.is_valid() and parameter_serializer.is_valid() and model_serializer.is_valid():
            base_serializer.save()
            parameter_serializer.save()
            model_serializer.save()
        else:
            return HttpResponseBadRequest("Serializer error")

        start_fit(model_serializer.data, base_serializer.data, pars, parameters)
        #add "warnings": ... later
        return {"authenticated":request.user.is_authenticated, "fit_id":base_serializer.data.id}
    return HttpResponseBadRequest()


def start_fit(model, data = None, params = None, param_limits = None):
    if params is None:
        params = get_object_or_404(FitModel).default_parameters

    current_model = model.model
    model = Model(current_model, **params)
    if param_limits.radius.lower_limit or param_limits.radius.upper_limit:
        model.radius.range(param_limits.radius.lower_limit, param_limits.radius.upper_limit)
    if param_limits.length.lower_limit or param_limits.length.upper_limit:
        model.length.range(param_limits.length.lower_limit, param_limits.length.upper_limitghhhh)

    if data is None:
        M = Experiment(model = model)
    else:
        test_data = get_object_or_404(Data, id = data.data_id).file
        M = Experiment(data = test_data, model=model)
    problem = FitProblem(M)
    result = fit(problem)
    return result


def status():
    return 0


@api_view(["GET"])
def fit_status(request, fit_id, version = None):
    fit_obj = get_object_or_404(Fit, id = fit_id)
    if request.method == "GET":
        #TODO figure out private later <- probs write in Fit model
        if not (fit_obj.is_public or request.user.is_authenticated):
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
        #elif: request.kind
        else:
            unique_models["models"] = [model_manager.get_model_dictionary()]
        return unique_models
        """TODO requires discussion:
        if request.username:
            if request.user.is_authenticated:
                user_models = 
                listed_models += {"plugin_models": user_models}
        """
    return HttpResponseBadRequest()

#takes DataInfo and saves it into to specified file location
