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

        #{str: param_name: value}
        pars = None
        #{str:param_name:{lower, upper}}
        par_limits = None

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
        result = start_fit(fit_db, all_param_dbs)
        base_serializer(fit_db, data = {"results": result})
        if base_serializer.is_valid():
            base_serializer.save()
        else:
            return Response(base_serializer.errors)

        #add "warnings": ... later
        return Response({"authenticated":request.user.is_authenticated, "fit_id":fit_db.id, "results":fit_db.results})
    return HttpResponseBadRequest()


def start_fit(fit_db = None, par_dbs = None):
    current_model = load_model(fit_db.model)
    default_parameters = load_model_info(fit_db.model).parameters.defaults

    if par_dbs:
        pars = {}
        par_limits = {}
        for x in par_dbs:
            num = eval(f"{x.data_type}({x.value})")
            #TODO check if x.name is a valid parameter else return blah
            #pars = {x.name: num for x in parameter_serializer.data for num = eval(...)}
            pars[x.name] = num

            #TODO reduce redundancies
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
    else:
        pars = default_parameters

    if not fit_db.data_id:
        #TODO impliment qmin/qmax
        test_data = empty_data1D(np.log10(1e-4), np.log10(1), 10000)
        call_kernel = DirectModel(test_data, current_model, pars)
        #return call_kernel...     
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
        test_data.dy = 0.2*test_data.y
        M = Experiment(data = test_data, model=model)
        problem = FitProblem(M)
        if fit_db.optimizer:
            result = fit(problem, method=fit_db.optimizer)
            return problem.chisq_str()
        else:
            result = fit(problem)

    #problem.fitness.model.state() <- return this dictionary to check if fit is actually working
    return "welp"

    #below code is in testing, used for when fit/ is scheduled with status
    """
    fit_db.status = 3
    fit_db.result = result
    OR...
    return result <- and whatever func this returns to sets ^^
    """


@api_view(['GET'])
def status(request, fit_id, version=None):
    if fit_id:
        fit_db = get_object_or_404(Fit, id = fit_id)
        if fit_db.is_public or request.user.is_authenticated: #do I need to add request.user = fit_db.current_user
            return Response(fit_db.status)
        return HttpResponseBadRequest("You are not authorized to see this private fit")
    return HttpResponseBadRequest("you have not submitted a fit_id")


@api_view(['GET'])
def fit_status(request, fit_id, version = None):
    fit_obj = get_object_or_404(Fit, id = fit_id)
    if request.method == "GET":
        #TODO figure out private later <- probs write in Fit model
        if not (fit_obj.is_public or request.user.is_authenticated):
            return HttpResponseBadRequest("user isn't logged in")
        return_info = {"fit_id" : fit_id, "status" : Fit.status}
        if Fit.results:
            return_info+={"results" : Fit.results}
        return Response(return_info)
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
