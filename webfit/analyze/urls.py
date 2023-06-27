import logging
from django.urls import path, re_path, include
from analyze.fitting import views

logger = logging.getLogger(__name__)

#urls to fit
fit_patterns = [
    re_path(r"^(?P<version>(v1))/bumps/$", views.run, name = "bumps"),   
]

urlpatterns = [
    path("fit/", include(fit_patterns), name = "fitter"),
    #path("Inversion/", include()),   <- where is this in the main script? 
    #path("Invariant/", include()),
    #path("Corfunc/", include()),
]