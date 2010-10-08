/**
 * Scattering model for a lamellar ParaCrystal
 */

#include "lamellarPC.h"
#include <math.h>
#include "libCylinder.h"
#include <stdio.h>
#include <stdlib.h>


/**
 * Function to evaluate 1D scattering function
 * @param pars: parameters of a lamellar ParaCrystal Model
 * @param q: q-value
 * @return: function value
 */
double lamellarPC_analytical_1D(LamellarPCParameters *pars, double q) {
	double dp[8];

	// Fill paramater array
	dp[0] = pars->scale;
	dp[1] = pars->thickness;
	dp[2] = pars->Nlayers;
	dp[3] = pars->spacing;
	dp[4] = pars->pd_spacing;
	dp[5] = pars->sld_layer;
	dp[6] = pars->sld_solvent;
	dp[7] = pars->background;

	// Call library function to evaluate model
	return Lamellar_ParaCrystal(dp, q);
}

double lamellarPC_analytical_2D(LamellarPCParameters *pars, double q, double phi){
	return lamellarPC_analytical_1D(pars,q);
}
double lamellarPC_analytical_2DXY(LamellarPCParameters *pars, double qx, double qy){
	return lamellarPC_analytical_1D(pars,sqrt(qx*qx+qy*qy));
}
