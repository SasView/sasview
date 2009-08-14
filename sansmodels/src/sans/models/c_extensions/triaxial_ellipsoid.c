/**
 * Scattering model for a cylinder
 * @author: Mathieu Doucet / UTK
 */

#include "triaxial_ellipsoid.h"
#include <math.h>
#include "libCylinder.h"
#include <stdio.h>
#include <stdlib.h>


/**
 * Function to evaluate 1D scattering function
 * @param pars: parameters of the triaxial ellipsoid
 * @param q: q-value
 * @return: function value
 */
double triaxial_ellipsoid_analytical_1D(TriaxialEllipsoidParameters *pars, double q) {
	double dp[6];

	// Fill paramater array
	dp[0] = pars->scale;
	dp[1] = pars->semi_axisA;
	dp[2] = pars->semi_axisB;
	dp[3] = pars->semi_axisC;
	dp[4] = pars->contrast;
	dp[5] = pars->background;

	// Call library function to evaluate model
	return TriaxialEllipsoid(dp, q);
}

double triaxial_ellipsoid_kernel(TriaxialEllipsoidParameters *pars, double q, double alpha, double nu) {
	double t,a,b,c;
	double kernel;
	double pi = acos(-1.0);

	a = pars->semi_axisA ;
	b = pars->semi_axisB ;
	c = pars->semi_axisC ;

	t = q * sqrt(a*a*cos(nu)*cos(nu)+b*b*sin(nu)*sin(nu)*sin(alpha)*sin(alpha)+c*c*cos(alpha)*cos(alpha));
	if (t==0){
		kernel  = 1.0;
	}else{
		kernel  = 3*(sin(t)-t*cos(t))/(t*t*t);
	}
	return kernel*kernel;
}


/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the triaxial ellipsoid
 * @param q: q-value
 * @return: function value
 */
double triaxial_ellipsoid_analytical_2DXY(TriaxialEllipsoidParameters *pars, double qx, double qy) {
	double q;
	q = sqrt(qx*qx+qy*qy);
    return triaxial_ellipsoid_analytical_2D_scaled(pars, q, qx/q, qy/q);
}


/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the triaxial ellipsoid
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double triaxial_ellipsoid_analytical_2D(TriaxialEllipsoidParameters *pars, double q, double phi) {
    return triaxial_ellipsoid_analytical_2D_scaled(pars, q, cos(phi), sin(phi));
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the triaxial ellipsoid
 * @param q: q-value
 * @param q_x: q_x / q
 * @param q_y: q_y / q
 * @return: function value
 */
double triaxial_ellipsoid_analytical_2D_scaled(TriaxialEllipsoidParameters *pars, double q, double q_x, double q_y) {
	double cyl_x, cyl_y, cyl_z, ell_x, ell_y;
	double q_z;
	double cos_nu,nu;
	double alpha, vol, cos_val;
	double answer;
    double pi = acos(-1.0);
    // Cylinder orientation
    cyl_x = sin(pars->axis_theta) * cos(pars->axis_phi);
    cyl_y = sin(pars->axis_theta) * sin(pars->axis_phi);
    cyl_z = cos(pars->axis_theta);

    // q vector
    q_z = 0;

	//dx = 1.0;
	//dy = 1.0;
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
    ell_x =  cos(pars->axis_psi);
    ell_y =  sin(pars->axis_psi);

    // calculate the axis of the ellipse wrt q-coord.
    cos_nu = ell_x*q_x + ell_y*q_y;
    nu = acos(cos_nu);

	// Call the IGOR library function to get the kernel
	answer = triaxial_ellipsoid_kernel(pars, q, alpha, nu);

	// Multiply by contrast^2
	answer *= pars->contrast*pars->contrast;

	//normalize by cylinder volume
	//NOTE that for this (Fournet) definition of the integral, one must MULTIPLY by Vcyl
    vol = 4/3 * pi * pars->semi_axisA * pars->semi_axisB * pars->semi_axisC;
	answer *= vol;

	//convert to [cm-1]
	answer *= 1.0e8;

	//Scale
	answer *= pars->scale;

	// add in the background
	answer += pars->background;

	return answer;
}
