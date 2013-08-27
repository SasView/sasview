#if !defined(corefourshell_h)
#define corefourshell_h
#include "parameters.hh"

/**
 * Structure definition for sphere parameters
 */
//[PYTHONCLASS] = CoreFourShellModel
//[DISP_PARAMS] = rad_core0, thick_shell1,thick_shell2,thick_shell3,thick_shell4
//[DESCRIPTION] =<text> Calculates the scattering intensity from a core-4 shell structure.
// 			scale = scale factor * volume fraction
//				rad_core0: the radius of the core
//				sld_core0: the SLD of the core
//				thick_shelli: the thickness of the i'th shell from the core
//				sld_shelli: the SLD of the i'th shell from the core
//				sld_solv: the SLD of the solvent
//				background: incoherent background
//		</text>
//[FIXED]=<text>  thick_shell4.width; thick_shell1.width;thick_shell2.width;thick_shell3.width;rad_core0.width </text>
//[ORIENTATION_PARAMS]= <text> M0_sld_shell4; M_theta_shell4; M_phi_shell4;M0_sld_shell3; M_theta_shell3; M_phi_shell3; M0_sld_shell2; M_theta_shell2; M_phi_shell2;M0_sld_shell1; M_theta_shell1; M_phi_shell1; M0_sld_core0; M_theta_core0; M_phi_core0;M0_sld_solv; M_theta_solv; M_phi_solv; Up_frac_i; Up_frac_f; Up_theta; </text>
//[MAGNETIC_PARAMS]= <text>  M0_sld_shell4; M_theta_shell4; M_phi_shell4;M0_sld_shell3; M_theta_shell3; M_phi_shell3;M0_sld_shell2; M_theta_shell2; M_phi_shell2;M0_sld_shell1; M_theta_shell1; M_phi_shell1; M0_sld_core0; M_theta_core0; M_phi_core0; M0_sld_solv; M_theta_solv; M_phi_solv; Up_frac_i; Up_frac_f; Up_theta; </text>


class CoreFourShellModel{
public:
  // Model parameters
  /// Scale factor
  //  [DEFAULT]=scale= 1.0
  Parameter scale;

  /// Radius of the core0 [A]
  //  [DEFAULT]=rad_core0=60. [A]
  Parameter rad_core0;

  /// sld of core0 [1/A^(2)]
  //  [DEFAULT]=sld_core0= 6.4e-6 [1/A^(2)]
  Parameter sld_core0;

  /// thickness of the shell1 [A]
  //  [DEFAULT]=thick_shell1=10.0 [A]
  Parameter thick_shell1;

  ///  sld of shell1 [1/A^(2)]
  //  [DEFAULT]=sld_shell1= 1.0e-6 [1/A^(2)]
  Parameter sld_shell1;

  ///  thickness of the shell2 [A]
  //  [DEFAULT]=thick_shell2=10.0 [A]
  Parameter thick_shell2;

  /// sld of shell2 [1/A^(2)]
  //  [DEFAULT]=sld_shell2= 2.0e-6 [1/A^(2)]
  Parameter sld_shell2;

  /// thickness of the shell3 [A]
  //  [DEFAULT]=thick_shell3=10.0 [A]
  Parameter thick_shell3;

  ///  sld of shell3 [1/A^(2)]
  //  [DEFAULT]=sld_shell3= 3.0e-6 [1/A^(2)]
  Parameter sld_shell3;

  ///  thickness of the shell4 [A]
  //  [DEFAULT]=thick_shell4=10.0 [A]
  Parameter thick_shell4;

  /// sld of shell4 [1/A^(2)]
  //  [DEFAULT]=sld_shell4= 4.0e-6 [1/A^(2)]
  Parameter sld_shell4;

  /// sld_solv[1/A^(2)]
  //  [DEFAULT]=sld_solv= 6.4e-6 [1/A^(2)]
  Parameter sld_solv;

  /// Incoherent Background [1/cm]
  //  [DEFAULT]=background=0.001 [1/cm]
  Parameter background;

  /// M0_sld_shell1
  //  [DEFAULT]=M0_sld_shell1=0.0e-6 [1/A^(2)]
  Parameter M0_sld_shell1;

  /// M_theta_shell1
  //  [DEFAULT]=M_theta_shell1=0.0 [deg]
  Parameter M_theta_shell1;

  /// M_phi_shell1
  //  [DEFAULT]=M_phi_shell1=0.0 [deg]
  Parameter M_phi_shell1;

  /// M0_sld_shell2
  //  [DEFAULT]=M0_sld_shell2=0.0e-6 [1/A^(2)]
  Parameter M0_sld_shell2;

  /// M_theta_shell2
  //  [DEFAULT]=M_theta_shell2=0.0 [deg]
  Parameter M_theta_shell2;

  /// M_phi_shell2
  //  [DEFAULT]=M_phi_shell2=0.0 [deg]
  Parameter M_phi_shell2;

  /// M0_sld_shell3
  //  [DEFAULT]=M0_sld_shell3=0.0e-6 [1/A^(2)]
  Parameter M0_sld_shell3;

  /// M_theta_shell3
  //  [DEFAULT]=M_theta_shell3=0.0 [deg]
  Parameter M_theta_shell3;

  /// M_phi_shell3
  //  [DEFAULT]=M_phi_shell3=0.0 [deg]
  Parameter M_phi_shell3;

  /// M0_sld_shell4
  //  [DEFAULT]=M0_sld_shell4=0.0e-6 [1/A^(2)]
  Parameter M0_sld_shell4;

  /// M_theta_shell4
  //  [DEFAULT]=M_theta_shell4=0.0 [deg]
  Parameter M_theta_shell4;

  /// M_phi_shell4
  //  [DEFAULT]=M_phi_shell4=0.0 [deg]
  Parameter M_phi_shell4;

  /// M0_sld_core0
  //  [DEFAULT]=M0_sld_core0=0.0e-6 [1/A^(2)]
  Parameter M0_sld_core0;

  /// M_theta_core0
  //  [DEFAULT]=M_theta_core0=0.0 [deg]
  Parameter M_theta_core0;

  /// M_phi_core0
  //  [DEFAULT]=M_phi_core0=0.0 [deg]
  Parameter M_phi_core0;

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
  CoreFourShellModel();

  // Operators to get I(Q)
  double operator()(double q);
  double operator()(double qx, double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);
};

#endif
