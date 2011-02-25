/**
 * Lorentzian function
 */

#include "lorentzian.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>


/**
 * Function to evaluate 1D Lorentzian function.
 * The function is normalized to the 'scale' parameter.
 * 
 * f(x)=scale * 1/pi 0.5gamma / [ (x-x_0)^2 + (0.5gamma)^2 ]
 * 
 * @param pars: parameters of the Lorentzian
 * @param x: x-value
 * @return: function value
 */
double lorentzian_analytical_1D(LorentzianParameters *pars, double x) {
	double delta2 = pow( (x-pars->center), 2);
	return pars->scale / acos(-1.0) * 0.5*pars->gamma /
		(delta2 + 0.25*pars->gamma*pars->gamma);
}

/**
 * Function to evaluate 2D Lorentzian  function
 * The function is normalized to the 'scale' parameter.
 * 
 * f(x,y) = Lorentzian(x) * Lorentzian(y)
 * 
 * where both Lorentzians share the same parameters.
 * 
 * @param pars: parameters of the Lorentzian
 * @param x: x-value
 * @param y: y-value
 * @return: function value
 */
double lorentzian_analytical_2DXY(LorentzianParameters *pars, double x, double y) {
    return lorentzian_analytical_1D(pars, x) * lorentzian_analytical_1D(pars, y);
} 

/**
 * Function to evaluate 2D Lorentzian  function
 * The function is normalized to the 'scale' parameter.
 * 
 * f(x,y) = Lorentzian(x) * Lorentzian(y)
 * 
 * where both Lorentzians share the same parameters.
 * 
 * @param pars: parameters of the Lorentzian
 * @param length: length of the (x,y) vector
 * @param phi: angle relative to x
 * @return: function value
 */
double lorentzian_analytical_2D(LorentzianParameters *pars, double length, double phi) {
    return lorentzian_analytical_2DXY(pars, length*cos(phi), length*sin(phi));
} 
