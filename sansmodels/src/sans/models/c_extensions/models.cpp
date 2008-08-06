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
}

Cylinder :: Cylinder() {
	scale = 1.0;
	radius = 10.0;
	length = 400.0;
	contrast = 1.0;
	background = 0;
}

double Cylinder :: operator()(double q) {
	double dp[5];
	// Fill paramater array
	dp[0] = scale;
	dp[1] = radius;
	dp[2] = length;
	dp[3] = contrast;
	dp[4] = background;

	// Call library function to evaluate model
	return CylinderForm(dp, q);
}

int main(void)
{
	Cylinder c = Cylinder();
	printf("I(Q=%g) = %g\n", 0.001, c(0.001));
	return 0;
}
