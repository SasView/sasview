/**
 * Scattering model for a hollow cylinder
 * @author:gervaise alina / UTK
 */

#include "hollow_cylinder.h"
#include "libCylinder.h"
#include <math.h>
#include <stdio.h>


/**
 * Function to evaluate 1D scattering function
 * @param pars: parameters of the hollow cylinder
 * @param q: q-value
 * @return: function value
 */
double hollow_cylinder_analytical_1D(HollowCylinderParameters *pars, double q) {
	double dp[7];

	dp[0] = pars->scale;
	dp[1] = pars->core_radius;
	dp[2] = pars->radius;
	dp[3] = pars->length;
	dp[4] = pars->sldCyl;
	dp[5] = pars->sldSolv;
	dp[6] = pars->background;

	return HollowCylinder(dp, q);
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the Hollow cylinder
 * @param q: q-value
 * @return: function value
 */
double hollow_cylinder_analytical_2DXY(HollowCylinderParameters *pars, double qx, double qy) {
	double q;
	q = sqrt(qx*qx+qy*qy);
    return hollow_cylinder_analytical_2D_scaled(pars, q, qx/q, qy/q);
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the hollow cylinder
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double hollow_cylinder_analytical_2D(HollowCylinderParameters *pars, double q, double phi) {
    return hollow_cylinder_analytical_2D_scaled(pars, q, cos(phi), sin(phi));
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the hollow cylinder
 * @param q: q-value
 * @param q_x: q_x / q
 * @param q_y: q_y / q
 * @return: function value
 */
double hollow_cylinder_analytical_2D_scaled(HollowCylinderParameters *pars, double q, double q_x, double q_y) {
	double cyl_x, cyl_y, cyl_z;
	double q_z;
	double  alpha,vol, cos_val;
	double answer;

    // Cylinder orientation
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
    	printf("core_shell_cylinder_analytical_2D: Unexpected error: cos(alpha)=%g\n", cos_val);
     	return 0;
    }

	alpha = acos( cos_val );

	// Call the IGOR library function to get the kernel
	answer = HolCylKernel(q, pars->core_radius, pars->radius, pars->length, cos_val);

	// Multiply by contrast^2
	answer *= (pars->sldCyl - pars->sldSolv)*(pars->sldCyl - pars->sldSolv);

	//normalize by cylinder volume
	vol=acos(-1.0)*((pars->radius*pars->radius)-(pars->core_radius *pars->core_radius))
			*(pars->length);
	answer /= vol;

	//convert to [cm-1]
	answer *= 1.0e8;

	//Scale
	answer *= pars->scale;

	// add in the background
	answer += pars->background;

	return answer;
}
