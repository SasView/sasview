import logging
from django.urls import path, re_path, include
from analyze.fitting import views

logger = logging.getLogger(__name__)

#urls to fit
fit_patterns = [
    path("", views.start, name = "starting a fit"),  
]

urlpatterns = [
    path("fit/", include(fit_patterns), name = "fit patterns"),
    #path("Inversion/", include()),   <- where is this in the main script? 
    #path("Invariant/", include()),
    #path("Corfunc/", include()),
]