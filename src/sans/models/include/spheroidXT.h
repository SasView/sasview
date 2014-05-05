#if !defined(spheroidXT_h)
#define spheroidXT_h
#include "parameters.hh"
// RKH 03Apr2014 a re-parametrised model

/** Structure definition for oblate parameters
 * [PYTHONCLASS] = CoreShellEllipsoidXTModel
 * [DISP_PARAMS] = equat_core, X_core, T_shell, XpolarShell,axis_phi, axis_theta
   [DESCRIPTION] = <text>[SpheroidCoreShellModel] Calculates the form factor for an spheroid
			ellipsoid particle with a core_shell structure.
			The form factor is averaged over all possible
			orientations of the ellipsoid such that P(q)
			= scale*<f^2>/Vol + bkg, where f is the
			single particle scattering amplitude.
			[Parameters]:
			equat_core = equatorial radius of core,
			polar_core = polar radius of core = equat_core*X_core,
			equat_shell = equatorial radius of outer surface = equat_core + T_shell,
			polar_shell = polar radius (revolution axis) of outer surface =  equat_core*X_core + XpolarShell*T_shell
			sld_core = SLD_core
			sld_shell = SLD_shell
			sld_solvent = SLD_solvent
			background = Incoherent bkg
			scale =scale
			Note:It is the users' responsibility to ensure
			that shell radii are larger than core radii.
			oblate: polar radius < equatorial radius
			prolate :  polar radius > equatorial radius - this new model will make this easier
			and polydispersity integrals more logical (as previously the shell could disappear).
			</text>

   [FIXED] = <text>equat_core.width;X_core.width; T_shell.width; Xpolarshell.width; axis_phi.width; axis_theta.width</text>
   [ORIENTATION_PARAMS]= <text>axis_phi; axis_theta; axis_phi.width; axis_theta.width</text>

 **/

class CoreShellEllipsoidXTModel{
public:
  // Model parameters
  /// Scale factor
  //  [DEFAULT]=scale=0.05
  Parameter scale;
  /// Equatorial radius of core [A]
  //  [DEFAULT]=equat_core=20.0 [A]
  Parameter equat_core;
  /// X (polar core)/ (equat_shell)
  //  [DEFAULT]=X_core=3.0
  Parameter X_core;
  /// thickness of equatorial shell [A]
  //  [DEFAULT]=T_shell=30.0 [A]
  Parameter T_shell;
  /// ratio (TpolarShell/Tequat_Shell
  //  [DEFAULT]=XpolarShell=1.0
  Parameter XpolarShell;
  ///  Core scattering length density [1/A^(2)]
  //  [DEFAULT]=sld_core=2.0e-6 [1/A^(2)]
  Parameter sld_core;
  ///  Shell scattering length density [1/A^(2)]
  //  [DEFAULT]=sld_shell=1.0e-6 [1/A^(2)]
  Parameter sld_shell;
  /// Solvent scattering length density  [1/A^(2)]
  //  [DEFAULT]=sld_solvent=6.3e-6 [1/A^(2)]
  Parameter sld_solvent;
  /// Incoherent Background [1/cm] 0.001
  //  [DEFAULT]=background=0.001 [1/cm]
  Parameter background;
  //Disable for now
  /// Orientation of the oblate axis w/respect incoming beam [deg]
  //  [DEFAULT]=axis_theta=0.0 [deg]
  Parameter axis_theta;
  /// Orientation of the oblate in the plane of the detector [deg]
  //  [DEFAULT]=axis_phi=0.0 [deg]
  Parameter axis_phi;

  // Constructor
  CoreShellEllipsoidXTModel();

  // Operators to get I(Q)
  double operator()(double q);
  double operator()(double qx, double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);
};

#endif
