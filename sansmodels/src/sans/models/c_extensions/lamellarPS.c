/**
 * Scattering model for a lamellar
 * TODO: Add 2D analysis
 */

#include "lamellarPS.h"
#include <math.h>
#include "libCylinder.h"
#include <stdio.h>
#include <stdlib.h>

/*LamellarPS_kernel() was moved from libigor to get rid of polydipersity in del(thickness) that we provide from control panel.
/*	LamellarPSX  :  calculates the form factor of a lamellar structure - with S(q) effects included
-------
------- resolution effects ARE NOT included, but only a CONSTANT default value, not the real q-dependent resolution!!

	*/
double
LamellarPS_kernel(double dp[], double q)
{
	double scale,dd,del,sld_bi,sld_sol,contr,NN,Cp,bkg;		//local variables of coefficient wave
	double inten, qval,Pq,Sq,alpha,temp,t1,t2,t3,dQ;
	double Pi,Euler,dQDefault,fii;
	int ii,NNint;
	Euler = 0.5772156649;		// Euler's constant
	dQDefault = 0.0;		//[=] 1/A, q-resolution, default value
	dQ = dQDefault;

	Pi = 4.0*atan(1.0);
	qval = q;

	scale = dp[0];
	dd = dp[1];
	del = dp[2];
	sld_bi = dp[3];
	sld_sol = dp[4];
	NN = trunc(dp[5]);		//be sure that NN is an integer
	Cp = dp[6];
	bkg = dp[7];

	contr = sld_bi - sld_sol;

	Pq = 2.0*contr*contr/qval/qval*(1.0-cos(qval*del));

	NNint = (int)NN;		//cast to an integer for the loop
	ii=0;
	Sq = 0.0;
	for(ii=1;ii<(NNint-1);ii+=1) {

		fii = (double)ii;		//do I really need to do this?

		temp = 0.0;
		alpha = Cp/4.0/Pi/Pi*(log(Pi*ii) + Euler);
		t1 = 2.0*dQ*dQ*dd*dd*alpha;
		t2 = 2.0*qval*qval*dd*dd*alpha;
		t3 = dQ*dQ*dd*dd*ii*ii;

		temp = 1.0-ii/NN;
		temp *= cos(dd*qval*ii/(1.0+t1));
		temp *= exp(-1.0*(t2 + t3)/(2.0*(1.0+t1)) );
		temp /= sqrt(1.0+t1);

		Sq += temp;
	}

	Sq *= 2.0;
	Sq += 1.0;

	inten = 2.0*Pi*scale*Pq*Sq/(dd*qval*qval);

	inten *= 1.0e8;		// 1/A to 1/cm

    return(inten+bkg);
}

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
	dp[3] = pars->sld_bi;
	dp[4] = pars->sld_sol;
	dp[5] = pars->n_plates;
	dp[6] = pars->caille;
	dp[7] = pars->background;

	// Call library function to evaluate model
	return LamellarPS_kernel(dp, q);
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
    return lamellarPS_analytical_1D(pars, q);
}


/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the lamellar
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double lamellarPS_analytical_2D(LamellarPSParameters *pars, double q, double phi) {
    return lamellarPS_analytical_1D(pars,q);
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the lamellar
 * @param q: q-value
 * @param q_x: q_x / q
 * @param q_y: q_y / q
 * @return: function value
 */


