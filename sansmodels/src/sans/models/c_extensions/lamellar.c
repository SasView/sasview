/**
 * Scattering model for dilute lamellar model: polydipsersion in thickness (delta) included
 * @author: Gervaise B. Alina / UTK
 */

#include "lamellar.h"
#include <math.h>
#include "libCylinder.h"
#include <stdio.h>
#include <stdlib.h>


/**
 * Function to evaluate 1D scattering function
 * @param pars: parameters of the lamellar
 * @param q: q-value
 * @return: function value
 */
double lamellar_analytical_1D(LamellarParameters *pars, double q) {
	double dp[5];

	// Fill paramater array
	dp[0] = pars->scale;
	dp[1] = pars->bi_thick;
	dp[2] = pars->sld_bi;
	dp[3] = pars->sld_sol;
	dp[4] = pars->background;


	// Call library function to evaluate model
	return lamellar_kernel(dp, q);
}


/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the lamellar
 * @param q: q-value
 * @return: function value
 */


double lamellar_analytical_2D(LamellarParameters *pars, double q, double phi){
	return lamellar_analytical_1D(pars,q);
}
double lamellar_analytical_2DXY(LamellarParameters *pars, double qx, double qy){
	return lamellar_analytical_1D(pars,sqrt(qx*qx+qy*qy));
}

