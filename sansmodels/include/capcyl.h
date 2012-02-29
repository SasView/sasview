#if !defined(capcyl_h)
#define capcyl_h
#include "parameters.hh"

/**
 * Structure definition for CappedCylinder parameters
 */
 //[PYTHONCLASS] = CappedCylinderModel
 //[DISP_PARAMS] = rad_cyl,len_cyl,rad_cap,phi,  theta
 //[DESCRIPTION] =<text>Calculates the scattering from a cylinder with spherical section end-caps.
 //				That is, a sphereocylinder
 //				with end caps that have a radius larger than
 //				that of the cylinder and the center of the
 //				end cap radius lies within the cylinder.
 //				Note: As the length of cylinder -->0,
 //				it becomes a ConvexLens.
 //				It must be that rad_cyl <(=) rad_cap.
 //				[Parameters];
 //				scale: volume fraction of spheres,
 //				background:incoherent background,
 //				rad_cyl: radius of the cylinder,
 //				len_cyl: length of the cylinder,
 //				rad_cap: radius of the semi-spherical cap,
 //				sld_capcyl: SLD of the capped cylinder,
 //				sld_solv: SLD of the solvent.
 //		</text>
 //[FIXED]=  rad_cyl.width;len_cyl;rad_cap;phi.width; theta.width
 //[ORIENTATION_PARAMS]= <text> phi; theta; phi.width; theta.width</text>

class CappedCylinderModel{
public:
  // Model parameters
  /// Scale factor
  //  [DEFAULT]=scale= 1.0
  Parameter scale;

  /// rad_cyl [A]
  //  [DEFAULT]=rad_cyl=20.0 [A]
  Parameter rad_cyl;

  /// length of the cylinder
  //  [DEFAULT]=len_cyl=400.0 [A]
  Parameter len_cyl;

  /// Radius of sphere [A]
  //  [DEFAULT]=rad_cap=40.0 [A]
  Parameter rad_cap;

  /// sld_capcyl [1/A^(2)]
  //  [DEFAULT]=sld_capcyl= 1.0e-6 [1/A^(2)]
  Parameter sld_capcyl;

  /// sld_solv [1/A^(2)]
  //  [DEFAULT]=sld_solv= 6.3e-6 [1/A^(2)]
  Parameter sld_solv;

  /// Incoherent Background [1/cm]
  //  [DEFAULT]=background=0.0 [1/cm]
  Parameter background;

  /// Angle of the main axis against z-axis in detector plane [deg]
  //  [DEFAULT]=theta=0.0 [deg]
  Parameter theta;

  /// Azimuthal angle around z-axis in detector plane [deg]
  //  [DEFAULT]=phi=0.0 [deg]
  Parameter phi;

  // Constructor
  CappedCylinderModel();

  // Operators to get I(Q)
  double operator()(double q);
  double operator()(double qx, double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);
};

#endif
