#if !defined(fuzzysphere_h)
#define fuzzysphere_h
#include "parameters.hh"

/**
 * Structure definition for FuzzySphere parameters
 */
//[PYTHONCLASS] = FuzzySphereModel
//[DISP_PARAMS] = radius, fuzziness
//[DESCRIPTION] =<text>
//				scale: scale factor times volume fraction,
//					or just volume fraction for absolute scale data
//				radius: radius of the solid sphere
//				fuzziness = the STD of the height of fuzzy interfacial
//				 thickness (ie., so-called interfacial roughness)
//				sldSph: the SLD of the sphere
//				sldSolv: the SLD of the solvent
//				background: incoherent background
//			Note: By definition, this function works only when fuzziness << radius.
//		</text>
//[FIXED]=  radius.width; fuzziness.width
//[ORIENTATION_PARAMS]= <text> </text>

class FuzzySphereModel{
public:
  // Model parameters
  /// Radius of sphere [A]
  //  [DEFAULT]=radius=60.0 [A]
  Parameter radius;
  /// Scale factor
  //  [DEFAULT]=scale= 0.01
  Parameter scale;


  /// surface roughness [A]
  //  [DEFAULT]=fuzziness= 10.0 [A]
  Parameter fuzziness;

  /// sldSph [1/A^(2)]
  //  [DEFAULT]=sldSph= 1.0e-6 [1/A^(2)]
  Parameter sldSph;

  /// sldSolv [1/A^(2)]
  //  [DEFAULT]=sldSolv= 3.0e-6 [1/A^(2)]
  Parameter sldSolv;

  /// Incoherent Background [1/cm]
  //  [DEFAULT]=background=0.001 [1/cm]
  Parameter background;

  // Constructor
  FuzzySphereModel();

  // Operators to get I(Q)
  double operator()(double q);
  double operator()(double qx, double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);
};

#endif
