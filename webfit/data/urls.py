import logging
from django.urls import path, re_path, include
from . import views

logger = logging.getLogger(__name__)

urlpatterns = [
    path("list/", views.list_data, name = "list public file_ids"),
    path("list/user/<int:db_id>/", views.list_data, name = "view users file_ids"),
    path("info/<int:db_id>", views.data_info, name = "views data using file id"),

    path("upload/", views.upload, name = "upload data into db"),
    path("upload/<data_id>/", views.upload, name = "update file in data"),
    path("<int:data_id>/download/", views.download, name = "download data from db"),
]