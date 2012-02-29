#if !defined(polygausscoil_h)
#define polygausscoil_h
#include "parameters.hh"

/**
 * Structure definition for sphere parameters
 */
//[PYTHONCLASS] = Poly_GaussCoil
//[DISP_PARAMS] = rg
//[DESCRIPTION] =<text>I(q)=(scale)*2*[(1+U*x)^(-1/U)+x-1]/[(1+U)*x^2] + background
//				where x = [rg^2*q^2]
//					and the polydispersity is
//					U = [M_w/M_n]-1.
//				scale = scale factor * volume fraction
//				rg = radius of gyration
//				poly_m = polydispersity of molecular weight
//				background = incoherent background
//		</text>
//[FIXED]=
//[ORIENTATION_PARAMS]= <text> </text>

class Poly_GaussCoil{
public:
  // Model parameters
  /// Radius of gyration [A]
  //  [DEFAULT]=rg=60.0 [A]
  Parameter rg;

  /// Scale factor
  //  [DEFAULT]=scale= 1.0
  Parameter scale;

  /// polydispersity of molecular weight
  //  [DEFAULT]=poly_m= 2.0 [Mw/Mn]
  Parameter poly_m;

  /// Incoherent Background [1/cm]
  //  [DEFAULT]=background=0.001 [1/cm]
  Parameter background;

  // Constructor
  Poly_GaussCoil();

  // Operators to get I(Q)
  double operator()(double q);
  double operator()(double qx, double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);
};

#endif
