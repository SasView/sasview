#if !defined(DiamEllip_h)
#define DiamEllip_h
#include "parameters.hh"

/**
 * To calculate the 2nd virial coefficient
* [PYTHONCLASS] = DiamEllipFunc
* [DISP_PARAMS] = radius_a, radius_b
  [DESCRIPTION] =<text>To calculate the 2nd virial coefficient for
                            the non-spherical object, then find the
                            radius of sphere that has this value of
                            virial coefficient:
                              radius_a = polar radius,
                              radius_b = equatorial radius;
                                 radius_a > radius_b: Prolate spheroid,
                                 radius_a < radius_b: Oblate spheroid.
 				</text>
	[FIXED]= <text>
				radius_a.width;radius_b.width
			</text>

 **/

class DiamEllipFunc{
public:
  // Model parameters
  /// Polar radius [A]
  //  [DEFAULT]=radius_a=20.0 A
  Parameter radius_a;

  /// Equatorial radius [A]
  //  [DEFAULT]=radius_b= 400 A
  Parameter radius_b;

  // Constructor
  DiamEllipFunc();

  // Operators to get I(Q)
  double operator()(double q);
  double operator()(double qx, double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);
};

#endif
