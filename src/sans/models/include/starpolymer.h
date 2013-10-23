#ifndef STAR_POLYMER_H
#define STAR_POLYMER_H

/**
	This software was developed by Institut Laue-Langevin as part of
	Distributed Data Analysis of Neutron Scattering Experiments (DANSE).

	Copyright 2012 Institut Laue-Langevin

**/

/**
   Scattering model class for 'Star polymer with Gaussian statistics'
   with
   P(q) = 2/{fv^2} * (v - (1-exp(-v)) + {f-1}/2 * (1-exp(-v))^2)
   where
   - v = u^2f/(3f-2)
   - u = <R_g^2>q^2, where <R_g^2> is the ensemble average radius of 
   gyration squared of an arm
   - f is the number of arms on the star

**/

// [PYTHONCLASS] = StarPolymer
// [DISP_PARAMS] = arms, R2, scale, background
// [DESCRIPTION] = <text>  Scattering model class for 'Star polymer with Gaussian statistics'
// with
// P(q) = 2/{fv^2} * (v - (1-exp(-v)) + {f-1}/2 * (1-exp(-v))^2)
// where
// - v = u^2f/(3f-2)
// - u = <R_g^2>q^2, where <R_g^2> is the ensemble average radius of 
// giration squared of an arm
// - f is the number of arms on the star
// </text>
// [FIXED] = 
// [ORIENTATION_PARAMS] = 

#include "parameters.hh"

class StarPolymer {

public:

  // Model parameters

  /// Number of arms in the model
  // [DEFAULT]=arms=3
  Parameter arms;

  /// Ensemble radius of gyration squared of an arm [A]
  // [DEFAULT]=R2=100.0 [A]
  Parameter R2;

  /// Scale factor
  // [DEFAULT]=scale=1.0
  Parameter scale;

  /// Background [1/cm]
  // [DEFAULT]=background=0 [1/cm]
  Parameter background;

  StarPolymer();

  // Operators to get I(q)
  double operator()(double q);
  double operator()(double qx, double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);

};



#endif
