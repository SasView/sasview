/**
 * Scattering model for a core-shell sphere
 * @author: Mathieu Doucet / UTK
 */

#include "core_shell.h"
#include "libSphere.h"
#include <math.h>


/**
 * Function to evaluate 1D scattering function
 * @param pars: parameters of the core-shell
 * @param q: q-value
 * @return: function value
 */
double core_shell_analytical_1D(CoreShellParameters *pars, double q) {
	double dp[7];
	
	dp[0] = pars->scale;
	dp[1] = pars->radius;
	dp[2] = pars->thickness;
	dp[3] = pars->core_sld;
	dp[4] = pars->shell_sld;
	dp[5] = pars->solvent_sld;
	dp[6] = pars->background;
	
	return CoreShellForm(dp, q);
}
    
/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the core-shell
 * @param q: q-value
 * @return: function value
 */
double core_shell_analytical_2D(CoreShellParameters *pars, double q, double phi) {
	return core_shell_analytical_1D(pars,q);
}

double core_shell_analytical_2DXY(CoreShellParameters *pars, double qx, double qy){
	return core_shell_analytical_1D(pars,sqrt(qx*qx+qy*qy));	
}
