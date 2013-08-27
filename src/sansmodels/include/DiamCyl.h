#if !defined(DiamCyl_h)
#define DiamCyl_h
#include "parameters.hh"

/**
* To calculate the 2nd virial coefficient
* [PYTHONCLASS] = DiamCylFunc
* [DISP_PARAMS] = radius, length
  [DESCRIPTION] =<text>To calculate the 2nd virial coefficient for
  the non-spherical object, then find the
  radius of sphere that has this value of
  virial coefficient.
 				</text>
	[FIXED]= <text>
				radius.width; length.width
			</text>
**/

class DiamCylFunc{
public:
  // Model parameters
  /// Radius [A]
  //  [DEFAULT]=radius=20.0 A
  Parameter radius;
  /// Length [A]
  //  [DEFAULT]=length= 400 A
  Parameter length;

  // Constructor
  DiamCylFunc();

  // Operators to get I(Q)
  double operator()(double q);
  double operator()(double qx, double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);
};

#endif
