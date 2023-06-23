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
from django.contrib import admin
from django.apps import apps
from django.urls import path, include
from rest_framework import routers
from . import settings

#REST API urls
router = routers.DefaultRouter()

#do i need this? reservation_item_types = f'(?P<item_type>{"|".join(ReservationItemType.values())})'

#base urls 
# no urls for pluggins currently

urlpatterns = [
    path("admin/", admin.site.urls),
    path("fitting/", include("fitting.urls"))
]

