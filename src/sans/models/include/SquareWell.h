#if !defined(SquareWell_h)
#define SquareWell_h
#include "parameters.hh"

/**Structure definition for SquareWell parameters
 */
//   [PYTHONCLASS] = SquareWellStructure
//   [DISP_PARAMS] = effect_radius
//   [DESCRIPTION] = <text> Structure Factor for interacting particles:             .
//
//  The interaction potential is
//
//		U(r)= inf   , r < 2R
//			= -d    , 2R <= r <=2Rw
//			= 0     , r >= 2Rw
//
//		R: effective radius (A)of the particle
//		v: volume fraction
//		d: well depth
//		w: well width; multiples of the
//		particle diameter
//
//		Ref: Sharma, R. V.; Sharma,
//      K. C., Physica, 1977, 89A, 213.
//   			</text>
//   [FIXED]= effect_radius.width
//[ORIENTATION_PARAMS]= <text> </text>

class SquareWellStructure{
public:
  // Model parameters
  /// effective radius of particle [A]
  //  [DEFAULT]=effect_radius=50.0 [A]
  Parameter effect_radius;

  /// Volume fraction
  //  [DEFAULT]=volfraction= 0.040
  Parameter volfraction;

  /// Well depth [kT]
  //  [DEFAULT]=welldepth= 1.50 [kT]
  Parameter welldepth;

  /// Well width
  //  [DEFAULT]=wellwidth= 1.20
  Parameter wellwidth;

  // Constructor
  SquareWellStructure();

  // Operators to get I(Q)
  double operator()(double q);
  double operator()(double qx, double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);
};

#endif
