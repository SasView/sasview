/**
 * Scattering model for a lamellar
 * TODO: Add 2D analysis
 */

#include "lamellarPS.h"
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
double lamellarPS_analytical_1D(LamellarPSParameters *pars, double q) {
	double dp[8];
	
	// Fill paramater array
	dp[0] = pars->scale;
	dp[1] = pars->spacing;
	dp[2] = pars->delta;
	dp[3] = pars->sigma;
	dp[4] = pars->contrast;
	dp[5] = pars->n_plates;
	dp[6] = pars->caille;
	dp[7] = pars->background;

	// Call library function to evaluate model
	return LamellarPS(dp, q);	
}
/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the lamellar
 * @param q: q-value
 * @return: function value
 */
double lamellarPS_analytical_2DXY(LamellarPSParameters *pars, double qx, double qy) {
	double q;
	q = sqrt(qx*qx+qy*qy);
    return lamellarPS_analytical_2D_scaled(pars, q, qx/q, qy/q);
} 


/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the lamellar
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double lamellarPS_analytical_2D(LamellarPSParameters *pars, double q, double phi) {
    return lamellarPS_analytical_2D_scaled(pars, q, cos(phi), sin(phi));
} 
        
/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the lamellar
 * @param q: q-value
 * @param q_x: q_x / q
 * @param q_y: q_y / q
 * @return: function value
 */
double lamellarPS_analytical_2D_scaled(LamellarPSParameters *pars, double q, double q_x, double q_y) {
	
	return 1.0;
}
    

