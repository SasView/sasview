
/**
	This software was developed by Institut Laue-Langevin as part of
	Distributed Data Analysis of Neutron Scattering Experiments (DANSE).

	Copyright 2012 Institut Laue-Langevin

**/

/**

   Scattering model class for the DAB (Debye Anderson Brumberger) Model

**/



#include <math.h>
#include "parameters.hh"
#include "dabmodel.h"

DABModel::DABModel() {
  length = Parameter(50.0);
  scale = Parameter(1.0);
  background = Parameter(0.0);

}

double DABModel::operator()(double q) {
  double d_length = length();
  double d_scale = scale();
  double d_background = background();

  double numerator = d_scale*pow(d_length,3);
  double denominator = pow(1 + pow(q*d_length,2),2);

  return numerator / denominator + d_background;
  


}

double DABModel::operator()(double qx,double qy) {
  double q = sqrt(qx*qx + qy*qy);
  return this->operator()(q);
}

double DABModel::calculate_ER() {
  // not implemented yet
  return 0.0;
}

double DABModel::calculate_VR() {
  return 1.0;
}

double DABModel::evaluate_rphi(double q,double phi) {
  double qx = q * cos(phi);
  double qy = q * sin(phi);
  return this->operator()(qx,qy);
}
