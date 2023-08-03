import json
import ast
from logging import getLogger
from collections import defaultdict

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser

from bumps.names import *
from sasmodels.core import load_model, load_model_info, list_models
from sasmodels.data import load_data, empty_data1D, empty_data2D, empty_sesans
from sasmodels.bumps_model import Model, Experiment
from sasmodels.direct_model import DirectModel
from sasdata.dataloader.loader import Loader
from sas.sascalc.fit.models import ModelManager
from bumps import fitters
from bumps.formatnum import format_uncertainty
#TODO categoryinstallers should belong in SasView.Systen rather than in QTGUI
from sas.qtgui.Utilities.CategoryInstaller import CategoryInstaller

from serializers import (
    FitSerializer,
    FitParameterSerializer,
)
from data.models import Data
from .models import (
    Fit,
    FitParameter,
)


fit_logger = getLogger(__name__)
model_manager = ModelManager()
#TODO add view that gets previous fit results
#TODO finish view for get status
#

#start() only puts all the request data into the db, start_fit() runs calculations
"""
Documentation for user input: User input should look like this:
{
    "current_user": int
    "data_id": int
    "model":str
    "parameters": [
        {
        "base_id": int
        "name":str
        "value":int/float
        }
    ]
}
"""

@api_view(['POST'])
def start(request, version = None):
    if request.method == "POST":
        #TODO set status
        #TODO add qmin/qmax
        #TODO add 

        base_serializer = FitSerializer(data=request.data)
        if base_serializer.is_valid():
            base_serializer.save()
        else:
            return Response(base_serializer.errors)
        
        fit_db = get_object_or_404(Fit, id = base_serializer.data["id"])

        #try to create model for check if the modelstring is valid
        if load_model(fit_db.model):
            pass
        else:
            fit_db.delete()
            return HttpResponseBadRequest("No model selected for fitting")

        if fit_db.data_id:
            if fit_db.data_id.is_public or (request.user.is_authenticated and 
                    request.user is fit_db.data_id.current_user):
                pass
            else:
                fit_db.delete()
                return HttpResponseBadRequest("data isn't public and/or the user's")

        if request.data.get("parameters"):
            parameters = request.data.get("parameters")
            
            #list of FitParameter objects
            all_param_dbs = []
            for x in parameters:
                x["base_id"] = fit_db.id
                parameter_serializer = FitParameterSerializer(data = x)
                if parameter_serializer.is_valid():
                    parameter_serializer.save()
                all_param_dbs.append(get_object_or_404(FitParameter, base_id = fit_db.id, name = x["name"]))

        #TODO remove below code later -> scheduling fits with status
        #start_fit connection for WORKING MODEL, NOT finalized api
        result = start_fit(fit_db)

        result_serializer = FitSerializer(fit_db, data = {"results": str(result)}, partial=True)
        if result_serializer.is_valid():
            result_serializer.save()
        else:
            return Response(result_serializer.errors)
        
        #add "warnings": ... later
        return Response({"authenticated":request.user.is_authenticated, "fit_id":fit_db.id, "results": result})

    return HttpResponseBadRequest()


def start_fit(fit_db):
    #fit_db.status = 2
    current_model = load_model(fit_db.model)

    pars = get_parameters(fit_db.id)[0]
    par_limits = get_parameters(fit_db.id)[1]

    if not fit_db.data_id:
        #TODO impliment qmin/qmax
        test_data = empty_data1D(np.log10(1e-4), np.log10(1), 10000)
        model = DirectModel(test_data, current_model)
        result = model(**pars)
    else:
        model = Model(current_model, **pars)
        if par_limits:
            for name in par_limits.keys():
                attr = getattr(model, name)
                if par_limits[name].get("lower") or par_limits[name].get("upper"):
                    lower_limit = par_limits[name]["lower"] if par_limits[name]["lower"] else attr.limits[0]
                    upper_limit = par_limits[name]["upper"] if par_limits[name]["upper"] else attr.limits[1]
                    attr.range(lower_limit, upper_limit)
        
        #TODO implement using Loader() instead of load_data
        """loader = Loader()
        test_data = loader.load(f.path)[0]"""
        f = fit_db.data_id.file
        test_data = load_data(f.path)
        M = Experiment(data = test_data, model=model)
        #TODO be able to do multiple experiments
        problem = FitProblem(M)
        if fit_db.optimizer:
            result = fit(problem, method=fit_db.optimizer)
        else:
            result = fit(problem)
    return result


def get_parameters(fit_id):
    pars = {}
    par_limits = {}
    fit_db = get_object_or_404(Fit, id = fit_id)
    default_parameters = load_model_info(fit_db.model).parameters.defaults
    if fit_db.analysisparameterbase_set.all():
        for x in fit_db.analysisparameterbase_set.all():
            num = eval(f"{x.data_type}({x.value})")
            #TODO check if x.name is a valid parameter else return blah
            #pars = {x.name: num for x in parameter_serializer.data for num = eval(...)}
            pars[x.name] = num

            #TODO make it not create blank dicts for no limits
            one_limit = {}
            if x.lower_limit:
                one_limit.update({"lower":x.lower_limit})
            if x.upper_limit:
                one_limit.update({"upper":x.upper_limit})
            par_limits.update({x.name:one_limit})
        #add in default parameters that don't exist
        for key, value in default_parameters.items():
            if key not in pars.keys():
                pars[key] = value
    #TODO check if this is necessary
    else:
        pars = default_parameters
    return [pars, par_limits]


@api_view(['GET'])
def view_results(request, fit_id, version=None):
    if request.method == 'GET':
        fit_obj = get_object_or_404(Fit, id = fit_id)
        return Response({"results":fit_obj.results})
    return HttpResponseBadRequest()


@api_view(['GET'])
def status(request, fit_id = None, version = None):
    if request.method == "GET":
        #TODO figure out private later <- probs write in Fit model
        return_info = {}
        if fit_id:
            fit_obj = get_object_or_404(Fit, id = fit_id)
            if fit_obj.is_public or request.user.is_authenticated:
                return_info = {"fit_id" : fit_id, "status" : fit_obj.status}
        elif request.user.is_authenticated:
            fit_obj = Fit.objects.filter(current_user = request.user)
            for x in fit_obj:
                return_info[x.id] = x.status
        return Response(return_info)
    return HttpResponseBadRequest()


@api_view(['GET'])
def view_parameters(request, fit_id, version = None):
    if request.method == "GET":
        return Response({"parameters": get_parameters(fit_id)[0], "parameter limits": get_parameters(fit_id)[1]})
    return HttpResponseBadRequest()


@api_view(['GET'])
def fit_info(request, fit_id, version = None):
    if request.method == "GET":
        f = status(request=request._request, fit_id=fit_id).data
        x = view_parameters(request = request._request, fit_id=fit_id).data
        r = view_results(request = request._request, fit_id=fit_id).data
        return Response({"status" : f, "parameters" : x, "results" : r})
    return HttpResponseBadRequest()


@api_view(['GET'])
def list_optimizers(request, version = None):
    if request.method == "GET":
        return_info = {"optimizers" : [fitters.FIT_ACTIVE_IDS]}
        return Response(return_info)
    return HttpResponseBadRequest()


@api_view(['POST'])
def list_model(request, version = None):
    if request.method == "POST":
        unique_models = {}
        #work on being able to do both
        if request.data:
            if request.data.get("category") and request.data.get("kind"):
                return HttpResponseBadRequest("Currently you cannot choose both category and kind, try again")
            elif request.data.get("category"):
                category = request.data.get("category").capitalize()
                user_file = CategoryInstaller.get_user_file()
                with open(user_file) as cat_file:
                    file_contents = json.load(cat_file)
                spec_cat = file_contents.get(category, [])
                unique_models[category + " models"] = spec_cat
            elif request.data.get("kind"):
                if list_models(request.data.get("kind")):
                    model_choices = list_models(request.data.get("kind"))
                    unique_models[request.data.get("kind") + " models"] = model_choices
        else:
            #unique_models["models"] = MODEL_CHOICES
            model_choices = list_models("all")
            unique_models["all models"] = model_choices
        return Response(unique_models)
        """TODO requires discussion:
        if request.username:
            if request.user.is_authenticated:
                user_models = 
                listed_models += {"plugin_models": user_models}
        """
    return HttpResponseBadRequest()

#takes DataInfo and saves it into to specified file location
