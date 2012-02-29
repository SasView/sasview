#if !defined(logNormal_h)
#define logNormal_h
#include "parameters.hh"

/** Structure definition for Gaussian parameters.
 * The Log normal is normalized to the 'scale' parameter.
 *
 * f(x)=scale * 1/(sigma*math.sqrt(2pi))e^(-1/2*((math.log(x)-mu)/sigma)^2)
 *
 * [PYTHONCLASS] = LogNormal
 * [DESCRIPTION] = <text>f(x)=scale * 1/(sigma*math.sqrt(2pi))e^(-1/2*((math.log(x)-mu)/sigma)^2)</text>
 */

class LogNormal{
public:
  /// Scale factor
  //  [DEFAULT]=scale=1.0
  Parameter scale;
  /// Standard deviation
  //  [DEFAULT]=sigma=1
  Parameter sigma;
  /// Center of the Log Normal distribution
  //  [DEFAULT]=center=0.0
  Parameter center;

  // Constructor
  LogNormal();

  // Operators to get I(Q)
  double operator()(double q);
  double operator()(double qx, double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);
};

#endif
