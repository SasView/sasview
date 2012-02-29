#if !defined(vesicle_h)
#define vesicle_h
#include "parameters.hh"

/**
 * Structure definition for vesicle parameters
[PYTHONCLASS] = VesicleModel
[DISP_PARAMS] = radius,thickness
[DESCRIPTION] =<text>Model parameters:    radius : the core radius of the vesicle
		thickness: the shell thickness
		core_sld: the core SLD
		shell_sld: the shell SLD
		background: incoherent background
		scale : scale factor
</text>
[FIXED]=  radius.width; thickness.width
[ORIENTATION_PARAMS]= <text> </text>
 */

class VesicleModel{
public:
  // Model parameters
  /// Scale factor
  //  [DEFAULT]=scale= 1.0
  Parameter scale;

  /// Core radius of the vesicle [A]
  //  [DEFAULT]=radius= 100.0 [A]
  Parameter radius;

  /// shell thickness [A]
  //  [DEFAULT]=thickness= 30.0 [A]
  Parameter thickness;

  /// core_solv scattering length density [1/A^(2)]
  //  [DEFAULT]=solv_sld= 6.36e-6 [1/A^(2)]
  Parameter solv_sld;

  /// shell scattering length density [1/A^(2)]
  //  [DEFAULT]=shell_sld= 5.0e-7 [1/A^(2)]
  Parameter shell_sld;

  /// Incoherent Background [1/cm]
  //  [DEFAULT]=background=0 [1/cm]
  Parameter background;

  //Constructor
  VesicleModel();

  //Operators to get I(Q)
  double operator()(double q);
  double operator()(double qx , double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);
};

#endif
