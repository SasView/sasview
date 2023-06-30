import logging
from django.urls import path, re_path, include
from . import views

logger = logging.getLogger(__name__)

urlpatterns = [
    path("list/", views.get_data, name = "view users data"),
    path("upload/", views.upload, name = "upload data into db"),
    path("download/", views.download, name = "download data from db"),
]