#if !defined(multishell_h)
#define multishell_h
#include "parameters.hh"

/**
 * Structure definition for sphere parameters

	[PYTHONCLASS] = MultiShellModel
	[DISP_PARAMS] = core_radius, s_thickness, w_thickness
	[DESCRIPTION] =<text> MultiShell (Sphere) Model (or Multilamellar Vesicles): Model parameters;
				scale : scale factor
				core_radius : Core radius of the multishell
				s_thickness: shell thickness
				w_thickness: water thickness
				core_sld: core scattering length density
				shell_sld: shell scattering length density
				n_pairs:number of pairs of water/shell
				background: incoherent background
               </text>
	[FIXED]=  core_radius.width; s_thickness.width; w_thickness.width
	[ORIENTATION_PARAMS]= <text> </text>
 */

class MultiShellModel{
public:
  // Model parameters
  /// Scale factor
  //  [DEFAULT]=scale= 1.0
  Parameter scale;

  /// Core radius of the multishell [A]
  //  [DEFAULT]=core_radius=60.0 [A]
  Parameter core_radius;

  /// shell thickness [A]
  //  [DEFAULT]=s_thickness= 10.0 [A]
  Parameter s_thickness;

  /// water thickness [A]
  //  [DEFAULT]=w_thickness= 10.0 [A]
  Parameter w_thickness;

  /// core scattering length density [1/A^(2)]
  //  [DEFAULT]=core_sld= 6.4e-6 [1/A^(2)]
  Parameter core_sld;

  /// shell scattering length density [1/A^(2)]
  //  [DEFAULT]=shell_sld= 4.0e-7 [1/A^(2)]
  Parameter shell_sld;

  /// number of pairs of water and shell
  //  [DEFAULT]=n_pairs= 2
  Parameter n_pairs;

  /// Incoherent Background [1/cm]
  //  [DEFAULT]=background=0 [1/cm]
  Parameter background;

  //Constructor
  MultiShellModel();

  //Operators to get I(Q)
  double operator()(double q);
  double operator()(double qx , double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);
};

#endif
