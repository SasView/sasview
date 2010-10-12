/*
 * Scattering model for a Capped Cylinder
 */
#include "capcyl.h"
#include <math.h>
#include "GaussWeights.h"
#include "libCylinder.h"

/**
 * Function to evaluate 1D scattering function
 * @param pars: parameters of the CappedCylinder
 * @param q: q-value
 * @return: function value
 */
double capcyl_analytical_1D(CapCylParameters *pars, double q) {
	double dp[7];
	double result;

	dp[0] = pars->scale;
	dp[1] = pars->rad_cyl;
	dp[2] = pars->len_cyl;
	dp[3] = pars->rad_cap;
	dp[4] = pars->sld_capcyl;
	dp[5] = pars->sld_solv;
	dp[6] = pars->background;

	result = CappedCylinder(dp, q);
	// Make Sure it never goes to inf/nan.
	if ( result == INFINITY || result == NAN){
		result = pars->background;
	}
	return result;
}


double capcyl2d_kernel(double dp[], double q, double alpha) {
	int i,j;
	double Pi;
	double scale,contr,bkg,sldc,slds;
	double len,rad,hDist,endRad;
	int nordj=76;
	double zi=alpha,yyy,answer;			//running tally of integration
	double summj,vaj,vbj,zij;			//for the inner integration
	double arg1,arg2,inner,be;


	scale = dp[0];
	rad = dp[1];
	len = dp[2];
	endRad = dp[3];
	sldc = dp[4];
	slds = dp[5];
	bkg = dp[6];

	hDist = -1.0*sqrt(fabs(endRad*endRad-rad*rad));		//by definition for this model

	contr = sldc-slds;

	Pi = 4.0*atan(1.0);
	vaj = -1.0*hDist/endRad;
	vbj = 1.0;		//endpoints of inner integral

	summj=0.0;

	for(j=0;j<nordj;j++) {
		//20 gauss points for the inner integral
		zij = ( Gauss76Z[j]*(vbj-vaj) + vaj + vbj )/2.0;		//the "t" dummy
		yyy = Gauss76Wt[j] * ConvLens_kernel(dp,q,zij,zi);		//uses the same Kernel as the Dumbbell, here L>0
		summj += yyy;
	}
	//now calculate the value of the inner integral
	inner = (vbj-vaj)/2.0*summj;
	inner *= 4.0*Pi*endRad*endRad*endRad;

	//now calculate outer integrand
	arg1 = q*len/2.0*cos(zi);
	arg2 = q*rad*sin(zi);
	yyy = inner;

	if(arg2 == 0) {
		be = 0.5;
	} else {
		be = NR_BessJ1(arg2)/arg2;
	}

	if(arg1 == 0.0) {		//limiting value of sinc(0) is 1; sinc is not defined in math.h
		yyy += Pi*rad*rad*len*2.0*be;
	} else {
		yyy += Pi*rad*rad*len*sin(arg1)/arg1*2.0*be;
	}
	yyy *= yyy;   //sin(zi);
	answer = yyy;


	answer /= Pi*rad*rad*len + 2.0*Pi*(2.0*endRad*endRad*endRad/3.0+endRad*endRad*hDist-hDist*hDist*hDist/3.0);		//divide by volume
	answer *= 1.0e8;		//convert to cm^-1
	answer *= contr*contr;
	answer *= scale;
	answer += bkg;

	return answer;
}


/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the BarBell
 * @param q: q-value
 * @return: function value
 */
double capcyl_analytical_2DXY(CapCylParameters *pars, double qx, double qy){
	double q;
	q = sqrt(qx*qx+qy*qy);
	return capcyl_analytical_2D_scaled(pars, q, qx/q, qy/q);
}

double capcyl_analytical_2D(CapCylParameters *pars, double q, double phi) {
	return capcyl_analytical_2D_scaled(pars, q, cos(phi), sin(phi));
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the BarBell
 * @param q: q-value
 * @param q_x: q_x / q
 * @param q_y: q_y / q
 * @return: function value
 */
double capcyl_analytical_2D_scaled(CapCylParameters *pars, double q, double q_x, double q_y) {
	double cyl_x, cyl_y, cyl_z;
	double q_z;
	double alpha, vol, cos_val;
	double answer;
	double dp[7];

	dp[0] = pars->scale;
	dp[1] = pars->rad_cyl;
	dp[2] = pars->len_cyl;
	dp[3] = pars->rad_cap;
	dp[4] = pars->sld_capcyl;
	dp[5] = pars->sld_solv;
	dp[6] = pars->background;


	//double Pi = 4.0*atan(1.0);
    // Cylinder orientation
    cyl_x = sin(pars->theta) * cos(pars->phi);
    cyl_y = sin(pars->theta) * sin(pars->phi);
    cyl_z = cos(pars->theta);

    // q vector
    q_z = 0;

    // Compute the angle btw vector q and the
    // axis of the cylinder
    cos_val = cyl_x*q_x + cyl_y*q_y + cyl_z*q_z;

    // The following test should always pass
    if (fabs(cos_val)>1.0) {
    	printf("cyl_ana_2D: Unexpected error: cos(alpha)>1\n");
     	return 0;
    }

    // Note: cos(alpha) = 0 and 1 will get an
    // undefined value from CylKernel
	alpha = acos( cos_val );

	// Call the IGOR library function to get the kernel
	answer = capcyl2d_kernel(dp, q, alpha)/sin(alpha);


	return answer;

}
