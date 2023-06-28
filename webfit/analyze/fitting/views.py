from logging import getLogger
from django.shortcuts import render
from django.http import HttpResponse
from sasdata.dataloader.loader import Loader
from .models import Fit

fit_logger = getLogger(__name__)

#how do i get loader to work here?
#what exactly am i trying to load
#should this be in models instead

#LOADER


def run(request, version = None):
    return HttpResponse("test")