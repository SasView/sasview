#if !defined(triaxial_ellipsoid_h)
#define triaxial_ellipsoid_h
#include "parameters.hh"

/** Structure definition for cylinder parameters
 * [PYTHONCLASS] = TriaxialEllipsoidModel
 * [DISP_PARAMS] = semi_axisA, semi_axisB, semi_axisC,axis_theta, axis_phi, axis_psi
	[DESCRIPTION] = <text>Note: During fitting ensure that the inequality A<B<C is not
	violated. Otherwise the calculation will
	not be correct.
	</text>
	[FIXED]= <text>axis_psi.width; axis_phi.width; axis_theta.width; semi_axisA.width; semi_axisB.width; semi_axisC.width </text>
	[ORIENTATION_PARAMS]= <text>axis_psi; axis_phi; axis_theta; axis_psi.width; axis_phi.width; axis_theta.width</text>
 **/

class TriaxialEllipsoidModel{
public:
  // Model parameters
  /// Scale factor
  //  [DEFAULT]=scale=1.0
  Parameter scale;
  /// semi -axis A of the triaxial_ellipsoid [A]
  //  [DEFAULT]=semi_axisA= 35.0 [A]
  Parameter semi_axisA;
  /// semi -axis B of the triaxial_ellipsoid [A]
  //  [DEFAULT]=semi_axisB=100.0 [A]
  Parameter semi_axisB;
  /// semi -axis C of the triaxial_ellipsoid [A]
  //  [DEFAULT]=semi_axisC=400.0 [A]
  Parameter semi_axisC;
  /// sldEll [1/A^(2)]
  //  [DEFAULT]=sldEll=1.0e-6 [1/A^(2)]
  Parameter sldEll;
  /// sldSolv [1/A^(2)]
  //  [DEFAULT]=sldSolv=6.3e-6 [1/A^(2)]
  Parameter sldSolv;
  /// Incoherent Background [1/cm] 0.00
  //  [DEFAULT]=background=0.0 [1/cm]
  Parameter background;
  /// Orientation of the triaxial_ellipsoid axis w/respect incoming beam [deg]
  //  [DEFAULT]=axis_theta=57.325 [deg]
  Parameter axis_theta;
  /// Orientation of the triaxial_ellipsoid in the plane of the detector [deg]
  //  [DEFAULT]=axis_phi=57.325 [deg]
  Parameter axis_phi;
  /// Orientation of the cross section of the triaxial_ellipsoid in the plane of the detector [deg]
  //  [DEFAULT]=axis_psi=0.0 [deg]
  Parameter axis_psi;

  // Constructor
  TriaxialEllipsoidModel();

  // Operators to get I(Q)
  double operator()(double q);
  double operator()(double qx, double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);
};
#endif
