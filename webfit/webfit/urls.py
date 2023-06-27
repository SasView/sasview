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
from django.urls import path, re_path, include
from rest_framework import routers, serializers

#TO DO: finalize version control

#base urls 
# no urls for pluggins currently
urlpatterns = [
    #admin page
    path("admin/", admin.site.urls),

    #r"^(?P<name>.+)/$
    #re_path(r"^tool_information/(?P<tool_id>\d+)/(?P<user_id>\d+)/(?P<back>back_to_start|back_to_category)/$", views.tool_information, name="kiosk_tool_information"),
    #root url
    path("", include("user_authentication.urls"), name="homepage"),
    
    #fit path
    
    path("<str:version>/analyze/", include("analyze.urls"), name = "analysis tools"),
]

