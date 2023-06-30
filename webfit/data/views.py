from django.shortcuts import HttpResponse, render, get_object_or_404
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.http import Http404
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status

from serializers import DataSerializers
from user_authentication.models import User
from .models import Data


@api_view(['GET'])
def get_data(request, version):
    if request.method == 'GET':
        public_data = get_object_or_404(Data)
        data_list = {"public_file_ids": public_data.public_file_ids}
        if request.user.is_authenticated:
            data = get_object_or_404(Data, username=request.username)
            data_list += {"user_data_ids": data.user_data_ids}
            return Response(data_list)


@api_view(['POST', 'PUT'])
def upload(request, version):         
    #saves file_string
    if request.method == 'POST':
        serializer = DataSerializers(file_string = request.file_string)
        if serializer.is_valid():
            serializer.save()
            #TODO fix so it only returns specific response, create UserViewSet
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    #saves or updates file_string
    if request.method == 'PUT':
        if User.anonymous == False:
            #checks to see if there is an existing file to update
            file = get_object_or_404(Data, file_string=request.file_string)

            serializer = DataSerializers(file, file_string=request.file_string)
            if serializer.is_valid():
                serializer.save()
                #TODO fix so it only returns specific response, create UserViewSet
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        #user is not logged in -> not allowed to update
        else:
            return HttpResponseForbidden()
    
    #data is actually loaded inside fit view

@api_view(['POST', 'PUT'])
def download(request, version = None):
    #saves the file string to where to save data
    if request.method == 'POST':
        serializer = DataSerializers(save_file_string = request.save_file_string)
        if request.opt_in == True:
            export_to_example_data(request)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    #saves or updates file_string
    if request.method == 'PUT':
        if User.anonymous == False:
            #checks to see if there is an existing file to update
            save_file = get_object_or_404(Data, save_file_string=request.save_file_string)
        
            serializer = DataSerializers(save_file, save_file_string=request.save_file_string)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        #user is not logged in -> not allowed to update
        else:
            return HttpResponseForbidden()
        
#loader = Loader()

#eventually create db inside Data that holds all the example data
def export_to_example_data(request):
    example_data = get_object_or_404(Data, example_data=request.example_data)
    try:
        example_data = Data.objects.get(example_data)
    except Data.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    serializer = DataSerializers(example_data, loader.load(request.file_string))