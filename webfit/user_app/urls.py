import logging
from django.urls import path, re_path, include
from .views import KnoxLoginView, KnoxRegisterView

logger = logging.getLogger(__name__)

urlpatterns = [
    path("register/", KnoxLoginView.as_view(), name = "list public file_ids"),
    path("login/", KnoxRegisterView.as_view(), name = "list public file_ids"),
]