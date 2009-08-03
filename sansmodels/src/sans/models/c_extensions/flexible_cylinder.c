/**
 * Scattering model for a parallelepiped
 * TODO: Add 2D analysis
 */

#include "flexible_cylinder.h"
#include <math.h>
#include "libCylinder.h"
#include <stdio.h>
#include <stdlib.h>


/**
 * Function to evaluate 1D scattering function
 * @param pars: parameters of the flexible cylinder
 * @param q: q-value
 * @return: function value
 */
double flexible_cylinder_analytical_1D(FlexibleCylinderParameters *pars, double q) {
	double dp[6];

	// Fill paramater array
	dp[0] = pars->scale;
	dp[1] = pars->length;
	dp[2] = pars->kuhn_length;
	dp[3] = pars->radius;
	dp[4] = pars->contrast;
	dp[5] = pars->background;

	// Call library function to evaluate model
	return FlexExclVolCyl(dp, q);
}
/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the flexible cylinder
 * @param q: q-value
 * @return: function value
 */
double flexible_cylinder_analytical_2DXY(FlexibleCylinderParameters *pars, double qx, double qy) {
	double q;
	q = sqrt(qx*qx+qy*qy);
    return flexible_cylinder_analytical_1D(pars, q);
}


/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the flexible cylinder
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double flexible_cylinder_analytical_2D(FlexibleCylinderParameters *pars, double q, double phi) {
    return flexible_cylinder_analytical_1D(pars, q);
}


