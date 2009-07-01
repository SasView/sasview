/**
 * Scattering model for lamellar
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
	dp[1] = pars->delta;
	dp[2] = pars->sigma;
	dp[3] = pars->contrast;
	dp[4] = pars->background;
	
	
	// Call library function to evaluate model
	return LamellarFF(dp, q);	
}

double lamellar_analytical_2D(LamellarParameters *pars, double q, double phi){
	return 1.0;
}
double lamellar_analytical_2DXY(LamellarParameters *pars, double qx, double qy){
	return 1.0;
}
double lamellar_analytical_2D_scaled(LamellarParameters *pars, double q, double q_x, double q_y){
	return 1.0;
}

