################################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation. 
#
#See the license text in license.txt
#
#copyright 2008, University of Tennessee
################################################################################


Park_integration provides various fitting engines for SansView to use.
ParkFitting performs a fit using the Park package, whereas ScipyFitting
performs a fit using the SciPy package. The format of these fitting
engines is based on the AbstractFitEngine class, which uses DataLoader
to transmit data. The Fitting class contains contains ScipyFit and 
ParkFit method declarations, which allows the user
to create an instance of type ScipyFit or ParkFit.

Packages dependencies:
- park
- scipy
- numpy