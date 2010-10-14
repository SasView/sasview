/**
 * Scattering model for an ellipsoid
 * @author: Mathieu Doucet / UTK
 */

#include "ellipsoid.h"
#include "libCylinder.h"
#include <math.h>
#include <stdio.h>

/**
 * Test kernel for validation
 *
 * @param q: q-value
 * @param r_small: small axis length
 * @param r_long: rotation axis length
 * @param angle: angle between rotation axis and q vector
 * @return: oriented kernel value
 */
double kernel(double q, double r_small, double r_long, double angle) {
	double length;
	double sin_alpha;
	double cos_alpha;
	double sph_func;

	sin_alpha = sin(angle);
	cos_alpha = cos(angle);

	// Modified length for phase
	length = r_small*sqrt(sin_alpha*sin_alpha +
			r_long*r_long/(r_small*r_small)*cos_alpha*cos_alpha);

	// Spherical scattering ampliture, with modified length for ellipsoid
	sph_func = 3.0*( sin(q*length) - q*length*cos(q*length) ) / (q*q*q*length*length*length);

	return sph_func*sph_func;
}

/**
 * Function to evaluate 1D scattering function
 * @param pars: parameters of the ellipsoid
 * @param q: q-value
 * @return: function value
 */
double ellipsoid_analytical_1D(EllipsoidParameters *pars, double q) {
	double dp[6];

	dp[0] = pars->scale;
	dp[1] = pars->radius_a;
	dp[2] = pars->radius_b;
	dp[3] = pars->sldEll;
	dp[4] = pars->sldSolv;
	dp[5] = pars->background;

	return EllipsoidForm(dp, q);
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the ellipsoid
 * @param q: q-value
 * @return: function value
 */
double ellipsoid_analytical_2DXY(EllipsoidParameters *pars, double qx, double qy) {
	double q;
	q = sqrt(qx*qx+qy*qy);
    return ellipsoid_analytical_2D_scaled(pars, q, qx/q, qy/q);
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the ellipsoid
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double ellipsoid_analytical_2D(EllipsoidParameters *pars, double q, double phi) {
    return ellipsoid_analytical_2D_scaled(pars, q, cos(phi), sin(phi));
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the ellipsoid
 * @param q: q-value
 * @param q_x: q_x / q
 * @param q_y: q_y / q
 * @return: function value
 */
double ellipsoid_analytical_2D_scaled(EllipsoidParameters *pars, double q, double q_x, double q_y) {
	double cyl_x, cyl_y, cyl_z;
	double q_z, lenq;
	double theta, alpha, f, vol, sin_val, cos_val;
	double answer;

    // Ellipsoid orientation
    cyl_x = sin(pars->axis_theta) * cos(pars->axis_phi);
    cyl_y = sin(pars->axis_theta) * sin(pars->axis_phi);
    cyl_z = cos(pars->axis_theta);

    // q vector
    q_z = 0.0;

    // Compute the angle btw vector q and the
    // axis of the cylinder
    cos_val = cyl_x*q_x + cyl_y*q_y + cyl_z*q_z;

    // The following test should always pass
    if (fabs(cos_val)>1.0) {
    	printf("ellipsoid_ana_2D: Unexpected error: cos(alpha)>1\n");
     	return 0;
    }

    // Angle between rotation axis and q vector
	alpha = acos( cos_val );

	// Call the IGOR library function to get the kernel
	answer = EllipsoidKernel(q, pars->radius_b, pars->radius_a, cos_val);

	// Multiply by contrast^2
	answer *= (pars->sldEll - pars->sldSolv) * (pars->sldEll - pars->sldSolv);

	//normalize by cylinder volume
    vol = 4.0/3.0 * acos(-1.0) * pars->radius_b * pars->radius_b * pars->radius_a;
	answer *= vol;

	//convert to [cm-1]
	answer *= 1.0e8;

	//Scale
	answer *= pars->scale;

	// add in the background
	answer += pars->background;

	return answer;
}
