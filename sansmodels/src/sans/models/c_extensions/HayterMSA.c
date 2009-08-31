/**
 * SquareWell Structure factor
 * @author: Jae Hie Cho / UTK
 */

#include "HayterMSA.h"
#include "libStructureFactor.h"
#include <math.h>


/**
 * Function to evaluate 1D scattering function
 * @param pars: parameters of the HayterPenfoldMSA
 * @param q: q-value
 * @return: function value
 */
double HayterMSA_analytical_1D(HayterMSAParameters *pars, double q) {
	double dp[6];

	dp[0] = pars->effect_radius;
	dp[1] = pars->charge;
	dp[1] = pars->volfraction;
	dp[3] = pars->temperature;
	dp[4] = pars->saltconc;
	dp[5] = pars->dielectconst;

	return HayterPenfoldMSA(dp, q);
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the HayterPenfoldMSA
 * @param q: q-value
 * @return: function value
 */
double HayterMSA_analytical_2D(HayterMSAParameters *pars, double q, double phi) {
	return HayterMSA_analytical_1D(pars,q);
}

double HayterMSA_analytical_2DXY(HayterMSAParameters *pars, double qx, double qy){
	return HayterMSA_analytical_1D(pars,sqrt(qx*qx+qy*qy));
}
