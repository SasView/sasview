#if !defined(testsphere_h)
#define testsphere_h

#include "modelCalculations.h"

/** Structure definition for sphere parameters 
 * [PYTHONCLASS] = TestSphere2
 * */
typedef struct {
    /// Scale factor 
    //  [DEFAULT]=scale=1.0
    double scale;
    /// Radius of the sphere
    //  [DEFAULT]=radius=20.0
    double radius;
    /// Maximum Q (for numerical calculations)
    //  [DEFAULT]=qmax=0.1
    double qmax;
    // Variables for numerical calculations 
    CalcParameters calcPars;
    
} TestSphereParameters;

/// 1D scattering function
double testsphere_analytical_1D(TestSphereParameters *pars, double q);

/// 2D scattering function
double testsphere_analytical_2D(TestSphereParameters *pars, double q, double phi);

/// 1D scattering function
double testsphere_numerical_1D(TestSphereParameters *pars, int *array, double q);

/// 2D scattering function
double testsphere_numerical_2D(TestSphereParameters *pars, int *array, double q, double phi);

int testsphere_generatePoints(SpacePoint * points, int n, double radius);

#endif
