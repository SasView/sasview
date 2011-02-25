/**
 * Schulz function
 */

#include "schulz.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>


/**
 * Function to evaluate 1D Schulz function.
 * The function is normalized to the 'scale' parameter.
 *
 * f(x)=scale * math.pow(z+1, z+1)*math.pow((R), z)*
 *					math.exp(-R*(z+1))/(center*gamma(z+1)
 *		z= math.pow[(1/(sigma/center),2]-1
 *		R= x/center
 * @param pars: parameters of the schulz
 * @param x: x-value
 * @return: function value
 */
double schulz_analytical_1D(SchulzParameters *pars, double x) {
	double z = pow(pars->center/ pars->sigma, 2)-1;
	double R= x/pars->center;
	double zz= z+1;
	double expo;
	expo = log(pars->scale)+zz*log(zz)+z*log(R)-R*zz-log(pars->center)-lgamma(zz);

	return exp(expo);//pars->scale * pow(zz,zz) * pow(R,z) * exp(-1*R*zz)/((pars->center) * tgamma(zz)) ;
}

/**
 * Function to evaluate 2D schulz function
 * The function is normalized to the 'scale' parameter.
 *
 * f(x,y) = Schulz(x) * Schulz(y)
 *
 * where both Shulzs share the same parameters.
 *
 * @param pars: parameters of the schulz
 * @param x: x-value
 * @param y: y-value
 * @return: function value
 */
double schulz_analytical_2DXY(SchulzParameters *pars, double x, double y) {
    return schulz_analytical_1D(pars, x) * schulz_analytical_1D(pars, y);
}

/**
 * Function to evaluate 2D Schulz  function
 * The function is normalized to the 'scale' parameter.
 *
 * f(x,y) = Schulz(x) * Schulz(y)
 *
 * where both Gaussians share the same parameters.
 *
 * @param pars: parameters of the gaussian
 * @param length: length of the (x,y) vector
 * @param phi: angle relative to x
 * @return: function value
 */
double schulz_analytical_2D(SchulzParameters *pars, double length, double phi) {
    return schulz_analytical_2DXY(pars, length*cos(phi), length*sin(phi));
}
