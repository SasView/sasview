"""a file for pathing for all analyze app pathing
currently only fitting is created, which makes this seem redundant"""

from django.urls import path, include

urlpatterns = [
    path("fit/", include("analyze.fitting.urls")),
    #path("Inversion/", include("fittings.urls")),   <- where is this? 
    #path("Invariant/", include("fittings.urls")),
    #path("Corfunc/", include("fittings.urls")),
]