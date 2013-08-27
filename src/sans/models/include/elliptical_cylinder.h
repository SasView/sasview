#if !defined(ell_cylinder_h)
#define ell_cylinder_h
#include "parameters.hh"

/** Structure definition for cylinder parameters
 * [PYTHONCLASS] = EllipticalCylinderModel
 * [DISP_PARAMS] = r_minor, r_ratio, length, cyl_theta, cyl_phi, cyl_psi
 * [DESCRIPTION] = <text> Model parameters: r_minor = the radius of minor axis of the cross section
r_ratio = the ratio of (r_major /r_minor >= 1)
length = the length of the cylinder
sldCyl = SLD of the cylinder
sldSolv = SLD of solvent -
background = incoherent background
 *</text>
 * [FIXED]= <text> cyl_phi.width;
 * cyl_theta.width; cyl_psi.width; length.width; r_minor.width; r_ratio.width
 *</text>
 * [ORIENTATION_PARAMS]= cyl_phi; cyl_theta; cyl_psi;  cyl_phi.width; cyl_theta.width; cyl_psi.width
 * */

class EllipticalCylinderModel{
public:
  // Model parameters
  /// Minor radius [A]
  //  [DEFAULT]=r_minor=20.0 [A]
  Parameter r_minor;
  /// Scale factor
  //  [DEFAULT]=scale=1.0
  Parameter scale;
  /// Ratio of major/minor radii
  //  [DEFAULT]=r_ratio=1.5
  Parameter r_ratio;
  /// Length of the cylinder [A]
  //  [DEFAULT]=length=400.0 [A]
  Parameter length;
  /// SLD of cylinder [1/A^(2)]
  //  [DEFAULT]=sldCyl=4.0e-6 [1/A^(2)]
  Parameter sldCyl;
  /// SLD of solvent [1/A^(2)]
  //  [DEFAULT]=sldSolv=1.0e-6 [1/A^(2)]
  Parameter sldSolv;
  /// Incoherent Background [1/cm] 0.000
  //  [DEFAULT]=background=0 [1/cm]
  Parameter background;
  /// Orientation of the cylinder axis w/respect incoming beam [deg]
  //  [DEFAULT]=cyl_theta=90.0 [deg]
  Parameter cyl_theta;
  /// Orientation of the cylinder in the plane of the detector [deg]
  //  [DEFAULT]=cyl_phi=0.0 [deg]
  Parameter cyl_phi;
  /// Orientation of major radius of the cross-section w/respect vector q [deg]
  //  [DEFAULT]=cyl_psi=0.0 [deg]
  Parameter cyl_psi;

  // Constructor
  EllipticalCylinderModel();

  // Operators to get I(Q)
  double operator()(double q);
  double operator()(double qx, double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);
};
#endif
