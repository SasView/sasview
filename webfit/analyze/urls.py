import logging
from django.urls import path, include
from analyze.fitting import views

logger = logging.getLogger(__name__)

#urls to fit
fit_patterns = [
    path("bumps/", views.run, "bumps"),   
]

urlpatterns = [
    path("fit/", include(fit_patterns), name = "fitter"),
    #path("Inversion/", include()),   <- where is this in the main script? 
    #path("Invariant/", include()),
    #path("Corfunc/", include()),
]