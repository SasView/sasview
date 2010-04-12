/**
 * Scattering model for a flexible cylinder with an elliptical cross section
 */
#include "flexcyl_ellipX.h"
#include <math.h>
#include "libCylinder.h"

/**
 * Function to evaluate 1D scattering function
 * @param pars: parameters of the flexible cylinder with an elliptical X
 * @param q: q-value
 * @return: function value
 */
double flexcyl_ellipX_analytical_1D(FlexCylEXParameters *pars, double q) {
	double dp[8];

	dp[0] = pars->scale;
	dp[1] = pars->length;
	dp[2] = pars->kuhn_length;
	dp[3] = pars->radius;
	dp[4] = pars->axis_ratio;
	dp[5] = pars->sldCyl;
	dp[6] = pars->sldSolv;
	dp[7] = pars->background;

	return FlexCyl_Ellip(dp, q);
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the flexible cylinder with an elliptical X
 * @param q: q-value
 * @return: function value
 */
double flexcyl_ellipX_analytical_2D(FlexCylEXParameters *pars, double q, double phi) {
	return flexcyl_ellipX_analytical_1D(pars,q);
}

double flexcyl_ellipX_analytical_2DXY(FlexCylEXParameters *pars, double qx, double qy){
	return flexcyl_ellipX_analytical_1D(pars,sqrt(qx*qx+qy*qy));
}
