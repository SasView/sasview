/**
 * Fractal scattering model
 */

#include "fractal.h"
#include "libTwoPhase.h"
#include <math.h>


/**
 * Function to evaluate 1D scattering function
 * @param pars: parameters of the fractal
 * @param q: q-value
 * @return: function value
 */
double fractal_analytical_1D(FractalParameters *pars, double q) {
	double dp[7];

	dp[0] = pars->scale;
	dp[1] = pars->radius;
	dp[2] = pars->fractal_dim;
	dp[3] = pars->cor_length;
	dp[4] = pars->sldBlock;
	dp[5] = pars->sldSolv;
	dp[6] = pars->background;

	return Fractal(dp, fabs(q));
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the fractal
 * @param q: q-value
 * @return: function value
 */
double fractal_analytical_2D(FractalParameters *pars, double q, double phi) {
	return fractal_analytical_1D(pars,q);
}

double fractal_analytical_2DXY(FractalParameters *pars, double qx, double qy){
	return fractal_analytical_1D(pars,sqrt(qx*qx+qy*qy));
}
