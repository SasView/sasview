/**
 * Structure factor for a hardsphere
 * @author: Jae Hie Cho / UTK
 */

#include "StickyHS.h"
#include "libStructureFactor.h"
#include <math.h>


/**
 * Function to evaluate 1D scattering function
 * @param pars: parameters of the StickyHS_struct
 * @param q: q-value
 * @return: function value
 */
double StickyHS_analytical_1D(StickyHSParameters *pars, double q) {
	double dp[4];
	
	dp[0] = pars->radius;
	dp[1] = pars->volfraction;	
	dp[2] = pars->perturb;
	dp[3] = pars->stickiness;	
	return StickyHS_Struct(dp, q);
}
    
/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the StickyHS_struct
 * @param q: q-value
 * @return: function value
 */
double StickyHS_analytical_2D(StickyHSParameters *pars, double q, double phi) {
	return StickyHS_analytical_1D(pars,q);
}

double StickyHS_analytical_2DXY(StickyHSParameters *pars, double qx, double qy){
	return StickyHS_analytical_1D(pars,sqrt(qx*qx+qy*qy));	
}
