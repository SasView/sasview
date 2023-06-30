import logging
from django.urls import path, re_path, include
from . import views

logger = logging.getLogger(__name__)

urlpatterns = [
    path("list/", views.get_data, name = "view users data"),
    path("import/", views.import_file_string, name = "import data"),
    path("export/", views.export_data, name = "export/save data"),
]