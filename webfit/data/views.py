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


@api_view(['POST', 'PUT'])
def import_file_string(request, file_id, version):    

    #saves file_string
    if request.method == 'POST':
        serializer = DataSerializers(file_string=file_id)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    #saves or updates file_string
    if request.method == 'PUT':
        if User.anonymous == False:
            #checks to see if there is an existing file to update
            try:
                file = Data.objects.get(file_string=file_id)
            except Data.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)
            

            serializer = DataSerializers(file, file_string=file_id)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        #user is not logged in -> not allowed to update
        else:
            return HttpResponseForbidden()
    
    #data is actually loaded inside fit view

@api_view(['POST', 'PUT'])
def export_data(request, save_file_id, version = None):
    #saves the file string to where to save data
    if request.method == 'POST':
        serializer = DataSerializers(save_file_string = save_file_id)
        return Response(serializer.data)
    
    #saves or updates file_string
    if request.method == 'PUT':
        if User.anonymous == False:
            #checks to see if there is an existing file to update
            try:
                save_file = Data.objects.get(save_file_string=save_file_id)
            except Data.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)
        
            serializer = DataSerializers(save_file, save_file_string=save_file_id)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
def export_to_example_data():
    