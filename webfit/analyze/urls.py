from django.urls import path, include
from analyze.fitting import views

#urls to fit
fit_patterns = [
    path("bumps/", views.run),   
]

urlpatterns = [
    path("fit/", include(fit_patterns)),
    #path("Inversion/", include()),   <- where is this in the main script? 
    #path("Invariant/", include()),
    #path("Corfunc/", include()),
]