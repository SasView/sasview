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
 //[ORIENTATION_PARAMS]= <text> M0_sld_sph; M_theta_sph; M_phi_sph;M0_sld_solv; M_theta_solv; M_phi_solv; Up_frac_i; Up_frac_f; Up_theta; </text>
 //[MAGNETIC_PARAMS]= <text> M0_sld_sph; M_theta_sph; M_phi_sph; M0_sld_solv; M_theta_solv; M_phi_solv; Up_frac_i; Up_frac_f; Up_theta; </text>
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

	/// M0_sld_sph
	//  [DEFAULT]=M0_sld_sph=0.0e-6 [1/A^(2)]
	Parameter M0_sld_sph;

	/// M_theta_sph
	//  [DEFAULT]=M_theta_sph=0.0 [deg]
	Parameter M_theta_sph;

	/// M_phi_sph
	//  [DEFAULT]=M_phi_sph=0.0 [deg]
	Parameter M_phi_sph;

	/// M0_sld_solv
	//  [DEFAULT]=M0_sld_solv=0.0e-6 [1/A^(2)]
	Parameter M0_sld_solv;

	/// M_theta_solv
	//  [DEFAULT]=M_theta_solv=0.0 [deg]
	Parameter M_theta_solv;

	/// M_phi_solv
	//  [DEFAULT]=M_phi_solv=0.0 [deg]
	Parameter M_phi_solv;
	
	/// Up_frac_i
	//  [DEFAULT]=Up_frac_i=0.5 [u/(u+d)]
	Parameter Up_frac_i;

	/// Up_frac_f
	//  [DEFAULT]=Up_frac_f=0.5 [u/(u+d)]
	Parameter Up_frac_f;

	/// Up_theta
	//  [DEFAULT]=Up_theta=0.0 [deg]
	Parameter Up_theta;


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
