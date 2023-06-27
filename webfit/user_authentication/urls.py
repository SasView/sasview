import logging
from django.urls import path, re_path, include
from .views import homepage, authentication

logger = logging.getLogger(__name__)

urlpatterns = [
    path("", homepage.placeholder, name = "homepage"),
    re_path(r"^(?P<version>(v1))/login/$", authentication.placeholder_login_screen, name="login placeholder"),
]