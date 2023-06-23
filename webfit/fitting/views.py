from django.shortcuts import render
from django.http import HttpResponse

# test function
def placeholder(request):
    return HttpResponse("Hi")
