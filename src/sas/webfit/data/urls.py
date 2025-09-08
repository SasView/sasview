import logging

from django.urls import path

from . import views

logger = logging.getLogger(__name__)

urlpatterns = [
    path("list/", views.list_data, name = "list public file_ids"),
    path("list/<str:username>/", views.list_data, name = "view users file_ids"),
    path("load/<int:db_id>/", views.data_info, name = "views data using file id"),

    path("upload/", views.upload, name = "upload data into db"),
    path("upload/<data_id>/", views.upload, name = "update file in data"),
    path("<int:data_id>/download/", views.download, name = "download data from db"),
]
