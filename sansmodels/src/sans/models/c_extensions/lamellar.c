/**
 * Scattering model for dilute lamellar model: polydipsersion in thickness (delta) included
 * @author: Gervaise B. Alina / UTK
 */

#include "lamellar.h"
#include <math.h>
#include "libCylinder.h"
#include <stdio.h>
#include <stdlib.h>

/*	LamellarFFX  :  calculates the form factor of a lamellar structure - no S(q) effects included
						-NO polydispersion included
*/
double lamellar_kernel(double dp[], double q){
	double scale,del,sld_bi,sld_sol,contr,bkg;		//local variables of coefficient wave
	double inten, qval,Pq;
	double Pi;


	Pi = 4.0*atan(1.0);
	scale = dp[0];
	del = dp[1];
	sld_bi = dp[2];
	sld_sol = dp[3];
	bkg = dp[4];
	qval = q;
	contr = sld_bi -sld_sol;

	Pq = 2.0*contr*contr/qval/qval*(1.0-cos(qval*del));

	inten = 2.0*Pi*scale*Pq/(qval*qval);		//this is now dimensionless...

	inten /= del;			//normalize by the thickness (in A)

	inten *= 1.0e8;		// 1/A to 1/cm

	return(inten+bkg);
}

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

