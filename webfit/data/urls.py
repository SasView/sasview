import logging
from django.urls import path, re_path, include
from . import views

logger = logging.getLogger(__name__)

urlpatterns = [
    re_path(r"import/(?P<file_id>)/$", views.import_file_string, name = "import data"),
    re_path(r"import/(?P<file_id>)/(?P<opt_in>)/$", views.import_file_string, name = "import data and opt in"),
    path("export/", views.export_data, name = "export/save data")
]