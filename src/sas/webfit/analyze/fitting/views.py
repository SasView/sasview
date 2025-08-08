import json
from logging import getLogger

import numpy as np
from bumps import fitters
from bumps.fitProblem import FitProblem
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from serializers import (
    FitParameterSerializer,
    FitSerializer,
)

from sasmodels.bumps_model import Experiment, Model
from sasmodels.core import list_models, load_model, load_model_info
from sasmodels.data import empty_data1D, load_data
from sasmodels.direct_model import DirectModel

#TODO categoryinstallers should belong in SasView.System rather than in QTGUI
from sas.qtgui.Utilities.CategoryInstaller import CategoryInstaller
from sas.sascalc.fit.models import ModelManager

from .models import (
    Fit,
    FitParameter,
)

fit_logger = getLogger(__name__)
model_manager = ModelManager()
#TODO add view that gets previous fit results
#TODO finish view for get status

#start() only puts all the request data into the db, start_fit() runs calculations
"""
Documentation for user input: User input should look like this:
{
    "current_user": int
    "data_id": int
    "model":str
    "parameters": [
        {
        "name":str
        "value":int/float
        "datatype":
        "lower":int
        "upper":int
        }
    ]
}
"""

@api_view(['POST'])
def start(request, version = None):
    if request.method == "POST":
        #TODO set status
        #TODO add constraints

        base_serializer = FitSerializer(data=request.data)
        if base_serializer.is_valid():
            base_serializer.save()
        else:
            return Response(base_serializer.errors)

        fit_db = get_object_or_404(Fit, id = base_serializer.data["id"])

        if not load_model(fit_db.model.lower()):
            fit_db.delete()
            return HttpResponseBadRequest("No model selected for fitting")

        if fit_db.data_id:
            if not (fit_db.data_id.is_public or (request.user.is_authenticated and
                    request.user is fit_db.data_id.current_user)):
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

        #TODO move below data to created queuing function
        result = start_fit(fit_db)

        #TODO result_serializer should actually be formatted to save result.model.state() in parameter database,
        #with parameter name like "name = 'fit_radius'"
        result_serializer = FitSerializer(fit_db, data = {"results": str(result), "status":3}, partial=True)
        if result_serializer.is_valid():
            result_serializer.save()
        else:
            return Response(result_serializer.errors)
        fit_db = get_object_or_404(Fit, id = result_serializer.data["id"])

        #add "warnings": ... later
        return Response({"authenticated":request.user.is_authenticated, "fit_id":fit_db.id, "results":result})

    return HttpResponseBadRequest()


def start_fit(fit_db):
    #fit_db.status = 2
    current_model = load_model(fit_db.model.lower())

    pars, par_limits = get_parameters(fit_db.id)

    q_min = np.log10(fit_db.q_minimum)
    q_max = np.log10(fit_db.q_maximum)
    #TODO figure out how to set qmin/qmax for normal Data1D
    test_data = load_data(fit_db.data_id.file.path) if fit_db.data_id else empty_data1D(np.logspace(q_min, q_max, 10000))
    if not par_limits or test_data.y is None:
        model = DirectModel(test_data, current_model)
        result = model(**pars)
    else:
        model = Model(current_model, **pars)
        if par_limits:
            for name in par_limits.keys():
                attr = getattr(model, name)
                lower_limit = par_limits[name]["lower"] if par_limits[name]["lower"] else attr.limits[0]
                upper_limit = par_limits[name]["upper"] if par_limits[name]["upper"] else attr.limits[1]
                attr.range(lower_limit, upper_limit)

        #TODO implement using Loader() instead of load_data
        """loader = Loader()
        test_data = loader.load(f.path)[0]"""

        if hasattr(test_data, "err_data") and (not test_data.err_data or test_data.err_data == []):
            test_data.err_data = np.ones(len(test_data.data))
        else:
            if test_data.dy is None or test_data.dy == [] or test_data.dy.all() == 0:
                test_data.dy = np.ones(len(test_data.y))
            #self.idx = self.idx & (self.dy != 0)
        M = Experiment(data = test_data, model=model)
        #TODO be able to do multiple experiments
        problem = FitProblem(M)
        if fit_db.optimizer:
            fitted = fitters.fit(problem, method=fit_db.optimizer)
        else:
            fitted = fitters.fit(problem)
        #TODO results to be formatted differently later
        result = M.__getstate__()
        result['_data'] = test_data.__str__()
        result['_model'] = fit_db.model
        result['_resolution'] = str(M.resolution.q) + ', ' + str(M.resolution.q_calc)
        result['model'] = model.state()
        result["parameter_limits"] = str(model.length.bounds.limits)
        result["old_parameters"] = pars
    return result


def get_parameters(fit_id):
    #what this returns
    """
    pars: {
    "name" : value
    }
    par_limits: {
    "name_lower_limit":value,
    "name_upper_limit":upper
    }
    """
    pars = {}
    par_limits = {}
    fit_db = get_object_or_404(Fit, id = fit_id)
    default_parameters = load_model_info(fit_db.model.lower()).parameters.defaults
    if fit_db.analysisparameterbase_set.all():
        for x in fit_db.analysisparameterbase_set.all():
            #TODO add check if x.name is a valid parameter else return HTTPBadRequest
            pars[x.name] = eval(f"{x.data_type}({x.value})") if x.value else default_parameters[x.name]
            if x.analyze:
                par_limits[x.name] = {"lower":x.lower_limit, "upper": x.upper_limit}
    return pars, par_limits


@api_view(['GET'])
def view_results(request, fit_id, version=None):
    if request.method == 'GET':
        fit_obj = get_object_or_404(Fit, id = fit_id)
        #results = json.loads(fit_obj.results)
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
        pars, par_limits = get_parameters(fit_id)
        return Response({"parameters": pars, "parameter limits": par_limits})
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
        return_info = {"optimizers" : fitters.FIT_ACTIVE_IDS}
        return Response(return_info)
    return HttpResponseBadRequest()


#TODO strip models that are in blacklist, categoryinstaller get rid of those that are False
#TODO implement category manager
#TODO in fresh install categories.json is gone, fix
#TODO move code to share between both qtgui and webfit, move to CategoryInstaller
#TODO CategoryInstaller should be moved to sasmodels? (as it manages models)
def regenerate_category_dict(cat_name):
    user_file = CategoryInstaller.get_user_file()
    with open(user_file) as cat_file:
        file_contents = json.load(cat_file)
    #TODO format it to remove boolean
    spec_cat = file_contents.get(cat_name, [])
    content = []
    for x in spec_cat:
        content.append(x[0])
    return content


@api_view(['GET'])
def list_model(request, category = None, kind = None, version = None):
    if request.method == "GET":
        unique_models = {}
        #work on being able to do both

        if category:
            cat_name = category.capitalize()
            unique_models[cat_name + " models"] = regenerate_category_dict(cat_name)
        elif kind:
            if list_models(kind):
                model_choices = list_models(kind)
                unique_models[kind + " models"] = model_choices
        else:
            model_choices = list_models("all")
            unique_models["all models"] = model_choices
        return Response(unique_models)
        '''TODO requires discussion:
        if request.username:
            if request.user.is_authenticated:
                user_models =
                listed_models += {"plugin_models": user_models}
        '''
    return HttpResponseBadRequest()
