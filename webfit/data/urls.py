import logging
from django.urls import path, re_path, include
from . import views

logger = logging.getLogger(__name__)

urlpatterns = [
    path("import/", views.ImportData, name = "import data"),
    path("export/", views.ExportData, name = "export/save data")
]