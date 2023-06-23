from django.urls import path, include
from .views import homepage, authentication

urlpatterns = [
    path("", homepage.placeholder),
    path("login/", authentication.placeholder_login_screen),
]