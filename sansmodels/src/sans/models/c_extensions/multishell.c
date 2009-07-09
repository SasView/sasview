/**
 * Scattering model for a sphere
 * @author: Gervaise B alina / UTK
 */

#include "multishell.h"
#include "libSphere.h"
#include <math.h>


/**
 * Function to evaluate 1D scattering function
 * @param pars: parameters of the multishell
 * @param q: q-value
 * @return: function value
 */
double multishell_analytical_1D(MultiShellParameters *pars, double q) {
	double dp[8];
	
	dp[0] = pars->scale;
	dp[1] = pars->core_radius;
	dp[2] = pars->s_thickness;
	dp[3] = pars->w_thickness;
	dp[4] = pars->core_sld;
	dp[5] = pars->shell_sld;
	dp[6] = pars->n_pairs;
	dp[7] = pars->background;
	
	return MultiShell(dp, q);
}
    
/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the multishell
 * @param q: q-value
 * @return: function value
 */
double multishell_analytical_2D(MultiShellParameters *pars, double q, double phi) {
	return multishell_analytical_1D(pars,q);
}

double multishell_analytical_2DXY(MultiShellParameters *pars, double qx, double qy){
	return multishell_analytical_1D(pars,sqrt(qx*qx+qy*qy));	
}
