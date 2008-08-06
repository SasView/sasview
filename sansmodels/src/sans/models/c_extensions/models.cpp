/**
 * Scattering model classes
 * The classes use the IGOR library found in
 *   sansmodels/src/libigor
 */
#include "models.h"
#include <stdio.h>
using namespace std;

extern "C" {
	#include "libCylinder.h"
	#include "cylinder.h"
}

Cylinder :: Cylinder() {
	parameters.scale      = 1.0;
	parameters.radius     = 10.0;
	parameters.length     = 400.0;
	parameters.contrast   = 1.0;
	parameters.background = 0;
	parameters.cyl_theta  = 0;
	parameters.cyl_phi    = 0;
}

/**
 * Function to evaluate 1D scattering function
 * @param q: q-value
 * @return: function value
 */
double Cylinder :: operator()(double q) {
	return cylinder_analytical_1D(&parameters, q);
}

/**
 * Function to evaluate 2D scattering function
 * @param q_x: value of Q along x
 * @param q_y: value of Q along y
 * @return: function value
 */
double Cylinder :: operator()(double qx, double qy) {
	return cylinder_analytical_2DXY(&parameters, qx, qy);
}

int main(void)
{
	Cylinder c = Cylinder();
	printf("I(Q=%g) = %g\n", 0.001, c(0.001));
	printf("I(Qx=%g, Qy=%g) = %g\n", 0.001, 0.001, c(0.001, 0.001));
	return 0;
}
