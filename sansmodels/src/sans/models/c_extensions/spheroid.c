/**
 * Scattering model for a prolate
 * @author: UTK
 */

#include "spheroid.h"
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
double spheroid_analytical_1D(SpheroidParameters *pars, double q) {
	double dp[8];

	// Fill paramater array
	dp[0] = pars->scale;
	dp[1] = pars->equat_core;
	dp[2] = pars->polar_core;
	dp[3] = pars->equat_shell;
	dp[4] = pars->polar_shell;
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
double spheroid_analytical_2DXY(SpheroidParameters *pars, double qx, double qy) {
	double q;
	q = sqrt(qx*qx+qy*qy);
    return spheroid_analytical_2D_scaled(pars, q, qx/q, qy/q);
}


/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the prolate
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double spheroid_analytical_2D(SpheroidParameters *pars, double q, double phi) {
    return spheroid_analytical_2D_scaled(pars, q, cos(phi), sin(phi));
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the prolate
 * @param q: q-value
 * @param q_x: q_x / q
 * @param q_y: q_y / q
 * @return: function value
 */
double spheroid_analytical_2D_scaled(SpheroidParameters *pars, double q, double q_x, double q_y) {

	double cyl_x, cyl_y, cyl_z;
	double q_z;
	double alpha, vol, cos_val;
	double answer;
	double Pi = 4.0*atan(1.0);

    // ellipsoid orientation, the axis of the rotation is consistent with the ploar axis.
    cyl_x = sin(pars->axis_theta) * cos(pars->axis_phi);
    cyl_y = sin(pars->axis_theta) * sin(pars->axis_phi);
    cyl_z = cos(pars->axis_theta);

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
	answer = gfn4(cos_val,pars->equat_core,pars->polar_core,pars->equat_shell,pars->polar_shell,pars->contrast,pars->sld_solvent,q);


	//normalize by cylinder volume
	//NOTE that for this (Fournet) definition of the integral, one must MULTIPLY by Vcyl
    vol = 4*Pi/3*pars->equat_shell*pars->equat_shell*pars->polar_shell;
	answer /= vol;

	//convert to [cm-1]
	answer *= 1.0e8;

	//Scale
	answer *= pars->scale;

	// add in the background
	answer += pars->background;

	return answer;
}


