#if !defined(lamellarFF_HG_h)
#define lamellarFF_HG_h
#include "parameters.hh"

/** Structure definition for lamellar parameters
 * [PYTHONCLASS] = LamellarFFHGModel
 * [DISP_PARAMS] =  t_length, h_thickness
   [DESCRIPTION] = <text> Parameters: t_length = tail length, h_thickness = head thickness,
			scale = Scale factor,
			background = incoherent Background
			sld_tail = tail scattering length density ,
			sld_solvent = solvent scattering length density.
			NOTE: The total bilayer thickness
			= 2(h_thickness+ t_length).

	</text>
	[FIXED]= t_length.width, h_thickness.width
	[ORIENTATION_PARAMS]=
 **/

class LamellarFFHGModel{
public:
  // Model parameters
  /// Scale factor
  //  [DEFAULT]=scale=1.0
  Parameter scale;
  /// tail length [A]
  //  [DEFAULT]=t_length=15.0 [A]
  Parameter t_length;
  /// head thickness
  //  [DEFAULT]=h_thickness=10.0 [A]
  Parameter h_thickness;
  /// tail scrattering length density[1/A^(2)]
  //  [DEFAULT]=sld_tail=4e-7 [1/A^(2)]
  Parameter sld_tail;
  /// head group scrattering length density[1/A^(2)]
  //  [DEFAULT]=sld_head=3e-6 [1/A^(2)]
  Parameter sld_head;
  /// solvent scrattering length density[1/A^(2)]
  //  [DEFAULT]=sld_solvent=6e-6 [1/A^(2)]
  Parameter sld_solvent;
  /// Incoherent Background [1/cm] 0.00
  //  [DEFAULT]=background=0.0 [1/cm]
  Parameter background;

  // Constructor
  LamellarFFHGModel();

  // Operators to get I(Q)
  double operator()(double q);
  double operator()(double qx, double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);
};

#endif
