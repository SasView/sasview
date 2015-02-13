#if !defined(flexcyl_ellipX_h)
#define flexcyl_ellipX_h
#include "parameters.hh"

/** Structure definition for Flexible cylinder w/ EllipX parameters
 * [PYTHONCLASS] = FlexCylEllipXModel
 * [DISP_PARAMS] = length, kuhn_length, radius, axis_ratio
   [DESCRIPTION] = <text> Note : scale and contrast=sldCyl-sldSolv are both multiplicative factors in the
		model and are perfectly correlated. One or
		both of these parameters must be held fixed
		during model fitting.
		</text>
	[FIXED]= <text>length.width; kuhn_length.width; radius.width; axis_ratio.width</text>
	[ORIENTATION_PARAMS]= <text></text>
 **/

class FlexCylEllipXModel{
public:
  // Model parameters
  /// Scale factor
  //  [DEFAULT]=scale=1.0
  Parameter scale;
  /// Length of the flexible cylinder [A]
  //  [DEFAULT]=length=1000 [A]
  Parameter length;
  /// Kuhn length of the flexible cylinder [A]
  //  [DEFAULT]=kuhn_length=100 [A]
  Parameter kuhn_length;
  /// Radius of the flexible cylinder [A]
  //  [DEFAULT]=radius=20.0 [A]
  Parameter radius;
  /// axis_ratio (major_radius/radius
  //  [DEFAULT]=axis_ratio=1.5
  Parameter axis_ratio;
  /// SLD of cylinder [1/A^(2)]
  //  [DEFAULT]=sldCyl=1.0e-6 [1/A^(2)]
  Parameter sldCyl;
  /// SLD of solvent [1/A^(2)]
  //  [DEFAULT]=sldSolv=6.3e-6 [1/A^(2)]
  Parameter sldSolv;
  /// Incoherent Background [1/cm]
  //  [DEFAULT]=background=0.0001 [1/cm]
  Parameter background;

  // Constructor
  FlexCylEllipXModel();

  // Operators to get I(Q)
  double operator()(double q);
  double operator()(double qx, double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);
};

#endif
