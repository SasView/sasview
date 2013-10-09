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

extern "C" {
	#include "libCylinder.h"
	#include "libStructureFactor.h"
	#include "libmultifunc/libfunc.h"
}
#include "cylinder.h"

// Convenience parameter structure
typedef struct {
    double scale;
    double radius;
    double length;
    double sldCyl;
    double sldSolv;
    double background;
    double cyl_theta;
    double cyl_phi;
    double M0_sld_cyl;
    double M_theta_cyl;
    double M_phi_cyl;
    double M0_sld_solv;
    double M_theta_solv;
    double M_phi_solv;
    double Up_frac_i;
	double Up_frac_f;
	double Up_theta;
} CylinderParameters;

CylinderModel :: CylinderModel() {
	scale      = Parameter(1.0);
	radius     = Parameter(20.0, true);
	radius.set_min(0.0);
	length     = Parameter(400.0, true);
	length.set_min(0.0);
	sldCyl   = Parameter(4.e-6);
	sldSolv   = Parameter(1.e-6);
	background = Parameter(0.0);
	cyl_theta  = Parameter(0.0, true);
	cyl_phi    = Parameter(0.0, true);
	M0_sld_cyl = Parameter(0.0e-6);
	M_theta_cyl = Parameter(0.0);
	M_phi_cyl = Parameter(0.0); 
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
double CylinderModel :: operator()(double q) {
	double dp[6];

	// Fill parameter array for IGOR library
	// Add the background after averaging
	dp[0] = scale();
	dp[1] = radius();
	dp[2] = length();
	dp[3] = sldCyl();
	dp[4] = sldSolv();
	dp[5] = 0.0;

	// Get the dispersion points for the radius
	vector<WeightPoint> weights_rad;
	radius.get_weights(weights_rad);

	// Get the dispersion points for the length
	vector<WeightPoint> weights_len;
	length.get_weights(weights_len);

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;
	double vol = 0.0;

	// Loop over radius weight points
	for(size_t i=0; i<weights_rad.size(); i++) {
		dp[1] = weights_rad[i].value;

		// Loop over length weight points
		for(size_t j=0; j<weights_len.size(); j++) {
			dp[2] = weights_len[j].value;
			//Un-normalize by volume
			sum += weights_rad[i].weight
				* weights_len[j].weight * CylinderForm(dp, q)
				*pow(weights_rad[i].value,2)*weights_len[j].value;

			//Find average volume
			vol += weights_rad[i].weight
				* weights_len[j].weight *pow(weights_rad[i].value,2)*weights_len[j].value;
			norm += weights_rad[i].weight
				* weights_len[j].weight;
		}
	}
	if (vol != 0.0 && norm != 0.0) {
		//Re-normalize by avg volume
		sum = sum/(vol/norm);}

	return sum/norm + background();
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the cylinder
 * @param q: q-value
 * @param q_x: q_x / q
 * @param q_y: q_y / q
 * @return: function value
 */
static double cylinder_analytical_2D_scaled(CylinderParameters *pars, double q, double q_x, double q_y) {
    double cyl_x, cyl_y;//, cyl_z;
    //double q_z;
    double alpha, vol, cos_val;
    double answer = 0.0;
    double form = 0.0;
    //convert angle degree to radian
    double pi = 4.0*atan(1.0);
    double theta = pars->cyl_theta * pi/180.0;
    double phi = pars->cyl_phi * pi/180.0;
    double sld_solv = pars->sldSolv;
    double sld_cyl = pars->sldCyl;
    double m_max = pars->M0_sld_cyl;
    double m_max_solv = pars->M0_sld_solv;
    double contrast = 0.0;

    // Cylinder orientation
	cyl_x = cos(theta) * cos(phi);
    cyl_y = sin(theta);
    //cyl_z = -cos(theta) * sin(phi);
    // q vector
    //q_z = 0.0;

    // Compute the angle btw vector q and the
    // axis of the cylinder
    cos_val = cyl_x*q_x + cyl_y*q_y;// + cyl_z*q_z;

    // The following test should always pass
    if (fabs(cos_val)>1.0) {
      printf("cyl_ana_2D: Unexpected error: |cos(alpha)=%g|>1\n", cos_val);
      printf("cyl_ana_2D: at theta=%g and phi=%g.", theta, phi);
      return 1.0;
    }

    // Note: cos(alpha) = 0 and 1 will get an
    // undefined value from CylKernel
  alpha = acos( cos_val );
  if (alpha == 0.0){
  	alpha = 1.0e-26;
  	}
  // Call the IGOR library function to get the kernel
  //answer = CylKernel(q, pars->radius, pars->length/2.0, alpha) / sin(alpha);

    // Call the IGOR library function to get the kernel
    form = CylKernel(q, pars->radius, pars->length/2.0, alpha) / sin(alpha);

	if (m_max < 1.0e-32 && m_max_solv < 1.0e-32){
		// Multiply by contrast^2
		contrast = (pars->sldCyl - pars->sldSolv);
  		answer = contrast * contrast * form;
	}
	else{
		double qx = q_x;
		double qy = q_y;
		double s_theta = pars->Up_theta;
		double m_phi = pars->M_phi_cyl;
		double m_theta = pars->M_theta_cyl;
		double m_phi_solv = pars->M_phi_solv;
		double m_theta_solv = pars->M_theta_solv;
		double in_spin = pars->Up_frac_i;
		double out_spin = pars->Up_frac_f;
		polar_sld p_sld;
		polar_sld p_sld_solv;
		p_sld = cal_msld(1, qx, qy, sld_cyl, m_max, m_theta, m_phi, 
			 			in_spin, out_spin, s_theta);
		p_sld_solv = cal_msld(1, qx, qy, sld_solv, m_max_solv, m_theta_solv, m_phi_solv, 
			 			in_spin, out_spin, s_theta);
		//up_up	
		if (in_spin > 0.0 && out_spin > 0.0){			 
			answer += ((p_sld.uu- p_sld_solv.uu) * (p_sld.uu- p_sld_solv.uu) * form);
			}
		//down_down
		if (in_spin < 1.0 && out_spin < 1.0){
			answer += ((p_sld.dd - p_sld_solv.dd) * (p_sld.dd - p_sld_solv.dd) * form);
			}
		//up_down
		if (in_spin > 0.0 && out_spin < 1.0){
			answer += ((p_sld.re_ud - p_sld_solv.re_ud) * (p_sld.re_ud - p_sld_solv.re_ud) * form);
			answer += ((p_sld.im_ud - p_sld_solv.im_ud) * (p_sld.im_ud - p_sld_solv.im_ud) * form);
			}
		//down_up	
		if (in_spin < 1.0 && out_spin > 0.0){
			answer += ((p_sld.re_du - p_sld_solv.re_du) * (p_sld.re_du - p_sld_solv.re_du) * form);
			answer += ((p_sld.im_du - p_sld_solv.im_du) * (p_sld.im_du - p_sld_solv.im_du) * form);
			}
	}

    //normalize by cylinder volume
    //NOTE that for this (Fournet) definition of the integral, one must MULTIPLY by Vcyl
    vol = acos(-1.0) * pars->radius * pars->radius * pars->length;
    answer *= vol;

    //convert to [cm-1]
    answer *= 1.0e8;

    //Scale
    answer *= pars->scale;

    // add in the background
    answer += pars->background;

    return answer;
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the cylinder
 * @param q: q-value
 * @return: function value
 */
static double cylinder_analytical_2DXY(CylinderParameters *pars, double qx, double qy) {
  double q;
  q = sqrt(qx*qx+qy*qy);
  return cylinder_analytical_2D_scaled(pars, q, qx/q, qy/q);
}

/**
 * Function to evaluate 2D scattering function
 * @param q_x: value of Q along x
 * @param q_y: value of Q along y
 * @return: function value
 */
double CylinderModel :: operator()(double qx, double qy) {
	CylinderParameters dp;
	// Fill parameter array
	dp.scale      = scale();
	dp.radius     = radius();
	dp.length     = length();
	dp.sldCyl   = sldCyl();
	dp.sldSolv   = sldSolv();
	dp.background = 0.0;
	dp.cyl_theta  = cyl_theta();
	dp.cyl_phi    = cyl_phi();
	dp.Up_theta =  Up_theta();
	dp.M_phi_cyl =  M_phi_cyl();
	dp.M_theta_cyl =  M_theta_cyl();
	dp.M0_sld_cyl =  M0_sld_cyl();
	dp.M_phi_solv =  M_phi_solv();
	dp.M_theta_solv =  M_theta_solv();
	dp.M0_sld_solv =  M0_sld_solv();
	dp.Up_frac_i =  Up_frac_i();
	dp.Up_frac_f =  Up_frac_f();
	
	// Get the dispersion points for the radius
	vector<WeightPoint> weights_rad;
	radius.get_weights(weights_rad);

	// Get the dispersion points for the length
	vector<WeightPoint> weights_len;
	length.get_weights(weights_len);

	// Get angular averaging for theta
	vector<WeightPoint> weights_theta;
	cyl_theta.get_weights(weights_theta);

	// Get angular averaging for phi
	vector<WeightPoint> weights_phi;
	cyl_phi.get_weights(weights_phi);

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;
	double norm_vol = 0.0;
	double vol = 0.0;
	double pi = 4.0*atan(1.0);
	// Loop over radius weight points
	for(size_t i=0; i<weights_rad.size(); i++) {
		dp.radius = weights_rad[i].value;


		// Loop over length weight points
		for(size_t j=0; j<weights_len.size(); j++) {
			dp.length = weights_len[j].value;

			// Average over theta distribution
			for(size_t k=0; k<weights_theta.size(); k++) {
				dp.cyl_theta = weights_theta[k].value;

				// Average over phi distribution
				for(size_t l=0; l<weights_phi.size(); l++) {
					dp.cyl_phi = weights_phi[l].value;
					//Un-normalize by volume
					double _ptvalue = weights_rad[i].weight
						* weights_len[j].weight
						* weights_theta[k].weight
						* weights_phi[l].weight
						* cylinder_analytical_2DXY(&dp, qx, qy)
						*pow(weights_rad[i].value,2)*weights_len[j].value;
					if (weights_theta.size()>1) {
						_ptvalue *= fabs(cos(weights_theta[k].value*pi/180.0));
					}
					sum += _ptvalue;
					//Find average volume
					vol += weights_rad[i].weight
							* weights_len[j].weight
							* pow(weights_rad[i].value,2)*weights_len[j].value;
					//Find norm for volume
					norm_vol += weights_rad[i].weight
							* weights_len[j].weight;

					norm += weights_rad[i].weight
						* weights_len[j].weight
						* weights_theta[k].weight
						* weights_phi[l].weight;

				}
			}
		}
	}
	// Averaging in theta needs an extra normalization
	// factor to account for the sin(theta) term in the
	// integration (see documentation).
	if (weights_theta.size()>1) norm = norm / asin(1.0);
	if (vol != 0.0 && norm_vol != 0.0) {
		//Re-normalize by avg volume
		sum = sum/(vol/norm_vol);}

	return sum/norm + background();
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the cylinder
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double CylinderModel :: evaluate_rphi(double q, double phi) {
	double qx = q*cos(phi);
	double qy = q*sin(phi);
	return (*this).operator()(qx, qy);
}
/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double CylinderModel :: calculate_ER() {
	CylinderParameters dp;

	dp.radius     = radius();
	dp.length     = length();
	double rad_out = 0.0;

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;

	// Get the dispersion points for the major shell
	vector<WeightPoint> weights_length;
	length.get_weights(weights_length);

	// Get the dispersion points for the minor shell
	vector<WeightPoint> weights_radius ;
	radius.get_weights(weights_radius);

	// Loop over major shell weight points
	for(int i=0; i< (int)weights_length.size(); i++) {
		dp.length = weights_length[i].value;
		for(int k=0; k< (int)weights_radius.size(); k++) {
			dp.radius = weights_radius[k].value;
			//Note: output of "DiamCyl(dp.length,dp.radius)" is DIAMETER.
			sum +=weights_length[i].weight
				* weights_radius[k].weight*DiamCyl(dp.length,dp.radius)/2.0;
			norm += weights_length[i].weight* weights_radius[k].weight;
		}
	}
	if (norm != 0){
		//return the averaged value
		rad_out =  sum/norm;}
	else{
		//return normal value
		//Note: output of "DiamCyl(dp.length,dp.radius)" is DIAMETER.
		rad_out = DiamCyl(dp.length,dp.radius)/2.0;}

	return rad_out;
}
double CylinderModel :: calculate_VR() {
  return 1.0;
}
