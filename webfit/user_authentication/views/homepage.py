from logging import getLogger
from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.versioning import URLPathVersioning

homepage_logger = getLogger(__name__)

# test function
def placeholder(request):
    return HttpResponse("Hi")
