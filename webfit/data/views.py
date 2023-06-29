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
    try:
        file = file_id
    except Data.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    #saves file_string
    if request.method == 'POST':
        serializer = DataSerializers(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    if User.anonymous == False:
        #saves or updates file_string
        if request.method == 'PUT':
            serializer = DataSerializers(imported_data, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    else:
        return HttpResponseForbidden()
    
    #data is actually loaded inside fit view

@api_view(['POST', 'PUT'])
def export_data(request, version = None):
    #saves the file string to where to save data
    if request.method == 'POST':
        where_to_save_string = Data.objects.all()
        serializer = DataSerializers(where_to_save_string, many=True)
        return Response(serializer.data)
    
    if User.anonymous == False:
        #saves or updates file_string
        if request.method == 'PUT':
            serializer = DataSerializers(imported_data, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
def export_to_example_data():
    