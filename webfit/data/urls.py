import logging
from django.urls import path, re_path, include
from . import views

logger = logging.getLogger(__name__)

urlpatterns = [
    path("import/<str:file_id>/", views.import_file_string, name = "import data"),
    path("export/", views.export_data, name = "export/save data")
]