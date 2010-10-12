/**
 * Scattering model for a corefourshell sphere
 */

#include "corefourshell.h"
#include "libSphere.h"
#include <math.h>


/**
 * Function to evaluate 1D scattering function
 * @param pars: parameters of the corefourshell
 * @param q: q-value
 * @return: function value
 */
double corefourshell_analytical_1D(CoreFourShellParameters *pars, double q) {
	double dp[13];

	dp[0] = pars->scale;
	dp[1] = pars->rad_core0;
	dp[2] = pars->sld_core0;
	dp[3] = pars->thick_shell1;
	dp[4] = pars->sld_shell1;
	dp[5] = pars->thick_shell2;
	dp[6] = pars->sld_shell2;
	dp[7] = pars->thick_shell3;
	dp[8] = pars->sld_shell3;
	dp[9] = pars->thick_shell4;
	dp[10] = pars->sld_shell4;
	dp[11] = pars->sld_solv;
	dp[12] = pars->background;

	return FourShell(dp, q);
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the corefourshell
 * @param q: q-value
 * @return: function value
 */
double corefourshell_analytical_2D(CoreFourShellParameters *pars, double q, double phi) {
	return corefourshell_analytical_1D(pars,q);
}

double corefourshell_analytical_2DXY(CoreFourShellParameters *pars, double qx, double qy){
	return corefourshell_analytical_1D(pars,sqrt(qx*qx+qy*qy));
}
