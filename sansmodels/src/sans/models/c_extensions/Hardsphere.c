/**
 * Structure factor for a hardsphere
 * @author: Jae Hie Cho / UTK
 */

#include "Hardsphere.h"
#include "libStructureFactor.h"
#include <math.h>
#include <stdio.h>

/**
 * Function to evaluate 1D scattering function
 * @param pars: parameters of the HardsphereStructure
 * @param q: q-value
 * @return: function value
 */
double Hardsphere_analytical_1D(HardsphereParameters *pars, double q) {
	double dp[2];
	if (q == 0){
		return 0.2;
	}
	dp[0] = pars->effect_radius;
	dp[1] = pars->volfraction;
	return HardSphereStruct(dp, q);
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the HardsphereStructure
 * @param q: q-value
 * @return: function value
 */
double Hardsphere_analytical_2D(HardsphereParameters *pars, double q, double phi) {
	return Hardsphere_analytical_1D(pars,q);
}

double Hardsphere_analytical_2DXY(HardsphereParameters *pars, double qx, double qy){
	return Hardsphere_analytical_1D(pars,sqrt(qx*qx+qy*qy));
}
