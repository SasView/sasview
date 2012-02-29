#if !defined(gaussian_h)
#define gaussian_h
#include "parameters.hh"

/** Structure definition for Gaussian parameters.
 * The Gaussian is normalized to the 'scale' parameter.
 *
 * f(x)=scale * 1/(sigma^2*2pi)e^(-(x-mu)^2/2sigma^2)
 *
 * [PYTHONCLASS] = Gaussian
 * [DESCRIPTION] = <text>f(x)=scale * 1/(sigma^2*2pi)e^(-(x-mu)^2/2sigma^2)</text>
 */

class Gaussian{
public:
  /// Scale factor
  //  [DEFAULT]=scale=1.0
  Parameter scale;
  /// Standard deviation
  //  [DEFAULT]=sigma=1
  Parameter sigma;
  /// Center of the Gaussian distribution
  //  [DEFAULT]=center=0.0
  Parameter center;

  // Constructor
  Gaussian();

  // Operators to get I(Q)
  double operator()(double q);
  double operator()(double qx, double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);
};

#endif
