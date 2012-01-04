/**
 * Gaussian function
 */

#include "gaussian.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>


/**
 * Function to evaluate 1D Gaussian function.
 * The function is normalized to the 'scale' parameter.
 * 
 * f(x)=scale * 1/(sigma^2*2pi)e^(-(x-mu)^2/2sigma^2)
 * 
 * @param pars: parameters of the gaussian
 * @param x: x-value
 * @return: function value
 */
double gaussian_analytical_1D(GaussianParameters *pars, double x) {
	double sigma2 = pow(pars->sigma, 2);	
	return pars->scale / sigma2 * exp( -pow((x-pars->center), 2) / (2*sigma2));
}

/**
 * Function to evaluate 2D Gaussian  function
 * The function is normalized to the 'scale' parameter.
 * 
 * f(x,y) = Gaussian(x) * Gaussian(y)
 * 
 * where both Gaussians share the same parameters.
 * 
 * @param pars: parameters of the gaussian
 * @param x: x-value
 * @param y: y-value
 * @return: function value
 */
double gaussian_analytical_2DXY(GaussianParameters *pars, double x, double y) {
    return gaussian_analytical_1D(pars, x) * gaussian_analytical_1D(pars, y);
} 

/**
 * Function to evaluate 2D Gaussian  function
 * The function is normalized to the 'scale' parameter.
 * 
 * f(x,y) = Gaussian(x) * Gaussian(y)
 * 
 * where both Gaussians share the same parameters.
 * 
 * @param pars: parameters of the gaussian
 * @param length: length of the (x,y) vector
 * @param phi: angle relative to x
 * @return: function value
 */
double gaussian_analytical_2D(GaussianParameters *pars, double length, double phi) {
    return gaussian_analytical_2DXY(pars, length*cos(phi), length*sin(phi));
} 
