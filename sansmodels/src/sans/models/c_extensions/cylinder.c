/**
 * Scattering model for a cylinder
 * @author: Mathieu Doucet / UTK
 */

#include "cylinder.h"
#include <math.h>
#include "libCylinder.h"
#include <stdio.h>
#include <stdlib.h>


/**
 * Function to evaluate 1D scattering function
 * @param pars: parameters of the cylinder
 * @param q: q-value
 * @return: function value
 */
double cylinder_analytical_1D(CylinderParameters *pars, double q) {
	double dp[6];

	// Fill paramater array
	dp[0] = pars->scale;
	dp[1] = pars->radius;
	dp[2] = pars->length;
	dp[3] = pars->sldCyl;
	dp[4] = pars->sldSolv;
	dp[5] = pars->background;

	// Call library function to evaluate model
	return CylinderForm(dp, q);
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the cylinder
 * @param q: q-value
 * @return: function value
 */
double cylinder_analytical_2DXY(CylinderParameters *pars, double qx, double qy) {
	double q;
	q = sqrt(qx*qx+qy*qy);
    return cylinder_analytical_2D_scaled(pars, q, qx/q, qy/q);
}


/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the cylinder
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double cylinder_analytical_2D(CylinderParameters *pars, double q, double phi) {
    return cylinder_analytical_2D_scaled(pars, q, cos(phi), sin(phi));
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the cylinder
 * @param q: q-value
 * @param q_x: q_x / q
 * @param q_y: q_y / q
 * @return: function value
 */
double cylinder_analytical_2D_scaled(CylinderParameters *pars, double q, double q_x, double q_y) {
	double cyl_x, cyl_y, cyl_z;
	double q_z;
	double alpha, vol, cos_val;
	double answer;
	//convert angle degree to radian
	double pi = 4.0*atan(1.0);
	double theta = pars->cyl_theta * pi/180.0;
	double phi = pars->cyl_phi * pi/180.0;

    // Cylinder orientation
    cyl_x = sin(theta) * cos(phi);
    cyl_y = sin(theta) * sin(phi);
    cyl_z = cos(theta);

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
	answer = CylKernel(q, pars->radius, pars->length/2.0, alpha) / sin(alpha);

	// Multiply by contrast^2
	answer *= (pars->sldCyl - pars->sldSolv)*(pars->sldCyl - pars->sldSolv);

	//normalize by cylinder volume
	//NOTE that for this (Fournet) definition of the integral, one must MULTIPLY by Vcyl
    vol = acos(-1.0) * pars->radius * pars->radius * pars->length;
	answer *= vol;

	//convert to [cm-1]
	answer *= 1.0e8;

	//Scale
	answer *= pars->scale;

	// add in the background
	answer += pars->background;

	return answer;
}

