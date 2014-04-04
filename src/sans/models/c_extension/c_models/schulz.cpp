/**
	This software was developed by the University of Tennessee as part of the
	Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
	project funded by the US National Science Foundation.

	If you use DANSE applications to do scientific research that leads to
	publication, we ask that you acknowledge the use of the software with the
	following sentence:

	"This work benefited from DANSE software developed under NSF award DMR-0520547."

	copyright 2008, University of Tennessee
 */

#include <math.h>
#include "parameters.hh"
#include <stdio.h>
using namespace std;
#include "schulz.h"

#if defined(_MSC_VER)
#include "gamma_win.h"
#endif

Schulz :: Schulz() {
  scale  = Parameter(1.0, true);
  sigma  = Parameter(1.0, true);
  center = Parameter(0.0, true);
}

/**
 * Function to evaluate 1D Schulz function.
 * The function is normalized to the 'scale' parameter.
 *
 * f(x)=scale * math.pow(z+1, z+1)*math.pow((R), z)*
 *          math.exp(-R*(z+1))/(center*gamma(z+1)
 *    z= math.pow[(1/(sigma/center),2]-1
 *    R= x/center
 *
 * @param q: q-value
 * @return: function value
 */
double Schulz :: operator()(double q) {
  double z = pow(center()/ sigma(), 2)-1;
  double R= q/center();
  double zz= z+1;
  double expo;
  expo = log(scale())+zz*log(zz)+z*log(R)-R*zz-log(center())-lgamma(zz);

  return exp(expo);//scale * pow(zz,zz) * pow(R,z) * exp(-1*R*zz)/((center) * tgamma(zz)) ;
}

/**
 * Function to evaluate 2D schulz function
 * The function is normalized to the 'scale' parameter.
 *
 * f(x,y) = Schulz(x) * Schulz(y)
 *
 * where both Shulzs share the same parameters.
 * @param q_x: value of Q along x
 * @param q_y: value of Q along y
 * @return: function value
 */
double Schulz :: operator()(double qx, double qy) {
  return (*this).operator()(qx) * (*this).operator()(qy);
}

/**
 * Function to evaluate 2D schulz function
 * The function is normalized to the 'scale' parameter.
 *
 * f(x,y) = Schulz(x) * Schulz(y)
 *
 * where both Shulzs share the same parameters.
 * @param pars: parameters of the cylinder
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double Schulz :: evaluate_rphi(double q, double phi) {
  double qx = q*cos(phi);
  double qy = q*sin(phi);
  return (*this).operator()(qx, qy);
}
/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double Schulz :: calculate_ER() {
  //NOT implemented yet!!!
  return 0.0;
}
double Schulz :: calculate_VR() {
  return 1.0;
}
