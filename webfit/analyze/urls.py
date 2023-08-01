import logging
from django.urls import path, re_path, include
from analyze.fitting import views as fit_views
from . import views

logger = logging.getLogger(__name__)

#urls to fit
fit_patterns = [
    path("", fit_views.start, name = "starting a fit"),  
    #TODO add specific urls that return certain options
    #path("return_.../", fit_views.start, name = "starting a fit"),    
    path("<int:fit_id>/", fit_views.fit_status, name = "get status using fit_id"),
    path("optimizers/", fit_views.list_optimizers, name = "lists all fit optimizers"),
    path("models/", fit_views.list_model, name = "lists all fit models"),
    path("status/<int:fit_id>", fit_views.status, name = "status of fit using fit db id"),
]

urlpatterns = [
    #path("<str:username>/<int:data_id>/", views.list_analysis_done, "view analysis done"),
    
    path("fit/", include(fit_patterns), name = "fit patterns"),
    #path("Inversion/", include()),   <- where is this in the main script? 
    #path("Invariant/", include()),
    #path("Corfunc/", include()),
]