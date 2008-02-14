#if !defined(simcylinderf_h)
#define simcylinderf_h

#include "modelCalculations.h"

/** Structure definition for simulated cylinder parameters 
 * [PYTHONCLASS] = SimCylinderF
 * */
typedef struct {
    /// Scale factor 
    //  [DEFAULT]=scale=1.0
    double scale;

    /// Radius of the cylinder
    //  [DEFAULT]=radius=20.0
    double radius;

    /// Length of the cylinder
    //  [DEFAULT]=length=400.0
    double length;

    /// Theta angle relative to beam
    //  [DEFAULT]=theta=0.0
    double theta;

    /// Phi angle relative to x-axis
    //  [DEFAULT]=phi=0.0
    double phi;

    /// Number of space points
    //  [DEFAULT]=npoints=50000
    double npoints;

    /// Random number seed
    //  [DEFAULT]=seed=1000.0
    double seed;

    // Variables for numerical calculations 
    CalcParameters calcPars;
    
} SimCylinderFParameters;

/// 1D scattering function
double simcylinder_fast_analytical_1D(SimCylinderFParameters *pars, double q);

/// 2D scattering function
double simcylinder_fast_analytical_2D(SimCylinderFParameters *pars, double q, double phi);

int simcylinder_fast_generatePoints(SpacePoint * points, int n, double radius, double length, int seed);
SpacePoint fast_rotate(SpacePoint p, double theta, double phi, double omega);
double simcylinder_simple_analytical_2D(SimCylinderFParameters *pars, double q, double phi);

#endif
