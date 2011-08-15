Park_integration provides various fitting engines for Sansview to use.
ParkFitting performs a fit using the Park package, whereas ScipyFitting
performs a fit using the SciPy package. The format of these fitting
engines is based on the AbstractFitEngine class, which uses DataLoader
to transmit data. The Fitting class contains contains ScipyFit and 
ParkFit method declarations, which allows the user
to create an instance of type ScipyFit or ParkFit.