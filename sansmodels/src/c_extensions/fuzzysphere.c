/**
 * Scattering model for a fuzzy sphere
 */

#include <math.h>
#include "libSphere.h"
#include "fuzzysphere.h"
#include <stdio.h>
#include <stdlib.h>

// scattering from a uniform sphere w/ fuzzy surface
// Modified from FuzzySpheres in libigor/libSphere.c without polydispersion: JHC
double fuzzysphere_kernel(double dp[], double q){
	double pi,x,xr;
	double radius,sldSph,sldSolv,scale,bkg,delrho,fuzziness,f2,bes,vol,f;		//my local names

	pi = 4.0*atan(1.0);
	x= q;
	scale = dp[0];
	radius = dp[1];
	fuzziness = dp[2];
	sldSph = dp[3];
	sldSolv = dp[4];
	bkg = dp[5];
	delrho=sldSph-sldSolv;

	xr = x*radius;
	//handle xr==0 separately
	if(xr == 0.0){
		bes = 1.0;
	}else{
		bes = 3.0*(sin(xr)-xr*cos(xr))/(xr*xr*xr);
	}
	vol = 4.0*pi/3.0*radius*radius*radius;
	f = vol*bes*delrho;		// [=] A
	f *= exp(-0.5*fuzziness*fuzziness*x*x);
	// normalize to single particle volume, convert to 1/cm
	f2 = f * f / vol * 1.0e8;		// [=] 1/cm

	f2 *= scale;
	f2 += bkg;

    return(f2);	//scale, and add in the background
}


/**
 * Function to evaluate 1D scattering function
 * @param pars: parameters of the fuzzysphere
 * @param q: q-value
 * @return: function value
 */
double fuzzysphere_analytical_1D(FuzzySphereParameters *pars, double q) {
	double dp[6];

	dp[0] = pars->scale;
	dp[1] = pars->radius;
	dp[2] = pars->fuzziness;
	dp[3] = pars->sldSph;
	dp[4] = pars->sldSolv;
	dp[5] = pars->background;

	return fuzzysphere_kernel(dp, q);
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the fuzzysphere
 * @param q: q-value
 * @return: function value
 */
double fuzzysphere_analytical_2D(FuzzySphereParameters *pars, double q, double phi) {
	return fuzzysphere_analytical_1D(pars,q);
}

double sphere_analytical_2DXY(FuzzySphereParameters *pars, double qx, double qy){
	return fuzzysphere_analytical_1D(pars,sqrt(qx*qx+qy*qy));
}
