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