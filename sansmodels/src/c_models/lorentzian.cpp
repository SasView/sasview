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
#include "lorentzian.h"

Lorentzian :: Lorentzian() {
  scale  = Parameter(1.0, true);
  gamma  = Parameter(1.0, true);
  center = Parameter(0.0, true);
}

/**
 * Function to evaluate 1D scattering function
 * @param q: q-value
 * @return: function value
 */
double Lorentzian :: operator()(double q) {
  double delta2 = pow( (q-center()), 2);
  return scale() / acos(-1.0) * 0.5*gamma() /
      (delta2 + 0.25*gamma()*gamma());
}

/**
 * Function to evaluate 2D scattering function
 * @param q_x: value of Q along x
 * @param q_y: value of Q along y
 * @return: function value
 */
double Lorentzian :: operator()(double qx, double qy) {
  return (*this).operator()(qx) * (*this).operator()(qy);
}

/**
 * Function to evaluate 2D scattering function
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double Lorentzian :: evaluate_rphi(double q, double phi) {
  double qx = q*cos(phi);
  double qy = q*sin(phi);
  return (*this).operator()(qx, qy);
}
/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double Lorentzian :: calculate_ER() {
  //NOT implemented yet!!!
  return 0.0;
}
double Lorentzian :: calculate_VR() {
  return 1.0;
}
