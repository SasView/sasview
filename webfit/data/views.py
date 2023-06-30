from django.shortcuts import render
from django.shortcuts import HttpResponse
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.http import Http404
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status

from serializers import DataSerializers
from user_authentication.models import User
from .models import Data

serializer = DataSerializers()

@api_view(['POST', 'PUT'])
def import_file_string(request, version):         
    #saves file_string
    if request.method == 'POST':
        serializer(file_string = request.file_string)
        if serializer.is_valid():
            serializer.save()
            #TODO fix so it only returns specific response, create UserViewSet
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    #saves or updates file_string
    if request.method == 'PUT':
        if User.anonymous == False:
            #checks to see if there is an existing file to update
            try:
                file = Data.objects.get(file_string=request.file_string)
            except Data.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)
            

            serializer(file, file_string=request.file_string)
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
def export_data(request, version = None):
    #saves the file string to where to save data
    if request.method == 'POST':
        serializer(save_file_string = request.save_file_string)
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
            try:
                save_file = Data.objects.get(save_file_string=request.save_file_string)
            except Data.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)
        
            serializer(save_file, save_file_string=request.save_file_string)
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
    try:
        example_data = Data.objects.get(example_data)
    except Data.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    serializer(example_data, loader.load(request.file_string))