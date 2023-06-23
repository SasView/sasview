"""
URL configuration for webfit project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import logging

from django.contrib import admin
from django.apps import apps
from django.urls import path, re_path, include
from rest_framework.reverse import reverse

#TO DO: finalize version control
#this doesn't go here... figure out where this goes
reverse("", request=request)

#base urls 
# no urls for pluggins currently
urlpatterns = [
    #admin page
    path("admin/", admin.site.urls),

    #root url
    path("", include("user_authentication.urls"), name = "homepage + login"),
    
    #fit path
    path("analyze/", include("analyze.urls"), name = "analysis tools"),
]

