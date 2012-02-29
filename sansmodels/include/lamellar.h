#if !defined(lamellar_h)
#define lamellar_h
#include "parameters.hh"

/** Structure definition for lamellar parameters
 * [PYTHONCLASS] = LamellarModel
 * [DISP_PARAMS] = bi_thick
   [DESCRIPTION] = <text>[Dilute Lamellar Form Factor](from a lyotropic lamellar phase)
		I(q)= 2*pi*P(q)/(delta *q^(2)), where
		P(q)=2*(contrast/q)^(2)*(1-cos(q*delta))^(2))
		bi_thick = bilayer thickness
		sld_bi = SLD of bilayer
		sld_sol = SLD of solvent
		background = Incoherent background
		scale = scale factor

 </text>
[FIXED]= <text>bi_thick.width</text>
 **/

class LamellarModel{
public:
  // Model parameters
  /// Scale factor
  //  [DEFAULT]=scale=1.0
  Parameter scale;
  /// delta bilayer thickness [A]
  //  [DEFAULT]=bi_thick=50.0 [A]
  Parameter bi_thick;
  /// SLD of bilayer [1/A^(2)]
  //  [DEFAULT]=sld_bi=1.0e-6 [1/A^(2)]
  Parameter sld_bi;
  /// SLD of solvent [1/A^(2)]
  //  [DEFAULT]=sld_sol=6.3e-6 [1/A^(2)]
  Parameter sld_sol;
  /// Incoherent Background [1/cm] 0.00
  //  [DEFAULT]=background=0.0 [1/cm]
  Parameter background;
  // Constructor
  LamellarModel();

  // Operators to get I(Q)
  double operator()(double q);
  double operator()(double qx, double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);
};

#endif
