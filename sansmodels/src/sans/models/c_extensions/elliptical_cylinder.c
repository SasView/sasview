/**
 * Scattering model for a cylinder with elliptical cross-section
 */

#include "elliptical_cylinder.h"
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
double elliptical_cylinder_analytical_1D(EllipticalCylinderParameters *pars, double q) {
	double dp[6];

	// Fill paramater array
	dp[0] = pars->scale;
	dp[1] = pars->r_minor;
	dp[2] = pars->r_ratio;
	dp[3] = pars->length;
	dp[4] = pars->contrast;
	dp[5] = pars->background;

	// Call library function to evaluate model
	return EllipCyl20(dp, q);
}

double elliptical_cylinder_kernel(EllipticalCylinderParameters *pars, double q, double alpha, double nu) {
	double qr;
	double qL;
	double Be,Si;
	double r_major;
	double kernel;

	r_major = pars->r_ratio * pars->r_minor;

	qr = q*sin(alpha)*sqrt( r_major*r_major*sin(nu)*sin(nu) + pars->r_minor*pars->r_minor*cos(nu)*cos(nu) );
	qL = q*pars->length*cos(alpha)/2.0;

	if (qr==0){
		Be = 0.5;
	}else{
		Be = NR_BessJ1(qr)/qr;
	}
	if (qL==0){
		Si = 1.0;
	}else{
		Si = sin(qL)/qL;
	}


	kernel = 2.0*Be * Si;
	return kernel*kernel;
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the cylinder
 * @param q: q-value
 * @return: function value
 */
double elliptical_cylinder_analytical_2DXY(EllipticalCylinderParameters *pars, double qx, double qy) {
	double q;
	q = sqrt(qx*qx+qy*qy);
    return elliptical_cylinder_analytical_2D_scaled(pars, q, qx/q, qy/q);
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the cylinder
 * @param q: q-value
 * @param theta: angle theta = angle wrt z axis
 * @param phi: angle phi = angle around y axis (starting from the x+-direction as phi = 0)
 * @return: function value
 */
double elliptical_cylinder_analytical_2D(EllipticalCylinderParameters *pars, double q, double phi) {
    return elliptical_cylinder_analytical_2D_scaled(pars, q, cos(phi), sin(phi));
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the cylinder
 * @param q: q-value
 * @param q_x: q_x / q
 * @param q_y: q_y / q
 * @return: function value
 */
double elliptical_cylinder_analytical_2D_scaled(EllipticalCylinderParameters *pars, double q, double q_x, double q_y) {
	double cyl_x, cyl_y, cyl_z;
	double ell_x, ell_y;
	double q_z;
	double alpha, vol, cos_val;
	double nu, cos_nu;
	double answer;

    //Cylinder orientation
    cyl_x = sin(pars->cyl_theta) * cos(pars->cyl_phi);
    cyl_y = sin(pars->cyl_theta) * sin(pars->cyl_phi);
    cyl_z = cos(pars->cyl_theta);

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

    //ellipse orientation:
	// the elliptical corss section was transformed and projected
	// into the detector plane already through sin(alpha)and furthermore psi remains as same
	// on the detector plane.
	// So, all we need is to calculate the angle (nu) of the minor axis of the ellipse wrt
	// the wave vector q.

	//x- y- component on the detector plane.
    ell_x =  cos(pars->cyl_psi);
    ell_y =  sin(pars->cyl_psi);

    // calculate the axis of the ellipse wrt q-coord.
    cos_nu = ell_x*q_x + ell_y*q_y;
    nu = acos(cos_nu);

    // The following test should always pass
    if (fabs(cos_nu)>1.0) {
    	printf("cyl_ana_2D: Unexpected error: cos(nu)>1\n");
     	return 0;
    }

	answer = elliptical_cylinder_kernel(pars, q, alpha,nu);

	// Multiply by contrast^2
	answer *= pars->contrast*pars->contrast;

	//normalize by cylinder volume
	//NOTE that for this (Fournet) definition of the integral, one must MULTIPLY by Vcyl
    vol = acos(-1.0) * pars->r_minor * pars->r_minor * pars->r_ratio * pars->length;
	answer *= vol;

	//convert to [cm-1]
	answer *= 1.0e8;

	//Scale
	answer *= pars->scale;

	// add in the background
	answer += pars->background;

	return answer;
}

