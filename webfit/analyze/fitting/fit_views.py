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
    FitSerializers,
    FitParameterSerializers,
    FitModelSerializers,
)
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
    base_serializer = FitSerializers()
    
    #TODO reduce redundancies... also check if this actually works
    if request.method == "PUT":
        base_serializer.status = 1

        #try to create model for check if the modelstring is valid
        if load_model(request.data.model):
            model_serializer = FitModelSerializers(model = request.data.model)
        #save model somewhere:
        else:
            return HttpResponseBadRequest("No model selected for fitting")

        #ask for Qmin + Qmax
        if request.data.data_id:
            if not fit_base.is_public:
                return HttpResponseBadRequest("data isn't public")
            if not (request.user.is_authenticated and request.user is fit_base.data_id.current_user):
                return HttpResponseBadRequest("data is not users")
            base_serializer(data_id = request.data.data_id)

        if request.data.parameters:
            parameters = JSONParser().parse(request.data.parameters)
            parameter_serializer = FitParameterSerializers(data = parameters)
            #str: name, number (int/float) <- unit 
            #if data == "float" -> float(value)
            #eval(f"{datatype}}({value})"
            pars = {}
            for x in parameter_serializer.data:
                num = eval(f"{x.datatype}({x.value})")
                #check if x.name is a valid parameter else return blah
                #pars = {x.name: num for x in parameter_serializer.data for num = eval(...)}
                pars[x.name] += {num,}

        base_serializer(is_public = request.data.is_public)

        if base_serializer.is_valid() and parameter_serializer.is_valid():
            base_serializer.save()
            parameter_serializer.save()

        start_fit(base_serializer.data, pars, model_serializer.data)
        #add "warnings": ... later
        return {"authenticated":request.user.is_authenticated, "fit_id":base_serializer.data.id}
    return HttpResponseBadRequest()


def start_fit(data, params, model):
    fit_base.status = 2
    test_data = get_object_or_404(Data, id = fit_base.data_id).file
    current_model = fit_base.fit_model.model

    #figure out how to add other parameters (polydispersity)
    model = Model(current_model, **fit_base.fit_model.default_parameters)

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
        if not fit_obj.is_public and not request.user.is_authenticated:
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
