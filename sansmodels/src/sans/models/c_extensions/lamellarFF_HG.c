/**
 * Scattering model for the form factor from a lyotropic lamellar phase
 * @author: Gervaise B. Alina / UTK
 */

#include "lamellarFF_HG.h"
#include <math.h>
#include "libCylinder.h"
#include <stdio.h>
#include <stdlib.h>


/**
 * Function to evaluate 1D scattering function
 * @param pars: parameters of the form factor from a lyotropic lamellar phase
 * @param q: q-value
 * @return: function value
 */
double lamellarFF_HG_analytical_1D(LamellarFF_HGParameters *pars, double q) {
	double dp[7];
	
	// Fill paramater array
	dp[0] = pars->scale;
	dp[1] = pars->t_length;
	dp[2] = pars->h_thickness;
	dp[3] = pars->sld_tail;
	dp[4] = pars->sld_head;
	dp[5] = pars->sld_solvent;
	dp[6] = pars->background;
	
	// Call library function to evaluate model
	return LamellarFF_HG(dp, q);	
}

double lamellarFF_HG_analytical_2D(LamellarFF_HGParameters *pars, double q, double phi){
	return 1.0;
}
double lamellarFF_HG_analytical_2DXY(LamellarFF_HGParameters *pars, double qx, double qy){
	return 1.0;
}
double lamellarFF_HG_analytical_2D_scaled(LamellarFF_HGParameters *pars, double q, double q_x, double q_y){
	return 1.0;
}

