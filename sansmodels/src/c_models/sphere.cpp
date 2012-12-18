/**
	This software was developed by the University of Tennessee as part of the
	Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
	project funded by the US National Science Foundation.

	If you use DANSE applications to do scientific research that leads to
	publication, we ask that you acknowledge the use of the software with the
	following sentence:

	"This work benefited from DANSE software developed under NSF award DMR-0520547."

	copyright 2008, University of Tennessee
 */

/**
 * Scattering model classes
 * The classes use the IGOR library found in
 *   sansmodels/src/libigor
 *
 */

#include <math.h>
#include "parameters.hh"
#include <stdio.h>
using namespace std;
#include "sphere.h"

extern "C" {
	#include "libSphere.h"
	#include "libmultifunc/libfunc.h"
}
// Convenience parameter structure
typedef struct {
    double scale;
    double radius;
    double sldSph;
    double sldSolv;
    double background;
    double M0_sld_sph;
    double M_theta_sph;
    double M_phi_sph;
    double M0_sld_solv;
    double M_theta_solv;
    double M_phi_solv;
    double Up_frac_i;
	double Up_frac_f;
	double Up_theta;
} SphereParameters;

SphereModel :: SphereModel() {
	scale      = Parameter(1.0);
	radius     = Parameter(20.0, true);
	radius.set_min(0.0);
	sldSph   = Parameter(4.0e-6);
	sldSolv   = Parameter(1.0e-6);
	background = Parameter(0.0);
	M0_sld_sph = Parameter(0.0e-6);
	M_theta_sph = Parameter(0.0);
	M_phi_sph = Parameter(0.0); 
	M0_sld_solv = Parameter(0.0e-6);
	M_theta_solv = Parameter(0.0);
	M_phi_solv = Parameter(0.0); 
	Up_frac_i = Parameter(0.5); 
	Up_frac_f = Parameter(0.5);
	Up_theta = Parameter(0.0);
}

/**
 * Function to evaluate 1D scattering function
 * The NIST IGOR library is used for the actual calculation.
 * @param q: q-value
 * @return: function value
 */
double SphereModel :: operator()(double q) {
	double dp[5];

	// Fill parameter array for IGOR library
	// Add the background after averaging
	dp[0] = scale();
	dp[1] = radius();
	dp[2] = sldSph();
	dp[3] = sldSolv();
	dp[4] = 0.0;

	// Get the dispersion points for the radius
	vector<WeightPoint> weights_rad;
	radius.get_weights(weights_rad);

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;
	double vol = 0.0;

	// Loop over radius weight points
	for(size_t i=0; i<weights_rad.size(); i++) {
		dp[1] = weights_rad[i].value;

		//Un-normalize SphereForm by volume
		sum += weights_rad[i].weight
			* SphereForm(dp, q) * pow(weights_rad[i].value,3);
		//Find average volume
		vol += weights_rad[i].weight
			* pow(weights_rad[i].value,3);

		norm += weights_rad[i].weight;
	}

	if (vol != 0.0 && norm != 0.0) {
		//Re-normalize by avg volume
		sum = sum/(vol/norm);}
	return sum/norm + background();
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters
 * @param q: q-value
 * @param q_x: q_x / q
 * @param q_y: q_y / q
 * @return: function value
 */

static double sphere_analytical_2D_scaled(SphereParameters *pars, double q, double q_x, double q_y) {
	double dp[5];
	//convert angle degree to radian
	dp[0] = 1.0;
	dp[1] = pars->radius;
	dp[2] = 0.0;
	dp[3] = 0.0;
	dp[4] = 0.0;

    double sldSph = pars->sldSph;
    double sldSolv = pars->sldSolv;
	double answer = 0.0;
	double m_max = pars->M0_sld_sph;
	double m_max_solv = pars->M0_sld_solv;

	if (m_max < 1.0e-32 && m_max_solv < 1.0e-32){
		dp[2] = sldSph;
		dp[3] = sldSolv;
		answer = SphereForm(dp, q);
	}
	else{
		double contrast = sldSph - sldSolv;
		double qx = q_x;
		double qy = q_y;
		double s_theta = pars->Up_theta;
		double m_phi = pars->M_phi_sph;
		double m_theta = pars->M_theta_sph;
		double m_phi_solv = pars->M_phi_solv;
		double m_theta_solv = pars->M_theta_solv;
		double in_spin = pars->Up_frac_i;
		double out_spin = pars->Up_frac_f;
		polar_sld p_sld;
		polar_sld p_sld_solv;
		p_sld = cal_msld(1, qx, qy, sldSph, m_max, m_theta, m_phi, 
			 				in_spin, out_spin, s_theta);
		p_sld_solv = cal_msld(1, qx, qy, sldSolv, m_max_solv, m_theta_solv, m_phi_solv, 
								in_spin, out_spin, s_theta);
		//up_up	
		if (in_spin > 0.0 && out_spin > 0.0){			 
			dp[2] = p_sld.uu;
			dp[3] = p_sld_solv.uu;
			answer += SphereForm(dp, q);
			}
		//down_down
		if (in_spin < 1.0 && out_spin < 1.0){
			dp[2] = p_sld.dd;
			dp[3] = p_sld_solv.dd;
			answer += SphereForm(dp, q);
			}
		//up_down
		if (in_spin > 0.0 && out_spin < 1.0){
			dp[2] = p_sld.re_ud;
			dp[3] = p_sld_solv.re_ud;
			answer += SphereForm(dp, q);	
			dp[2] = p_sld.im_ud;
			dp[3] = p_sld_solv.im_ud;
			answer += SphereForm(dp, q);
			}
		//down_up	
		if (in_spin < 1.0 && out_spin > 0.0){
			dp[2] = p_sld.re_du;
			dp[3] = p_sld_solv.re_du;
			answer += SphereForm(dp, q);	
			dp[2] = p_sld.im_du;
			dp[3] = p_sld_solv.im_du;
			answer += SphereForm(dp, q);
			}
	}
	
	// add in the background
	answer *= pars->scale;
	answer += pars->background;
	return answer;
}


/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters
 * @param q: q-value
 * @return: function value
 */
static double sphere_analytical_2DXY(SphereParameters *pars, double qx, double qy) {
  double q;
  q = sqrt(qx*qx+qy*qy);
  return sphere_analytical_2D_scaled(pars, q, qx/q, qy/q);
}


/**
 * Function to evaluate 2D scattering function
 * @param q_x: value of Q along x
 * @param q_y: value of Q along y
 * @return: function value
 */
double SphereModel :: operator()(double qx, double qy) {
	SphereParameters dp;
	dp.scale = scale();
	dp.radius = radius();
	dp.sldSph = sldSph();
	dp.sldSolv = sldSolv();
	dp.background = 0.0;
	dp.Up_theta =  Up_theta();
	dp.M_phi_sph =  M_phi_sph();
	dp.M_theta_sph =  M_theta_sph();
	dp.M0_sld_sph =  M0_sld_sph();
	dp.M_phi_solv =  M_phi_solv();
	dp.M_theta_solv =  M_theta_solv();
	dp.M0_sld_solv =  M0_sld_solv();
	dp.Up_frac_i =  Up_frac_i();
	dp.Up_frac_f =  Up_frac_f();

	// Get the dispersion points for the radius
	vector<WeightPoint> weights_rad;
	radius.get_weights(weights_rad);

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;
	double vol = 0.0;

	// Loop over radius weight points
	for(size_t i=0; i<weights_rad.size(); i++) {
		dp.radius = weights_rad[i].value;

		//Un-normalize SphereForm by volume
		sum += weights_rad[i].weight
			* sphere_analytical_2DXY(&dp, qx, qy) * pow(weights_rad[i].value,3);
		//Find average volume
		vol += weights_rad[i].weight
			* pow(weights_rad[i].value,3);

		norm += weights_rad[i].weight;
	}

	if (vol != 0.0 && norm != 0.0) {
		//Re-normalize by avg volume
		sum = sum/(vol/norm);}
	return sum/norm + background();
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the sphere
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double SphereModel :: evaluate_rphi(double q, double phi) {
	double qx = q*cos(phi);
	double qy = q*sin(phi);
	return (*this).operator()(qx, qy);
}

/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double SphereModel :: calculate_ER() {
	double rad_out = 0.0;

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;

	// Get the dispersion points for the radius
	vector<WeightPoint> weights_rad;
	radius.get_weights(weights_rad);
	// Loop over radius weight points to average the radius value
	for(size_t i=0; i<weights_rad.size(); i++) {
		sum += weights_rad[i].weight
			* weights_rad[i].value;
		norm += weights_rad[i].weight;
	}
	if (norm != 0){
		//return the averaged value
		rad_out =  sum/norm;}
	else{
		//return normal value
		rad_out = radius();}

	return rad_out;
}
double SphereModel :: calculate_VR() {
  return 1.0;
}