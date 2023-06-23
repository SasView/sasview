from django.urls import path, include
from .views import bumps

urlpatterns = [
    #url to fit
    path("bumps/", bumps.run),
    

]