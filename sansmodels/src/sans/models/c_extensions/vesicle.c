/**
 * Scattering model for a sphere
 * @author: Gervaise B alina / UTK
 */

#include "vesicle.h"
#include "libSphere.h"
#include <math.h>


/**
 * Function to evaluate 1D scattering function
 * @param pars: parameters of the vesicle
 * @param q: q-value
 * @return: function value
 */
double vesicle_analytical_1D(VesicleParameters *pars, double q) {
	double dp[6];

	dp[0] = pars->scale;
	dp[1] = pars->radius;
	dp[2] = pars->thickness;
	dp[3] = pars->core_sld;
	dp[4] = pars->shell_sld;
	dp[5] = pars->background;


	return VesicleForm(dp, q);
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the vesicle
 * @param q: q-value
 * @return: function value
 */
double vesicle_analytical_2D(VesicleParameters *pars, double q, double phi) {
	return vesicle_analytical_1D(pars,q);
}

double vesicle_analytical_2DXY(VesicleParameters *pars, double qx, double qy){
	return vesicle_analytical_1D(pars,sqrt(qx*qx+qy*qy));
}
