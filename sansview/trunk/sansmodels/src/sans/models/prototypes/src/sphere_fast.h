#if !defined(simspheref_h)
#define simspheref_h

#include "modelCalculations.h"

/** Structure definition for simulated cylinder parameters 
 * [PYTHONCLASS] = SimSphereF
 * */
typedef struct {
    /// Scale factor 
    //  [DEFAULT]=scale=1.0
    double scale;

    /// Radius of the cylinder
    //  [DEFAULT]=radius=20.0
    double radius;

    /// Number of space points
    //  [DEFAULT]=npoints=50000
    double npoints;

    /// Random number seed
    //  [DEFAULT]=seed=1000
    double seed;

    // Variables for numerical calculations 
    CalcParameters calcPars;
    
} SimSphereFParameters;

/// 1D scattering function
double sphere_fast_analytical_1D(SimSphereFParameters *pars, double q);

/// 2D scattering function
double sphere_fast_analytical_2D(SimSphereFParameters *pars, double q, double phi);

int sphere_fast_generatePoints(SpacePoint * points, int n, double radius, int seed);

#endif
