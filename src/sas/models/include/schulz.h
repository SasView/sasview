#if !defined(schulz_h)
#define schulz_h
#include "parameters.hh"

/** Structure definition for Schulz parameters.
 * The Schulz is normalized to the 'scale' parameter.
 *
 * f(x)=scale * math.pow(z+1, z+1)*math.pow((R), z)*
 *					math.exp(-R*(z+1))/(center*gamma(z+1)
 *		z= math.pow[(1/(sigma/center),2]-1
 *		R= x/center
 *
 * [PYTHONCLASS] = Schulz
 * [DESCRIPTION] = <text> f(x)=scale * math.pow(z+1, z+1)*math.pow((R), z)*
 					math.exp(-R*(z+1))/(center*gamma(z+1)
 		            z= math.pow[(1/(sigma/center),2]-1
 					R= x/center</text>
 */

class Schulz{
public:
  /// Scale factor
  //  [DEFAULT]=scale=1.0
  Parameter scale;
  /// Standard deviation
  //  [DEFAULT]=sigma=1
  Parameter sigma;
  /// Center of the Schulz distribution
  //  [DEFAULT]=center=0.0
  Parameter center;

  // Constructor
  Schulz();

  // Operators to get I(Q)
  double operator()(double q);
  double operator()(double qx, double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);
};

#endif
