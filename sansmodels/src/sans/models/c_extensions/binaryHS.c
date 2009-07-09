/**
 * Scattering model for a sphere
 * @author: Gervaise B alina / UTK
 */

#include "binaryHS.h"
#include "libSphere.h"
#include <math.h>


/**
 * Function to evaluate 1D scattering function
 * @param pars: parameters of the binary hard sphere
 * @param q: q-value
 * @return: function value
 */
double binaryHS_analytical_1D(BinaryHSParameters *pars, double q) {
	double dp[8];
	
	dp[0] = pars->l_radius;
	dp[1] = pars->s_radius;
	dp[2] = pars->vol_frac_ls;
	dp[3] = pars->vol_frac_ss;
	dp[4] = pars->ls_sld;
	dp[5] = pars->ss_sld;
	dp[6] = pars->solvent_sld;
	dp[7] = pars->background;
	
	return BinaryHS(dp, q);
}
    
/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the binary hard sphere
 * @param q: q-value
 * @return: function value
 */
double binaryHS_analytical_2D(BinaryHSParameters *pars, double q, double phi) {
	return binaryHS_analytical_1D(pars,q);
}

double binaryHS_analytical_2DXY(BinaryHSParameters *pars, double qx, double qy){
	return binaryHS_analytical_1D(pars,sqrt(qx*qx+qy*qy));	
}
