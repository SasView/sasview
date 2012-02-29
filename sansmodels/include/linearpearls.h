#if !defined(o_h)
#define linearpearls_h
#include "parameters.hh"

/**
 * Structure definition for the parameters
 */
//[PYTHONCLASS] = LinearPearlsModel
//[DISP_PARAMS] = radius, edge_separation
//[DESCRIPTION] =<text>Calculate form factor for Pearl Necklace Model
//				[Macromol. 1996, 29, 2974-2979]
//				Parameters:
//				background:background
//				scale: scale factor
//				sld_pearl: the SLD of the pearl spheres
//				sld_solv: the SLD of the solvent
//				num_pearls: number of the pearls
//				radius: the radius of a pearl
//				edge_separation: the length of string segment; surface to surface
//		</text>
//[FIXED]=  <text>radius.width; edge_separation.width</text>
//[NON_FITTABLE_PARAMS]= <text></text>
//[ORIENTATION_PARAMS]= <text> </text>

typedef struct {
  /// Scale factor
  //  [DEFAULT]=scale= 1.0
  double scale;
  ///	radius [A]
  //  [DEFAULT]=radius=80.0 [A]
  double radius;
  ///	edge_separation
  //  [DEFAULT]=edge_separation= 350 [A]
  double edge_separation;
  ///	num_pearls
  //  [DEFAULT]=num_pearls= 3
  double num_pearls;
  ///	sld_pearl
  //  [DEFAULT]=sld_pearl= 1.0e-06 [1/A^(2)]
  double sld_pearl;
  ///	sld_solv
  //  [DEFAULT]=sld_solv= 6.3e-06 [1/A^(2)]
  double sld_solv;
  /// Background
  //  [DEFAULT]=background=0
  double background;

}LinearPearlsParameters;



class LinearPearlsModel{
public:
  // Model parameters
  /// Scale factor
  //  [DEFAULT]=scale= 1.0
  Parameter scale;
  /// radius [A]
  //  [DEFAULT]=radius=80.0 [A]
  Parameter radius;
  /// edge_separation
  //  [DEFAULT]=edge_separation= 350 [A]
  Parameter edge_separation;
  /// num_pearls
  //  [DEFAULT]=num_pearls= 3
  Parameter num_pearls;
  /// sld_pearl
  //  [DEFAULT]=sld_pearl= 1.0e-06 [1/A^(2)]
  Parameter sld_pearl;
  /// sld_solv
  //  [DEFAULT]=sld_solv= 6.3e-06 [1/A^(2)]
  Parameter sld_solv;
  /// Background
  //  [DEFAULT]=background=0
  Parameter background;

  // Constructor
  LinearPearlsModel();

  // Operators to get I(Q)
  double operator()(double q);
  double operator()(double qx, double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);
};

#endif
