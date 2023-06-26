from django.shortcuts import render
from django.http import HttpResponse

#turn into authentication/user login later
def placeholder_login_screen(request, version = None):
    if version == "v1":
        return HttpResponse("login screen placeholder")
    else:
        return HttpResponse("nope")