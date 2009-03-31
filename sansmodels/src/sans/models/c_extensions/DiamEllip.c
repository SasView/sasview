/**
 * SquareWell Structure factor
 * @author: Jae Hie Cho / UTK
 */

#include "DiamEllip.h"
#include "libStructureFactor.h"
#include <math.h>


/**
 * Function to evaluate 1D scattering function
 * @param pars: parameters of the DiaEllip
 * @param q: q-value
 * @return: 2 virial coefficient value
 */
double DiamEllips_analytical_1D(DiamEllipsParameters *pars, double q) {
	double dp[2];

	dp[0] = pars->radius_a;
	dp[1] = pars->radius_b;
	return DiamEllip(dp, q);
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the RadiEllip
 * @param q: q-value
 * @return: function value
 */
double DiamEllips_analytical_2D(DiamEllipsParameters *pars, double q, double phi) {
	return DiamEllips_analytical_1D(pars,q);
}

double DiamEllips_analytical_2DXY(DiamEllipsParameters *pars, double qx, double qy){
	return DiamEllips_analytical_1D(pars,sqrt(qx*qx+qy*qy));
}
