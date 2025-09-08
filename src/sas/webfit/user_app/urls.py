import logging

from django.urls import include, path

from .views import KnoxLoginView, KnoxRegisterView

logger = logging.getLogger(__name__)

urlpatterns = [
    path('login/', KnoxLoginView.as_view(), name='knox_login'),
    path('knox/', include('knox.urls')), #for logout
    path('registration/', KnoxRegisterView.as_view(), name='knox_register'),
    path('', include('dj_rest_auth.urls')),
    path('', include('allauth.urls')),
]
