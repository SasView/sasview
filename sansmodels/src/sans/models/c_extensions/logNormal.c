/**
 * log normal function
 */

#include "logNormal.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>


/**
 * Function to evaluate 1D Log normal function.
 * The function is normalized to the 'scale' parameter.
 * 
 * f(x)=scale * 1/(sigma*math.sqrt(2pi))e^(-1/2*((math.log(x)-mu)/sigma)^2)
 * 
 * @param pars: parameters of the log normal 
 * @param x: x-value
 * @return: function value
 */
double logNormal_analytical_1D(LogNormalParameters *pars, double x) {
	double sigma2 = pow(pars->sigma, 2);	
	return pars->scale / (x*sigma2) * exp( -pow((log(x) -pars->center), 2) / (2*sigma2));
}

/**
 * Function to evaluate 2D log normal  function
 * The function is normalized to the 'scale' parameter.
 * 
 * f(x,y) = LogNormal(x) * Lognormal(y)
 * 
 * where both Gaussians share the same parameters.
 * 
 * @param pars: parameters of the log normal 
 * @param x: x-value
 * @param y: y-value
 * @return: function value
 */
double logNormal_analytical_2DXY(LogNormalParameters *pars, double x, double y) {
    return logNormal_analytical_1D(pars, x) * logNormal_analytical_1D(pars, y);
} 

/**
 * Function to evaluate 2D log normal  function
 * The function is normalized to the 'scale' parameter.
 * 
 * f(x,y) = Lognormal(x) * Lognormal(y)
 * 
 * where both log normal s share the same parameters.
 * 
 * @param pars: parameters of the log normal
 * @param length: length of the (x,y) vector
 * @param phi: angle relative to x
 * @return: function value
 */
double logNormal_analytical_2D(LogNormalParameters *pars, double length, double phi) {
    return logNormal_analytical_2DXY(pars, length*cos(phi), length*sin(phi));
} 
