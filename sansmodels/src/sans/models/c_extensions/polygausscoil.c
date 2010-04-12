/**
 * Scattering model for a polygausscoil
 */

#include "polygausscoil.h"
#include "libTwoPhase.h"
#include <math.h>


/**
 * Function to evaluate 1D scattering function
 * @param pars: parameters of the polygausscoil
 * @param q: q-value
 * @return: function value
 */
double polygausscoil_analytical_1D(PolyGaussCoilParameters *pars, double q) {
	double dp[5];

	dp[0] = pars->scale;
	dp[1] = pars->rg;
	dp[2] = pars->poly_m;
	dp[4] = pars->background;

	return PolyGaussCoil(dp, q);
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the sphere
 * @param q: q-value
 * @return: function value
 */
double polygausscoil_analytical_2D(PolyGaussCoilParameters *pars, double q, double phi) {
	return polygausscoil_analytical_1D(pars,q);
}

double polygausscoil_analytical_2DXY(PolyGaussCoilParameters *pars, double qx, double qy){
	return polygausscoil_analytical_1D(pars,sqrt(qx*qx+qy*qy));
}
