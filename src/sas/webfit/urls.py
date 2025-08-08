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
from django.urls import include, path, re_path

logger = logging.getLogger(__name__)

#TO DO: finalize version control

#base urls
# no urls for plugins currently
urlpatterns = [
    #admin page
    path("admin/", admin.site.urls, name = "admin page"),

    #authentication
    path("auth/", include("user_app.urls"), name = "login/register/logout tools"),
    #re_path(r"auth/", include("knox.urls")),
    #path('auth/', include('dj_rest_auth.urls')),

    #data path
    re_path(r"^(?P<version>(v1))/data/", include("data.urls"), name = "data tools"),

    #perspective paths
    re_path(r"^(?P<version>(v1))/analyze/", include("analyze.urls"), name = "analysis tools"),
]

