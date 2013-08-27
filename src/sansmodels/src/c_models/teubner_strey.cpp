/**
	This software was developed by Institut Laue-Langevin as part of
	Distributed Data Analysis of Neutron Scattering Experiments (DANSE).

	Copyright 2012 Institut Laue-Langevin

**/

#include <math.h>
#include "parameters.hh"
#include "teubner_strey.h"

TeubnerStreyModel::TeubnerStreyModel() {
  scale = Parameter(0.1);
  c1 = Parameter(-30.0);
  c2 = Parameter(5000.0);
  background = Parameter(0.0);
}

double TeubnerStreyModel::operator()(double q) { 
  double d_scale = scale();
  double d_c1 = c1();
  double d_c2 = c2();
  double d_background = background();

  double term1 = d_c1 * pow(q,2);
  double term2 = d_c2 * pow(q,4);

  return 1/(d_scale + term1 + term2) + d_background;

}


double TeubnerStreyModel::operator()(double qx,double qy) {
  double q = sqrt(qx*qx + qy*qy);
  return this->operator()(q);
}

double TeubnerStreyModel::calculate_ER() {
  // not implemented yet
  return 0.0;
}

double TeubnerStreyModel::calculate_VR() {
  return 1.0;
}

double TeubnerStreyModel::evaluate_rphi(double q,double phi) {
  double qx = q*cos(phi);
  double qy = q*sin(phi);
  return this->operator()(qx, qy);
}



/***
    Notes

    This file was ported from python to C++ at ILL Grenoble in
    July 2012. In the original python file were two functions,
    teubnerStreyLengths and teubnerStreyDistance that did not appear
    to be used anywhere in the code. The source for them is below:

    def teubnerStreyLengths(self):
        """
            Calculate the correlation length (L) 
            @return L: the correlation distance 
        """
        return  math.pow( 1/2 * math.pow( (self.params['scale']/self.params['c2']), 1/2 )\
                            +(self.params['c1']/(4*self.params['c2'])),-1/2 )
    def teubnerStreyDistance(self):
        """
            Calculate the quasi-periodic repeat distance (D/(2*pi)) 
            @return D: quasi-periodic repeat distance
        """
        return  math.pow( 1/2 * math.pow( (self.params['scale']/self.params['c2']), 1/2 )\
                            -(self.params['c1']/(4*self.params['c2'])),-1/2 )


***/
