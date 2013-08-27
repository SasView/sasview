#if !defined(binaryHS_h)
#define binaryHS_h
#include "parameters.hh"

/**
 * Structure definition for binary hard sphere parameters

	[PYTHONCLASS] = BinaryHSModel
	[DISP_PARAMS] = l_radius,s_radius
	[DESCRIPTION] =<text> Model parameters: l_radius : large radius of binary hard sphere
			s_radius : small radius of binary hard sphere
			vol_frac_ls : volume fraction of large spheres
			vol_frac_ss : volume fraction of small spheres
			ls_sld: large sphere  scattering length density
			ss_sld: small sphere scattering length density
			solvent_sld: solvent scattering length density
			background: incoherent background
               </text>
	[FIXED]= l_radius.width;s_radius.width
	[ORIENTATION_PARAMS]= <text> </text>
 */

class BinaryHSModel{
public:
  // Model parameters
  /// large radius of the binary hard sphere [A]
  //  [DEFAULT]=l_radius= 100.0 [A]
  Parameter l_radius;

  /// small radius of the binary hard sphere [A]
  //  [DEFAULT]=s_radius= 25.0 [A]
  Parameter s_radius;

  /// volume fraction of large spheres
  //  [DEFAULT]=vol_frac_ls= 0.1
  Parameter vol_frac_ls;

  /// volume fraction of small spheres
  //  [DEFAULT]=vol_frac_ss= 0.2
  Parameter vol_frac_ss;

  /// large sphere scattering length density [1/A^(2)]
  //  [DEFAULT]=ls_sld= 3.5e-6 [1/A^(2)]
  Parameter ls_sld;

  /// lsmall sphere scattering length density [1/A^(2)]
  //  [DEFAULT]=ss_sld= 5e-7 [1/A^(2)]
  Parameter ss_sld;

  /// solvent scattering length density [1/A^(2)]
  //  [DEFAULT]=solvent_sld= 6.36e-6 [1/A^(2)]
  Parameter solvent_sld;

  /// Incoherent Background [1/cm]
  //  [DEFAULT]=background=0.001 [1/cm]
  Parameter background;

  //Constructor
  BinaryHSModel();

  //Operators to get I(Q)
  double operator()(double q);
  double operator()(double qx , double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);
};

#endif
