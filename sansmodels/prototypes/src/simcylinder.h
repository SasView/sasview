#if !defined(simcylinder_h)
#define simcylinder_h

#include "modelCalculations.h"

/** Structure definition for simulated cylinder parameters 
 * [PYTHONCLASS] = SimCylinder
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

    /// Maximum Q (for numerical calculations)
    //  [DEFAULT]=qmax=0.1
    double qmax;
    // Variables for numerical calculations 
    CalcParameters calcPars;
    
} SimCylinderParameters;

/// 1D scattering function
double simcylinder_analytical_1D(SimCylinderParameters *pars, double q);

/// 2D scattering function
double simcylinder_analytical_2D(SimCylinderParameters *pars, double q, double phi);

int simcylinder_generatePoints(SpacePoint * points, int n, double radius, double length);

#endif
