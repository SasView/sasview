#if !defined(lorentzian_h)
#define lorentzian_h
#include "parameters.hh"

/** Structure definition for Lorentzian parameters.
 * The Lorentzian is normalized to the 'scale' parameter.
 *
 * f(x)=scale * 1/pi 0.5gamma / [ (x-x_0)^2 + (0.5gamma)^2 ]
 *
 * [PYTHONCLASS] = Lorentzian
 * [DESCRIPTION] = <text>f(x)=scale * 1/pi 0.5gamma / [ (x-x_0)^2 + (0.5gamma)^2 ]</text>
 * [ORIENTATION_PARAMS]= <text> </text>
 */

class Lorentzian{
public:
  /// Scale factor
  //  [DEFAULT]=scale=1.0
  Parameter scale;
  /// Width
  //  [DEFAULT]=gamma=1.0
  Parameter gamma;
  /// Center of the Lorentzian distribution
  //  [DEFAULT]=center=0.0
  Parameter center;

  // Constructor
  Lorentzian();

  // Operators to get I(Q)
  double operator()(double q);
  double operator()(double qx, double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);
};

#endif
