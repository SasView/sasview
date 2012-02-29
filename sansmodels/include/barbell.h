#if !defined(barbell_h)
#define barbell_h
#include "parameters.hh"
/**
 * Structure definition for BarBell parameters
 */
 //[PYTHONCLASS] = BarBellModel
 //[DISP_PARAMS] = rad_bar,len_bar,rad_bell,phi,  theta
 //[DESCRIPTION] =<text>Calculates the scattering from a barbell-shaped cylinder. That is
 //				a sphereocylinder with spherical end caps
 //				that have a radius larger than that of
 //				the cylinder and the center of the end cap
 //				radius lies outside of the cylinder.
 //				Note: As the length of cylinder(bar) -->0,
 //				it becomes a dumbbell.
 //				And when rad_bar = rad_bell,
 //				it is a spherocylinder.
 //				It must be that rad_bar <(=) rad_bell.
 //				[Parameters];
 //				scale: volume fraction of spheres,
 //				background:incoherent background,
 //				rad_bar: radius of the cylindrical bar,
 //				len_bar: length of the cylindrical bar,
 //				rad_bell: radius of the spherical bell,
 //				sld_barbell: SLD of the barbell,
 //				sld_solv: SLD of the solvent.
 //		</text>
 //[FIXED]=  rad_bar.width;len_bar;rad_bell;phi.width; theta.width
 //[ORIENTATION_PARAMS]= <text> phi; theta; phi.width; theta.width</text>

class BarBellModel {
public:
  // Model parameters

  /// Scale factor
  //  [DEFAULT]=scale= 1.0
  Parameter scale;

  /// rad_bar [A]
  //  [DEFAULT]=rad_bar=20.0 [A]
  Parameter rad_bar;

  /// length of the bar [A]
  //  [DEFAULT]=len_bar=400.0 [A]
  Parameter len_bar;

  /// Radius of sphere [A]
  //  [DEFAULT]=rad_bell=40.0 [A]
  Parameter rad_bell;

  /// sld_barbell [1/A^(2)]
  //  [DEFAULT]=sld_barbell= 1.0e-6 [1/A^(2)]
  Parameter sld_barbell;

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
  BarBellModel();

  // Operators to get I(Q)
  double operator()(double q);
  double operator()(double qx, double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);
};

#endif
