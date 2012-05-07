#if !defined(raspberry_h)
#define raspberry_h
#include "parameters.hh"

/**
 * Structure definition for RaspBerryModel parameters
 */
//[PYTHONCLASS] = RaspBerryModel
//[DISP_PARAMS] = radius_Lsph
//[DESCRIPTION] =<text> RaspBerryModel:
//				volf_Lsph = volume fraction large spheres
//				radius_Lsph = radius large sphere (A)
//				sld_Lsph = sld large sphere (A-2)
//				volf_Ssph = volume fraction small spheres
//				radius_Ssph = radius small sphere (A)
//				surfrac_Ssph = fraction of small spheres at surface
//				sld_Ssph = sld small sphere
//				delta_Ssph = small sphere penetration (A) 
//				sld_solv   = sld solvent
//				background = background (cm-1)
//			Ref: J. coll. inter. sci. (2010) vol. 343 (1) pp. 36-41.
//		</text>
//[FIXED]=  radius_Lsph.width
//[ORIENTATION_PARAMS]= <text> </text>

class RaspBerryModel{
public:
  // Model parameters
  /// volf_Lsph 
  //  [DEFAULT]=volf_Lsph=0.05
  Parameter volf_Lsph;
  /// radius_Lsph [A]
  //  [DEFAULT]=radius_Lsph= 5000.0 [A]
  Parameter radius_Lsph;
  /// sld_Lsph [1/A^(2)]
  //  [DEFAULT]=sld_Lsph= -4.0e-7 [1/A^(2)]
  Parameter sld_Lsph;
  /// volf_Ssph 
  //  [DEFAULT]=volf_Ssph=0.005
  Parameter volf_Ssph;
  /// radius_Ssph [A]
  //  [DEFAULT]=radius_Ssph= 100.0 [A]
  Parameter radius_Ssph;
  /// surfrac_Ssph 
  //  [DEFAULT]=surfrac_Ssph=0.4
  Parameter surfrac_Ssph;
  /// sld_Ssph [1/A^(2)]
  //  [DEFAULT]=sld_Ssph= 3.5e-6 [1/A^(2)]
  Parameter sld_Ssph;  
  /// delta_Ssph [A]
  //  [DEFAULT]=delta_Ssph= 0.0
  Parameter delta_Ssph;
  /// sld_solv [1/A^(2)]
  //  [DEFAULT]=sld_solv= 6.3e-6 [1/A^(2)]
  Parameter sld_solv;
  /// Incoherent Background [1/cm]
  //  [DEFAULT]=background=0.0 [1/cm]
  Parameter background;

  // Constructor
  RaspBerryModel();

  // Operators to get I(Q)
  double operator()(double q);
  double operator()(double qx, double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);
};
double raspberry_kernel(double dp[], double q);
double rasp_bes(double qval, double rad);
#endif
