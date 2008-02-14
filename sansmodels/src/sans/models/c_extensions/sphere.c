/**
 * Scattering model for a sphere
 * @author: Mathieu Doucet / UTK
 */

#include "sphere.h"
#include "libSphere.h"
#include <math.h>


/**
 * Function to evaluate 1D scattering function
 * @param pars: parameters of the sphere
 * @param q: q-value
 * @return: function value
 */
double sphere_analytical_1D(SphereParameters *pars, double q) {
	double dp[5];
	
	dp[0] = pars->scale;
	dp[1] = pars->radius;
	dp[2] = pars->contrast;
	dp[3] = pars->background;
	
	return SphereForm(dp, q);
}
    
/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the sphere
 * @param q: q-value
 * @return: function value
 */
double sphere_analytical_2D(SphereParameters *pars, double q, double phi) {
	return sphere_analytical_1D(pars,q);
}

double sphere_analytical_2DXY(SphereParameters *pars, double qx, double qy){
	return sphere_analytical_1D(pars,sqrt(qx*qx+qy*qy));	
}
