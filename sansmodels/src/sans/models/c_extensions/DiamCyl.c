/**
 * SquareWell Structure factor
 * @author: Jae Hie Cho / UTK
 */

#include "DiamCyl.h"
#include "libStructureFactor.h"
#include <math.h>


/**
 * Function to evaluate 1D scattering function
 * @param pars: parameters of the DiaEllip
 * @param q: q-value ; NOT used
 * @return: 2 virial coefficient value
 */
double DiamCyld_analytical_1D(DiamCyldParameters *pars, double q) {
	double dp[2];

	dp[0] = pars->radius;
	dp[1] = pars->length;
	return DiamCyl(dp, q);
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the RadiEllip
 * @param q: q-value
 * @return: function value
 */
double DiamCyld_analytical_2D(DiamCyldParameters *pars, double q, double phi) {
	return DiamCyld_analytical_1D(pars,q);
}

double DiamCyld_analytical_2DXY(DiamCyldParameters *pars, double qx, double qy){
	return DiamCyld_analytical_1D(pars,sqrt(qx*qx+qy*qy));
}
