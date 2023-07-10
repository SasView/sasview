from django.shortcuts import get_object_or_404
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework.decorators import api_view

from sasdata.dataloader.loader import Loader
from serializers import DataSerializers
from .models import Data

#TODO finish logger
#TODO look through whole code to make sure serializer updates to the correct object

@api_view(['GET'])
def list_data(request, db_id = None, version = None):
    if request.method == 'GET':
        data_list = {}
        public_data = Data.objects.filter(is_public = True)
        data_list += {"public_file_ids": public_data.id}
        if request.user.is_authenticated:
            data = get_object_or_404(Data, id=db_id)
            data_list += {"user_data_ids": data.user_data_ids}
        return Response(data_list)
    return HttpResponseBadRequest()


@api_view(['GET'])
def data_info(request, db_id, version = None):
    if request.method == 'GET':
        public_data = Data.objects.filter(id = db_id, is_public=True)
        #TODO check if this actually checks the id is public/properly logged in
        if public_data or request.user.is_authenticated:
            file = get_object_or_404(Data, id = db_id)
            #TODO ^^ how to check if file_id is in user_file_ids
            #TODO check if this loads the file correctly
            return_data = {"info" : file.file.__str__()}
            return return_data
        return HttpResponseBadRequest("Database ID not public")
    return HttpResponseBadRequest()


#perhaps rename data.obj from file -> data_obj as it gets confused with file.file
@api_view(['POST', 'PUT'])
def upload(request, version = None):
    serializer = DataSerializers()
    file = get_object_or_404(Data)
    
    #saves file
    if request.method == 'POST':
        serializer(file = request.file, is_public = request.data.is_public)
    
    #saves or updates file
    elif request.method == 'PUT':
        if request.user.is_authenticated:
            #checks to see if there is an existing file to update
            file(username = request.data.username)
            serializer(file, file=request.file, is_public = request.data.is_public)
        else:
            return HttpResponseForbidden()

    if serializer.is_valid():
        serializer.save()
        #TODO get warnings/errors later
        return_data = {"authenticated" : request.user.is_authenticated, "file_id" : howeveryougetthefileid, "is_public" : serializer.is_public}
        return Response(return_data)
    return HttpResponseBadRequest()
    #data is actually loaded inside fit view


#TODO check if I should move to fit
@api_view(['GET'])
def download(request, version = None):
    serializer = DataSerializers()
    #saves the file string to where to save data
    if request.method == 'POST':
        serializer(save_file_string = request.save_file_string)
    
    #saves or updates save_file_string
    elif request.method == 'PUT':
        if request.user.is_authenticated:
            #checks to see if there is an existing file to update
            save_file = get_object_or_404(Data, username = request.username)
            serializer(save_file, save_file_string = request.save_file_string)
        else:
            return HttpResponseForbidden()

    if serializer.is_valid():
        serializer.save()
        #CHECK not sure if the serializer will be able to get the id
        #TODO get warnings/errors later
        return_data={"authenticated" : request.user.is_authenticated, "file_id" : serializer.data.id}
        return Response(return_data)
    return HttpResponseBadRequest()
        
