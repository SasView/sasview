import logging

from django.urls import include, path

from . import views

logger = logging.getLogger(__name__)

#info urls
info_patterns = [
    path("", views.fit_info),
    path("status/", views.status, name = "get status using fit_id"),
    path("parameters/", views.view_parameters, name = "current parameters"),
    #TODO implement parameter trace
    #path("parameter_history/"),
    #TODO allow user to find specific parts of results
    path("results/", views.view_results, name = "current results"),
    #TODO implement results trace
    #path("results_history/")
]

#urls to fit
urlpatterns = [
    path("", views.start, name = "starting a fit"),
    path("status/", views.status, name = "get status of all user's fits"),
    path("<int:fit_id>/", include(info_patterns), name = "get fit info"),
    path("optimizers/", views.list_optimizers, name = "lists all fit optimizers"),
    path("models/", views.list_model, name = "lists all fit models"),
    path("models/<str:category>/", views.list_model, name = "lists all fit models"),
    path("models/<str:kind>/", views.list_model, name = "lists all fit models"),
]
