#if !defined(hollow_cylinder_h)
#define hollow_cylinder_h
#include "parameters.hh"

/**
 * Structure definition for hollow cylinder parameters
 */
//[PYTHONCLASS] = HollowCylinderModel
//[DISP_PARAMS] = core_radius, radius, length, axis_theta, axis_phi
//[DESCRIPTION] = <text> P(q) = scale*<f*f>/Vol + bkg, where f is the scattering amplitude.
//					core_radius = the radius of core
//				radius = the radius of shell
// 			length = the total length of the cylinder
//				sldCyl = SLD of the shell
//				sldSolv = SLD of the solvent
//				background = incoherent background
//	</text>
//[FIXED]= <text> axis_phi.width; axis_theta.width; length.width;core_radius.width; radius</text>
//[ORIENTATION_PARAMS]= axis_phi; axis_theta;axis_phi.width; axis_theta.width

class HollowCylinderModel{
public:
  // Model parameters
  /// Scale factor
  //  [DEFAULT]=scale=1.0
  Parameter scale;

  /// Core radius [A]
  //  [DEFAULT]=core_radius=20.0 [A]
  Parameter core_radius;

  /// Shell radius [A]
  //  [DEFAULT]=radius=30.0 [A]
  Parameter radius;

  /// Hollow cylinder length [A]
  //  [DEFAULT]=length=400.0 [A]
  Parameter length;

  /// SLD_cylinder  [1/A^(2)]
  //  [DEFAULT]=sldCyl=6.3e-6 [1/A^(2)]
  Parameter sldCyl;

  /// SLD_solvent  [1/A^(2)]
  //  [DEFAULT]=sldSolv=1.0e-6 [1/A^(2)]
  Parameter sldSolv;

  /// Incoherent Background [1/cm]
  //  [DEFAULT]=background=0.01 [1/cm]
  Parameter background;

  /// Orientation of the long axis of the hollow cylinder w/respect incoming beam [deg]
  //  [DEFAULT]=axis_theta=90.0 [deg]
  Parameter axis_theta;

  /// Orientation of the long axis of the hollow cylinder in the plane of the detector [deg]
  //  [DEFAULT]=axis_phi=0.0 [deg]
  Parameter axis_phi;
  //Constructor
  HollowCylinderModel();

  //Operators to get I(Q)
  double operator()(double q);
  double operator()(double qx , double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);
};

#endif
