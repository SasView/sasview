from django.shortcuts import render
from django.shortcuts import HttpResponse
from django.http import Http404
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status

from .models import Data
from sasdata.dataloader.loader import Loader

loader = Loader()

@api_view(['POST', 'PUT'])
def ImportData(request, pk, version= None):
    if request.method == 'POST':
        x=1


    #takes files string and turn it into DataInfo
    if Data.file_string != False:
        Data.data = loader.load(Data.file_string)
#opt in to uploading to example data pool
    if Data.opt_in == True:
        #upload data to example data pool
        loader.save(loader, file = "PUT FILE STRING HERE LATER", data = Data.data)

def ExportData(request, version = None):
    #takes DataInfo and saves it into to specified file location
    file_locaton = Data.
    loader.save(loader, file = Data.saved_file_string, data = Data.data)
    
    if Data.saved_file == True:
        return(AlreadySavedError)

