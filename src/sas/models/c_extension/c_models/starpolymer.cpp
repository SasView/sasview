/**
	This software was developed by Institut Laue-Langevin as part of
	Distributed Data Analysis of Neutron Scattering Experiments (DANSE).

	Copyright 2012 Institut Laue-Langevin

**/

#include <math.h>
#include "parameters.hh"
#include "starpolymer.h"

StarPolymer::StarPolymer() {
 
  arms = Parameter(3.0);
  R2 = Parameter(100.0);
  scale = Parameter(1.0);
  background = Parameter(0.0);

}

double StarPolymer::operator()(double q) {

  double d_arms = arms();
  double d_R2 = R2();
  double d_scale = scale();
  double d_background = background();

  double u_2 = d_R2 * pow(q,2);
  double v = u_2 * d_arms / (3.0 * d_arms - 2.0);

  double term1 = v - 1.0 + exp(-v);
  double term2 = ((d_arms - 1.0)/2.0)* pow((1.0 - exp(-v)),2.0);

  return 2.0 * d_scale / (d_arms * pow(v,2.0)) * (term1 + term2) + d_background;

}

double StarPolymer::operator()(double qx, double qy) {
  double q = sqrt(qx*qx + qy*qy);
  return this->operator()(q);
}

double StarPolymer::calculate_ER() {
  // not implemented yet
  return 0.0;
}

double StarPolymer::calculate_VR() {
  return 1.0;
}

double StarPolymer::evaluate_rphi(double q, double phi) {
  double qx = q * cos(phi);
  double qy = q * sin(phi);
  return this->operator()(qx, qy);
}


