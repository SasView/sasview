#if !defined(sphere_h)
#define sphere_h
#include "parameters.hh"

/**
 * Structure definition for sphere parameters
 */
 //[PYTHONCLASS] = SphereModel
 //[DISP_PARAMS] = radius
 //[DESCRIPTION] =<text>P(q)=(scale/V)*[3V(sldSph-sldSolv)*(sin(qR)-qRcos(qR))
 //						/(qR)^3]^(2)+bkg
 //
 //				bkg:background, R: radius of sphere
 //				V:The volume of the scatter
 //				sldSph: the SLD of the sphere
 //				sldSolv: the SLD of the solvent
 //
 //		</text>
 //[FIXED]=  radius.width
 //[ORIENTATION_PARAMS]= <text> </text>
 //[CATEGORY] = Shapes & Spheres

class SphereModel{
public:
  // Model parameters
  /// Scale factor
  //  [DEFAULT]=scale= 1.0
  Parameter scale;

  /// Radius of sphere [A]
  //  [DEFAULT]=radius=60.0 [A]
  Parameter radius;

  /// sldSph [1/A^(2)]
  //  [DEFAULT]=sldSph= 2.0e-6 [1/A^(2)]
  Parameter sldSph;

  /// sldSolv [1/A^(2)]
  //  [DEFAULT]=sldSolv= 1.0e-6 [1/A^(2)]
  Parameter sldSolv;

/// Incoherent Background [1/cm]
//  [DEFAULT]=background=0 [1/cm]
Parameter background;

  // Constructor
  SphereModel();

  // Operators to get I(Q)
  double operator()(double q);
  double operator()(double qx, double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);
};


#endif
