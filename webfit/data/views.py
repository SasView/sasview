from django.shortcuts import HttpResponse, render, get_object_or_404
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.http import Http404
from django.contrib.auth.models import User
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status

from sasdata.dataloader.loader import Loader
from serializers import DataSerializers
from .models import Data


@api_view(['GET'])
def list_data(request, version = None):
    if request.method == 'GET':
        public_data = Data.objects.filter(opt_in = True)
        data_list = {"public_file_ids": public_data.public_file_ids}
        return Response(data_list)
    return HttpResponseBadRequest()
        

@api_view(['GET'])
def list_data(request, db_id, version = None):
    if request.method == 'GET':
        if request.user.is_authenticated:
            data = get_object_or_404(Data, id=db_id)
            data_list = {"user_data_ids": data.user_data_ids}
            return Response(data_list)
        return HttpResponseForbidden()
    return HttpResponseBadRequest()


@api_view(['GET'])
def data_info(request, db_id, version = None):
    if request.method == 'Get':
        file = get_object_or_404(Data, id = db_id)
        #TODO ^^ how to check if file_id is in user_file_ids
        loader = Loader.load(file.file_string)
        return_data = {"info" : loader.__str__()}
        return return_data
    return HttpResponseBadRequest()

@api_view(['POST', 'PUT'])
def upload(request, version = None):
    serializer = DataSerializers()
    file = get_object_or_404(Data)
          
    #saves file_string
    if request.method == 'POST':
        serializer(file_string = request.file_string, opt_in = request.opt_in)
    
    #saves or updates file_string
    elif request.method == 'PUT':
        if request.user.is_authenticated:
            #checks to see if there is an existing file to update
            file(username = request.username)
            serializer(file, file_string=request.file_string, opt_in = request.opt_in)
        else:
            return HttpResponseForbidden()

    if serializer.is_valid():
        serializer.save()
        if request.opt_in == True:
            export_to_example_data(request)
        else:
            file.user_file_ids += (request.file_string.id, "idk")
        return_data = {"authenticated" : request.user.is_authenticated, "file_id" : howeveryougetthefileid, "opt_in" : serializer.opt_in, "warnings" : serializer.errors}
        return Response(return_data)
    return HttpResponseBadRequest()
    #data is actually loaded inside fit view

@api_view(['POST', 'PUT'])
def download(request, version = None):
    return_data = {}
    serializer = DataSerializers()
    #saves the file string to where to save data
    if request.method == 'POST':
        serializer(save_file_string = request.save_file_string)
    
    #saves or updates file_string
    elif request.method == 'PUT':
        if request.user.is_authenticated:
            #checks to see if there is an existing file to update
            save_file = get_object_or_404(Data, save_file_string=request.save_file_string)
            serializer(save_file, save_file_string=request.save_file_string)
        else:
            return HttpResponseForbidden()

    if serializer.is_valid():
        serializer.save()
        return_data+={"authenticated" : request.user.is_authenticated, "file_id" : howeveryougetthefileid, "warnings" : serializer.errors}
        return Response(return_data)
    return HttpResponseBadRequest()
        


#eventually insert data into example_data
def export_to_example_data(request):
    loader = Loader()
    file = get_object_or_404(Data, username = request.username) 
    serializer = DataSerializers()

    #TODO write if statements to check if the file already exists
    file.public_file_ids += (request.file_string.id, "idk")
    file.example_data += (loader.load(request.file_string), "uhh name later")