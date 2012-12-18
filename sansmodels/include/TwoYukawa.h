#if !defined(TwoYukawa_h)
#define TwoYukawa_h
#include "parameters.hh"

/**
 * Structure definition for TwoYukawaModel (factor) parameters
 */
//[PYTHONCLASS] = TwoYukawaModel
//[DESCRIPTION] =<text>Structure factor for interacting particles:                   .
//
//  Calculates the structure factor, S(q), for a monodisperse spherical particle interacting 
//  through a two-Yukawa potential. The Mean Spherical Approximation is used as the 
//  closure to solve the Ornstein-Zernicke equations.
//
//  The function calculated is S(q), based on the solution of the Ornstein-Zernicke equations 
//  using the Two-Yukawa potential (in its scaled form, r=r/diam):
//
//  Radius is that of the hard core. The returned value is dimensionless.
//	 </text>


class TwoYukawaModel{
public:

  // Model parameters

  /// Something volfraction
  //  [DEFAULT]=volfraction= 0.2
  Parameter volfraction;
  
  //  [DEFAULT]=effect_radius= 50.0 [A]
  Parameter effect_radius;
  
  //  [DEFAULT]=scale_K1= 6.0
  Parameter scale_K1;
  
  //  [DEFAULT]=decayConst_Z1= 10.0
  Parameter decayConst_Z1;
  
  //  [DEFAULT]=scale_K2= -1.0
  Parameter scale_K2;
  
  //  [DEFAULT]=decayConst_Z2= 2.0
  Parameter decayConst_Z2;

  // Constructor
  TwoYukawaModel();

  // Operators to get I(Q)
  double operator()(double q);
  double operator()(double qx, double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);
};

#endif
