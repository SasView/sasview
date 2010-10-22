/**
 * Scattering model for a core-shell cylinder
 * @author: Mathieu Doucet / UTK
 */

#include "core_shell_cylinder.h"
#include "libCylinder.h"
#include <math.h>
#include <stdio.h>


/**
 * Function to evaluate 1D scattering function
 * @param pars: parameters of the core-shell cylinder
 * @param q: q-value
 * @return: function value
 */
double core_shell_cylinder_analytical_1D(CoreShellCylinderParameters *pars, double q) {
	double dp[8];

	dp[0] = pars->scale;
	dp[1] = pars->radius;
	dp[2] = pars->thickness;
	dp[3] = pars->length;
	dp[4] = pars->core_sld;
	dp[5] = pars->shell_sld;
	dp[6] = pars->solvent_sld;
	dp[7] = pars->background;

	return CoreShellCylinder(dp, q);
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the core-shell cylinder
 * @param q: q-value
 * @return: function value
 */
double core_shell_cylinder_analytical_2DXY(CoreShellCylinderParameters *pars, double qx, double qy) {
	double q;
	q = sqrt(qx*qx+qy*qy);
    return core_shell_cylinder_analytical_2D_scaled(pars, q, qx/q, qy/q);
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the core-shell cylinder
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double core_shell_cylinder_analytical_2D(CoreShellCylinderParameters *pars, double q, double phi) {
    return core_shell_cylinder_analytical_2D_scaled(pars, q, cos(phi), sin(phi));
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the core-shell cylinder
 * @param q: q-value
 * @param q_x: q_x / q
 * @param q_y: q_y / q
 * @return: function value
 */
double core_shell_cylinder_analytical_2D_scaled(CoreShellCylinderParameters *pars, double q, double q_x, double q_y) {
	double cyl_x, cyl_y, cyl_z;
	double q_z, lenq;
	double alpha, f, vol, sin_val, cos_val;
	double answer;
	//convert angle degree to radian
	double pi = 4.0*atan(1.0);
	double theta = pars->axis_theta * pi/180.0;
	double phi = pars->axis_phi * pi/180.0;

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
    	printf("core_shell_cylinder_analytical_2D: Unexpected error: cos(alpha)=%g\n", cos_val);
     	return 0;
    }

	alpha = acos( cos_val );

	// Call the IGOR library function to get the kernel
	answer = CoreShellCylKernel(q, pars->radius, pars->thickness,
								pars->core_sld,pars->shell_sld,
								pars->solvent_sld, pars->length/2.0, alpha) / fabs(sin(alpha));

	//normalize by cylinder volume
	vol=pi*(pars->radius+pars->thickness)
			*(pars->radius+pars->thickness)
			*(pars->length+2.0*pars->thickness);
	answer /= vol;

	//convert to [cm-1]
	answer *= 1.0e8;

	//Scale
	answer *= pars->scale;

	// add in the background
	answer += pars->background;

	return answer;
}
