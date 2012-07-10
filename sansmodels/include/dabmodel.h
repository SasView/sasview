#ifndef DAB_MODEL_H
#define DAB_MODEL_H

#include "parameters.hh"

/**
	This software was developed by Institut Laue-Langevin as part of
	Distributed Data Analysis of Neutron Scattering Experiments (DANSE).

	Copyright 2012 Institut Laue-Langevin

**/


// definition for model parameters

// [PYTHONCLASS] = DABModel
// [DISP_PARAMS] = length, scale, background
// [DESCRIPTION] = <text>Provide F(x) = scale/( 1 + (x*L)^2 )^(2) + background
//    DAB (Debye Anderson Brumberger) function as a BaseComponent model
//     </text>
// [FIXED] = 
// [ORIENTATION_PARAMS] =


class DABModel {

public:
  // Model parameters

  /// Correlation length [A]
  // [DEFAULT]=length=50.0 [A]
  Parameter length;

  /// Scale factor
  // [DEFAULT]=scale=1.0
  Parameter scale;

  /// Background [1/cm]
  // [DEFAULT]=background=0 [1/cm]
  Parameter background;

  DABModel();

    // Operators to get I(Q)
  double operator()(double q);
  double operator()(double qx, double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);
};


#endif

