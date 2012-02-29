#if !defined(cylinder_h)
#define cylinder_h
#include "parameters.hh"

/** Structure definition for cylinder parameters
 * [PYTHONCLASS] = CylinderModel
 * [DISP_PARAMS] = radius, length, cyl_theta, cyl_phi
   [DESCRIPTION] = <text> f(q)= 2*(sldCyl - sldSolv)*V*sin(qLcos(alpha/2))
				/[qLcos(alpha/2)]*J1(qRsin(alpha/2))/[qRsin(alpha)]

		P(q,alpha)= scale/V*f(q)^(2)+bkg
		V: Volume of the cylinder
		R: Radius of the cylinder
		L: Length of the cylinder
		J1: The bessel function
		alpha: angle betweenthe axis of the
		cylinder and the q-vector for 1D
		:the ouput is P(q)=scale/V*integral
		from pi/2 to zero of...
		f(q)^(2)*sin(alpha)*dalpha+ bkg
		</text>
	[FIXED]= <text>cyl_phi.width; cyl_theta.width; length.width;radius.width</text>
	[ORIENTATION_PARAMS]= <text>cyl_phi; cyl_theta; cyl_phi.width; cyl_theta.width</text>


 **/
class CylinderModel{
public:
  // Model parameters

  /// Scale factor
  //  [DEFAULT]=scale=1.0
  Parameter scale;

  /// Radius of the cylinder [A]
  //  [DEFAULT]=radius=20.0 [A]
  Parameter radius;

  /// Length of the cylinder [A]
  //  [DEFAULT]=length=400.0 [A]
  Parameter length;

  /// Contrast [1/A^(2)]
  //  [DEFAULT]=sldCyl=4.0e-6 [1/A^(2)]
  Parameter sldCyl;

  /// sldCyl [1/A^(2)]
  //  [DEFAULT]=sldSolv=1.0e-6 [1/A^(2)]
  Parameter sldSolv;

  /// Incoherent Background [1/cm] 0.00
  //  [DEFAULT]=background=0.0 [1/cm]
  Parameter background;

  /// Orientation of the cylinder axis w/respect incoming beam [deg]
  //  [DEFAULT]=cyl_theta=60.0 [deg]
  Parameter cyl_theta;

  /// Orientation of the cylinder in the plane of the detector [deg]
  //  [DEFAULT]=cyl_phi=60.0 [deg]
  Parameter cyl_phi;

  // Constructor
  CylinderModel();

  // Operators to get I(Q)
  double operator()(double q);
  double operator()(double qx, double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);
};

#endif
