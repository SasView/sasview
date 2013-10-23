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
 //[ORIENTATION_PARAMS]= <text> M0_sld_shell; M_theta_shell; M_phi_shell; M0_sld_core; M_theta_core; M_phi_core;M0_sld_solv; M_theta_solv; M_phi_solv; Up_frac_i; Up_frac_f; Up_theta; </text>
 //[MAGNETIC_PARAMS]= <text>  M0_sld_shell; M_theta_shell; M_phi_shell;M0_sld_core; M_theta_core; M_phi_core; M0_sld_solv; M_theta_solv; M_phi_solv; Up_frac_i; Up_frac_f; Up_theta; </text>


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

/// M0_sld_shell
//  [DEFAULT]=M0_sld_shell=0.0e-6 [1/A^(2)]
  Parameter M0_sld_shell;

/// M_theta_shell
//  [DEFAULT]=M_theta_shell=0.0 [deg]
  Parameter M_theta_shell;

/// M_phi_shell
//  [DEFAULT]=M_phi_shell=0.0 [deg]
  Parameter M_phi_shell;

/// M0_sld_core
//  [DEFAULT]=M0_sld_core=0.0e-6 [1/A^(2)]
  Parameter M0_sld_core;

/// M_theta_core
//  [DEFAULT]=M_theta_core=0.0 [deg]
  Parameter M_theta_core;

/// M_phi_core
//  [DEFAULT]=M_phi_core=0.0 [deg]
  Parameter M_phi_core;

/// M0_sld_solv
//  [DEFAULT]=M0_sld_solv=0.0e-6 [1/A^(2)]
  Parameter M0_sld_solv;

/// M_theta_solv
//  [DEFAULT]=M_theta_solv=0.0 [deg]
  Parameter M_theta_solv;

/// M_phi_solv
//  [DEFAULT]=M_phi_solv=0.0 [deg]
  Parameter M_phi_solv;

/// Up_frac_i
//  [DEFAULT]=Up_frac_i=0.5 [u/(u+d)]
  Parameter Up_frac_i;

/// Up_frac_f
//  [DEFAULT]=Up_frac_f=0.5 [u/(u+d)]
  Parameter Up_frac_f;

/// Up_theta
//  [DEFAULT]=Up_theta=0.0 [deg]
  Parameter Up_theta;

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
