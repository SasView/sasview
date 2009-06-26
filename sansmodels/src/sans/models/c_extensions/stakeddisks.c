/**
 * Scattering model for a staked disk
 * TODO: Add 2D analysis
 */

#include "stakeddisks.h"
#include <math.h>
#include "libCylinder.h"
#include <stdio.h>
#include <stdlib.h>


/**
 * Function to evaluate 1D scattering function
 * @param pars: parameters of the staked disks
 * @param q: q-value
 * @return: function value
 */
double flexible_cylinder_analytical_1D(StakedParameters *pars, double q) {
	double dp[10];
	
	// Fill paramater array
	dp[0] = pars->scale;
	dp[1] = pars->length;
	dp[2] = pars->kuhn_length;
	dp[3] = pars->radius;
	dp[4] = pars->contrast;
	dp[5] = pars->background;

	// Call library function to evaluate model
	return FlexExclVolCyl(dp, q);	
}
/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the staked disks
 * @param q: q-value
 * @return: function value
 */
double flexible_cylinder_analytical_2DXY(FlexibleCylinderParameters *pars, double qx, double qy) {
	double q;
	q = sqrt(qx*qx+qy*qy);
    return flexible_cylinder_analytical_2D_scaled(pars, q, qx/q, qy/q);
} 


/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the staked disks
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double flexible_cylinder_analytical_2D(FlexibleCylinderParameters *pars, double q, double phi) {
    return flexible_cylinder_analytical_2D_scaled(pars, q, cos(phi), sin(phi));
} 
        
/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the staked disks
 * @param q: q-value
 * @param q_x: q_x / q
 * @param q_y: q_y / q
 * @return: function value
 */
double flexible_cylinder_analytical_2D_scaled(FlexibleCylinderParameters *pars, double q, double q_x, double q_y) {
	double cyl_x, cyl_y, cyl_z;
	double q_z;
	double alpha, vol, cos_val;
	double answer;
	
	

    // parallelepiped orientation
    cyl_x = sin(pars->axis_theta) * cos(pars->axis_phi);
    cyl_y = sin(pars->axis_theta) * sin(pars->axis_phi);
    cyl_z = cos(pars->axis_theta);
     
    // q vector
    q_z = 0;
        
    // Compute the angle btw vector q and the
    // axis of the parallelepiped
    cos_val = cyl_x*q_x + cyl_y*q_y + cyl_z*q_z;
    
    // The following test should always pass
    if (fabs(cos_val)>1.0) {
    	printf("parallel_ana_2D: Unexpected error: cos(alpha)>1\n");
     	return 0;
    }
    
    // Note: cos(alpha) = 0 and 1 will get an
    // undefined value from PPKernel
	alpha = acos( cos_val );

	// Call the IGOR library function to get the kernel
	answer = CylKernel(q, pars->radius, pars->length/2.0, alpha) / sin(alpha);
	
	// Multiply by contrast^2
	answer *= pars->contrast*pars->contrast;
	
	//normalize by staked disks volume
	//NOTE that for this (Fournet) definition of the integral, one must MULTIPLY by Vparallel
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
    

