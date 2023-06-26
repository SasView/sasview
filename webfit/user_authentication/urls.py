from django.urls import path, re_path, include
from .views import homepage, authentication


urlpatterns = [
    path("", homepage.placeholder),
    re_path(r"^(?P<version>(v1))/login/$", authentication.placeholder_login_screen, name="login placeholder"),
]