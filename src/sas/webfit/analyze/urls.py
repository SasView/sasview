import logging

from django.urls import include, path

logger = logging.getLogger(__name__)

urlpatterns = [
    #path("<str:username>/<int:data_id>/", views.list_analysis_done, "view analysis done"),

    path("fit/", include("analyze.fitting.urls"), name = "fit patterns"),
    #path("Inversion/", include()),   <- where is this in the main script?
    #path("Invariant/", include()),
    #path("Corfunc/", include()),
]
