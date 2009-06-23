/**
 * Scattering model for a parallelepiped
 * TODO: Add 2D analysis
 */

#include "parallelepiped.h"
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
double parallelepiped_analytical_1D(ParallelepipedParameters *pars, double q) {
	double dp[6];
	
	// Fill paramater array
	dp[0] = pars->scale;
	dp[1] = pars->short_edgeA;
	dp[2] = pars->longer_edgeB;
	dp[3] = pars->longuest_edgeC;
	dp[4] = pars->contrast;
	dp[5] = pars->background;

	// Call library function to evaluate model
	return Parallelepiped(dp, q);	
}
/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the cylinder
 * @param q: q-value
 * @return: function value
 */
double parallelepiped_analytical_2DXY(ParallelepipedParameters *pars, double qx, double qy) {
	double q;
	q = sqrt(qx*qx+qy*qy);
    return parallelepiped_analytical_2D_scaled(pars, q, qx/q, qy/q);
} 


/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the Parallelepiped
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double parallelepiped_analytical_2D(ParallelepipedParameters *pars, double q, double phi) {
    return parallelepiped_analytical_2D_scaled(pars, q, cos(phi), sin(phi));
} 
        
/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the parallelepiped
 * @param q: q-value
 * @param q_x: q_x / q
 * @param q_y: q_y / q
 * @return: function value
 */
double parallelepiped_analytical_2D_scaled(ParallelepipedParameters *pars, double q, double q_x, double q_y) {
	double parallel_x, parallel_y, parallel_z;
	double q_z;
	double alpha, vol, cos_val;
	double aa, mu, uu;
	double answer;
	
	

    // parallelepiped orientation
    parallel_x = sin(pars->parallel_theta) * cos(pars->parallel_phi);
    parallel_y = sin(pars->parallel_theta) * sin(pars->parallel_phi);
    parallel_z = cos(pars->parallel_theta);
     
    // q vector
    q_z = 0;
        
    // Compute the angle btw vector q and the
    // axis of the parallelepiped
    cos_val = parallel_x*q_x + parallel_y*q_y + parallel_z*q_z;
    
    // The following test should always pass
    if (fabs(cos_val)>1.0) {
    	printf("parallel_ana_2D: Unexpected error: cos(alpha)>1\n");
     	return 0;
    }
    
    // Note: cos(alpha) = 0 and 1 will get an
    // undefined value from PPKernel
	alpha = acos( cos_val );

	aa = pars->short_edgeA/pars->longer_edgeB;
	mu = 1.0;
	uu = 1.0;
	
	// Call the IGOR library function to get the kernel
	answer = PPKernel( aa, mu, uu);
	
	// Multiply by contrast^2
	answer *= pars->contrast*pars->contrast;
	
	//normalize by cylinder volume
	//NOTE that for this (Fournet) definition of the integral, one must MULTIPLY by Vparallel
    vol = pars->short_edgeA* pars->longer_edgeB * pars->longuest_edgeC;
	answer *= vol;
	
	//convert to [cm-1]
	answer *= 1.0e8;
	
	//Scale
	answer *= pars->scale;
	
	// add in the background
	answer += pars->background;
	
	return answer;
}
    

