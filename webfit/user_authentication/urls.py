import logging
from django.urls import path, re_path, include
from .views import homepage, authentication

logger = logging.getLogger(__name__)

urlpatterns = [
    path("", homepage.placeholder, name = "homepage"),
    path("<str:version>/login/", authentication.placeholder_login_screen, name="login placeholder"),
]