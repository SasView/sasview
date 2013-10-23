#ifndef TEUBNER_STREY_H
#define TEUBNER_STREY_H

#include "parameters.hh"

/**
	This software was developed by Institut Laue-Langevin as part of
	Distributed Data Analysis of Neutron Scattering Experiments (DANSE).

	Copyright 2012 Institut Laue-Langevin

**/

/**
   Scattering model class for the Teubner-Strey model given by 
    Provide F(x) = 1/( scale + c1*(x)^(2)+  c2*(x)^(4)) + bkd
**/


// definition for model parameters

// [PYTHONCLASS] = TeubnerStreyModel
// [DISP_PARAMS] = scale, c1, c2, background
// [DESCRIPTION] = <text>F(x) = 1/( scale + c1*(x)^(2)+  c2*(x)^(4)) + bkd </text>
//       </text>
// [FIXED] = 
// [ORIENTATION_PARAMS] =

class TeubnerStreyModel {

public:
  // Model parameters

  /// Scale factor
  // [DEFAULT]=scale=0.1
  Parameter scale;

  /// c1
  // [DEFAULT]=c1=-30.0
  Parameter c1;

  /// c2
  // [DEFAULT]=c2=5000.0
  Parameter c2;

  /// Background
  // [DEFAULT]=background=0.0
  Parameter background;

  TeubnerStreyModel();

  // Operators to get I(Q)
  double operator()(double q);
  double operator()(double qx, double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);
};


#endif



