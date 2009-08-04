/**
 * Scattering model for a prolate
 * @author: Gervaise B Alina/ UTK
 */

#include "prolate.h"
#include <math.h>
#include "libCylinder.h"
#include <stdio.h>
#include <stdlib.h>


/**
 * Function to evaluate 1D scattering function
 * @param pars: parameters of the prolate
 * @param q: q-value
 * @return: function value
 */
double prolate_analytical_1D(ProlateParameters *pars, double q) {
	double dp[8];

	// Fill paramater array
	dp[0] = pars->scale;
	dp[1] = pars->major_core;
	dp[2] = pars->minor_core;
	dp[3] = pars->major_shell;
	dp[4] = pars->minor_shell;
	dp[5] = pars->contrast;
	dp[6] = pars->sld_solvent;
	dp[7] = pars->background;

	// Call library function to evaluate model
	return ProlateForm(dp, q);
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the prolate
 * @param q: q-value
 * @return: function value
 */
double prolate_analytical_2DXY(ProlateParameters *pars, double qx, double qy) {
	double q;
	q = sqrt(qx*qx+qy*qy);
    return prolate_analytical_1D(pars, q);
}


/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the prolate
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double prolate_analytical_2D(ProlateParameters *pars, double q, double phi) {
    return prolate_analytical_1D(pars, q);
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the prolate
 * @param q: q-value
 * @param q_x: q_x / q
 * @param q_y: q_y / q
 * @return: function value
 */
//double prolate_analytical_2D_scaled(ProlateParameters *pars, double q, double q_x, double q_y) {
//
//	return 1.0;
//}

