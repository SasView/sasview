#if !defined(core_shell_h)
#define core_shell_h
#include "parameters.hh"

/**
 * Structure definition for core-shell parameters
 */
 //[PYTHONCLASS] = CoreShellModel
 //[DISP_PARAMS] = radius, thickness
 //[DESCRIPTION] =<text>Form factor for a monodisperse spherical particle with particle
 //    with a core-shell structure:
 //
 //    The form factor is normalized by the
 //    total particle volume.
 //
 //		radius: core radius, thickness: shell thickness
 //
 //     Ref: Guinier, A. and G. Fournet,
 //     John Wiley and Sons, New York, 1955.
 //				</text>
 //[FIXED]= <text> thickness.width;radius.width</text>


class CoreShellModel{
public:
  // Model parameters

  /// Core Radius [A] 60.0
  //  [DEFAULT]=radius=60.0 [A]
  Parameter radius;
  /// Scale factor
  //  [DEFAULT]=scale=1.0
  Parameter scale;
  /// Shell Thickness [A] 10.0
  //  [DEFAULT]=thickness=10 [A]
  Parameter thickness;
  /// Core SLD [1/A^(2)] 1.0e-6
  //  [DEFAULT]=core_sld=1.0e-6 [1/A^(2)]
  Parameter core_sld;
/// Shell SLD [1/A^(2)] 2.0e-6
//  [DEFAULT]=shell_sld=2.0e-6 [1/A^(2)]
  Parameter shell_sld;
/// Solvent SLD [1/A^(2)] 3.0e-6
//  [DEFAULT]=solvent_sld=3.0e-6 [1/A^(2)]
  Parameter solvent_sld;
/// Incoherent Background [1/cm] 0.000
//  [DEFAULT]=background=0 [1/cm]
  Parameter background;

  // Constructor
  CoreShellModel();

  // Operators to get I(Q)
  double operator()(double q);
  double operator()(double qx, double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);
};


#endif
