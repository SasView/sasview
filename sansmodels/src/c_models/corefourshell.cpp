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
#include "corefourshell.h"

extern "C" {
	#include "libSphere.h"
	#include "libmultifunc/libfunc.h"
}

typedef struct {
  double scale;
  double rad_core0;
  double sld_core0;
  double thick_shell1;
  double sld_shell1;
  double thick_shell2;
  double sld_shell2;
  double thick_shell3;
  double sld_shell3;
  double thick_shell4;
  double sld_shell4;
  double sld_solv;
  double background;
  double M0_sld_shell1;
  double M_theta_shell1;
  double M_phi_shell1;
  double M0_sld_shell2;
  double M_theta_shell2;
  double M_phi_shell2;
  double M0_sld_shell3;
  double M_theta_shell3;
  double M_phi_shell3;
  double M0_sld_shell4;
  double M_theta_shell4;
  double M_phi_shell4;
  double M0_sld_core0;
  double M_theta_core0;
  double M_phi_core0;
  double M0_sld_solv;
  double M_theta_solv;
  double M_phi_solv;
  double Up_frac_i;
  double Up_frac_f;
  double Up_theta;
} CoreFourShellParameters;

CoreFourShellModel :: CoreFourShellModel() {
	scale      = Parameter(1.0);
	rad_core0     = Parameter(60.0, true);
	rad_core0.set_min(0.0);
	sld_core0   = Parameter(6.4e-6);
	thick_shell1     = Parameter(10.0, true);
	thick_shell1.set_min(0.0);
	sld_shell1   = Parameter(1.0e-6);
	thick_shell2     = Parameter(10.0, true);
	thick_shell2.set_min(0.0);
	sld_shell2   = Parameter(2.0e-6);
	thick_shell3     = Parameter(10.0, true);
	thick_shell3.set_min(0.0);
	sld_shell3   = Parameter(3.0e-6);
	thick_shell4     = Parameter(10.0, true);
	thick_shell4.set_min(0.0);
	sld_shell4   = Parameter(4.0e-6);
	sld_solv   = Parameter(6.4e-6);
	background = Parameter(0.001);
	M0_sld_shell1 = Parameter(0.0e-6);
	M_theta_shell1 = Parameter(0.0);
	M_phi_shell1 = Parameter(0.0);
	M0_sld_shell2 = Parameter(0.0e-6);
	M_theta_shell2 = Parameter(0.0);
	M_phi_shell2 = Parameter(0.0);
	M0_sld_shell3 = Parameter(0.0e-6);
	M_theta_shell3 = Parameter(0.0);
	M_phi_shell3 = Parameter(0.0);
	M0_sld_shell4 = Parameter(0.0e-6);
	M_theta_shell4 = Parameter(0.0);
	M_phi_shell4 = Parameter(0.0);
	M0_sld_core0 = Parameter(0.0e-6);
	M_theta_core0 = Parameter(0.0);
	M_phi_core0 = Parameter(0.0);
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
double CoreFourShellModel :: operator()(double q) {
	double dp[13];

	// Fill parameter array for IGOR library
	// Add the background after averaging

	dp[0] = scale();
	dp[1] = rad_core0();
	dp[2] = sld_core0();
	dp[3] = thick_shell1();
	dp[4] = sld_shell1();
	dp[5] = thick_shell2();
	dp[6] = sld_shell2();
	dp[7] = thick_shell3();
	dp[8] = sld_shell3();
	dp[9] = thick_shell4();
	dp[10] = sld_shell4();
	dp[11] = sld_solv();
	dp[12] = 0.0;

	// Get the dispersion points for the radius
	vector<WeightPoint> weights_rad;
	rad_core0.get_weights(weights_rad);

	// Get the dispersion points for the thick 1
	vector<WeightPoint> weights_s1;
	thick_shell1.get_weights(weights_s1);

	// Get the dispersion points for the thick 2
	vector<WeightPoint> weights_s2;
	thick_shell2.get_weights(weights_s2);

	// Get the dispersion points for the thick 3
	vector<WeightPoint> weights_s3;
	thick_shell3.get_weights(weights_s3);

	// Get the dispersion points for the thick 4
	vector<WeightPoint> weights_s4;
	thick_shell4.get_weights(weights_s4);

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;
	double vol = 0.0;

	// Loop over radius weight points
	for(size_t i=0; i<weights_rad.size(); i++) {
		dp[1] = weights_rad[i].value;
		// Loop over radius weight points
		for(size_t j=0; j<weights_s1.size(); j++) {
			dp[3] = weights_s1[j].value;
			// Loop over radius weight points
			for(size_t k=0; k<weights_s2.size(); k++) {
				dp[5] = weights_s2[k].value;
				// Loop over radius weight points
				for(size_t l=0; l<weights_s3.size(); l++) {
					dp[7] = weights_s3[l].value;
					// Loop over radius weight points
					for(size_t m=0; m<weights_s4.size(); m++) {
						dp[9] = weights_s4[m].value;
						//Un-normalize FourShell by volume
						sum += weights_rad[i].weight*weights_s1[j].weight*weights_s2[k].weight*weights_s3[l].weight*weights_s4[m].weight
							* FourShell(dp, q) * pow((weights_rad[i].value+weights_s1[j].value+weights_s2[k].value+weights_s3[l].value+weights_s4[m].value),3);
						//Find average volume
						vol += weights_rad[i].weight*weights_s1[j].weight*weights_s2[k].weight*weights_s3[l].weight*weights_s4[m].weight
							* pow((weights_rad[i].value+weights_s1[j].value+weights_s2[k].value+weights_s3[l].value+weights_s4[m].value),3);

						norm += weights_rad[i].weight*weights_s1[j].weight*weights_s2[k].weight*weights_s3[l].weight*weights_s4[m].weight;
					}
				}
			}
		}
	}

	if (vol != 0.0 && norm != 0.0) {
		//Re-normalize by avg volume
		sum = sum/(vol/norm);}
	return sum/norm + background();
}

/**
 * Function to evaluate 2D scattering function
 * @param q_x: value of Q along x
 * @param q_y: value of Q along y
 * @return: function value
 */

static double corefourshell_analytical_2D_scaled(CoreFourShellParameters *pars, double q, double q_x, double q_y) {
	double dp[13];

	// Fill parameter array for IGOR library
	// Add the background after averaging

	dp[0] = pars->scale;
	dp[1] = pars->rad_core0;
	dp[2] = 0.0; //sld_core0;
	dp[3] = pars->thick_shell1;
	dp[4] = 0.0; //sld_shell1;
	dp[5] = pars->thick_shell2;
	dp[6] = 0.0; //sld_shell2;
	dp[7] = pars->thick_shell3;
	dp[8] = 0.0; //sld_shell3;
	dp[9] = pars->thick_shell4;
	dp[10] = 0.0; //sld_shell4;
	dp[11] = 0.0; //sld_solv;
	dp[12] = 0.0;

    double sld_core0 = pars->sld_core0;
    double sld_shell1 = pars->sld_shell1;
	double sld_shell2 = pars->sld_shell2;
	double sld_shell3 = pars->sld_shell3;
	double sld_shell4 = pars->sld_shell4;
	double sld_solv = pars->sld_solv;
	double answer = 0.0;
	double m_max0 = pars->M0_sld_core0;
	double m_max_shell1 = pars->M0_sld_shell1;
	double m_max_shell2 = pars->M0_sld_shell2;
	double m_max_shell3 = pars->M0_sld_shell3;
	double m_max_shell4 = pars->M0_sld_shell4;
	double m_max_solv = pars->M0_sld_solv;

	if (m_max0 < 1.0e-32 && m_max_solv < 1.0e-32 && m_max_shell1 < 1.0e-32 && m_max_shell2 <
						1.0e-32 && m_max_shell3 < 1.0e-32 && m_max_shell4 < 1.0e-32){
		dp[2] = sld_core0;
		dp[4] = sld_shell1;
		dp[6] = sld_shell2;
		dp[8] = sld_shell3;
		dp[10] = sld_shell4;
		dp[11] = sld_solv;
		answer = FourShell(dp, q);
	}
	else{
		double qx = q_x;
		double qy = q_y;
		double s_theta = pars->Up_theta;
		double m_phi0 = pars->M_phi_core0;
		double m_theta0 = pars->M_theta_core0;
		double m_phi_shell1 = pars->M_phi_shell1;
		double m_theta_shell1 = pars->M_theta_shell1;
		double m_phi_shell2 = pars->M_phi_shell2;
		double m_theta_shell2 = pars->M_theta_shell2;
		double m_phi_shell3 = pars->M_phi_shell3;
		double m_theta_shell3 = pars->M_theta_shell3;
		double m_phi_shell4 = pars->M_phi_shell4;
		double m_theta_shell4 = pars->M_theta_shell4;
		double m_phi_solv = pars->M_phi_solv;
		double m_theta_solv = pars->M_theta_solv;
		double in_spin = pars->Up_frac_i;
		double out_spin = pars->Up_frac_f;
		polar_sld p_sld_core0;
		polar_sld p_sld_shell1;
		polar_sld p_sld_shell2;
		polar_sld p_sld_shell3;
		polar_sld p_sld_shell4;
		polar_sld p_sld_solv;
		//Find (b+m) slds
		p_sld_core0 = cal_msld(1, qx, qy, sld_core0, m_max0, m_theta0, m_phi0,
								in_spin, out_spin, s_theta);
		p_sld_shell1 = cal_msld(1, qx, qy, sld_shell1, m_max_shell1, m_theta_shell1, m_phi_shell1,
								in_spin, out_spin, s_theta);
		p_sld_shell2 = cal_msld(1, qx, qy, sld_shell2, m_max_shell2, m_theta_shell2, m_phi_shell2,
								in_spin, out_spin, s_theta);
		p_sld_shell3 = cal_msld(1, qx, qy, sld_shell3, m_max_shell3, m_theta_shell3, m_phi_shell3,
								in_spin, out_spin, s_theta);
		p_sld_shell4 = cal_msld(1, qx, qy, sld_shell4, m_max_shell4, m_theta_shell4, m_phi_shell4,
								in_spin, out_spin, s_theta);
		p_sld_solv = cal_msld(1, qx, qy, sld_solv, m_max_solv, m_theta_solv, m_phi_solv,
						 		in_spin, out_spin, s_theta);
		//up_up
		if (in_spin > 0.0 && out_spin > 0.0){
			dp[2] = p_sld_core0.uu;
			dp[4] = p_sld_shell1.uu;
			dp[6] = p_sld_shell2.uu;
			dp[8] = p_sld_shell3.uu;
			dp[10] = p_sld_shell4.uu;
			dp[11] = p_sld_solv.uu;
			answer += FourShell(dp, q);
			}
		//down_down
		if (in_spin < 1.0 && out_spin < 1.0){
			dp[2] = p_sld_core0.dd;
			dp[4] = p_sld_shell1.dd;
			dp[6] = p_sld_shell2.dd;
			dp[8] = p_sld_shell3.dd;
			dp[10] = p_sld_shell4.dd;
			dp[11] = p_sld_solv.dd;
			answer += FourShell(dp, q);
			}
		//up_down
		if (in_spin > 0.0 && out_spin < 1.0){
			dp[2] = p_sld_core0.re_ud;
			dp[4] = p_sld_shell1.re_ud;
			dp[6] = p_sld_shell2.re_ud;
			dp[8] = p_sld_shell3.re_ud;
			dp[10] = p_sld_shell4.re_ud;
			dp[11] = p_sld_solv.re_ud;
			answer += FourShell(dp, q);
			dp[2] = p_sld_core0.im_ud;
			dp[4] = p_sld_shell1.im_ud;
			dp[6] = p_sld_shell2.im_ud;
			dp[8] = p_sld_shell3.im_ud;
			dp[10] = p_sld_shell4.im_ud;
			dp[11] = p_sld_solv.im_ud;
			answer += FourShell(dp, q);
			}
		//down_up
		if (in_spin < 1.0 && out_spin > 0.0){
			dp[2] = p_sld_core0.re_du;
			dp[4] = p_sld_shell1.re_du;
			dp[6] = p_sld_shell2.re_du;
			dp[8] = p_sld_shell3.re_du;
			dp[10] = p_sld_shell4.re_du;
			dp[11] = p_sld_solv.re_du;
			answer += FourShell(dp, q);
			dp[2] = p_sld_core0.im_du;
			dp[4] = p_sld_shell1.im_du;
			dp[6] = p_sld_shell2.im_du;
			dp[8] = p_sld_shell3.im_du;
			dp[10] = p_sld_shell4.im_du;
			dp[11] = p_sld_solv.im_du;
			answer += FourShell(dp, q);
			}
	}
	// Already normalized
	// add in the background
	answer += pars->background;
	return answer;
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters
 * @param q: q-value
 * @return: function value
 */
static double corefourshell_analytical_2DXY(CoreFourShellParameters *pars, double qx, double qy) {
  double q;
  q = sqrt(qx*qx+qy*qy);
  return corefourshell_analytical_2D_scaled(pars, q, qx/q, qy/q);
}


double CoreFourShellModel :: operator()(double qx, double qy) {
	CoreFourShellParameters dp;
	dp.scale = scale();
	dp.rad_core0 = rad_core0();
	dp.sld_core0 = sld_core0();
	dp.thick_shell1 = thick_shell1();
	dp.sld_shell1 = sld_shell1();
	dp.thick_shell2 = thick_shell2();
	dp.sld_shell2 = sld_shell2();
	dp.thick_shell3 = thick_shell3();
	dp.sld_shell3 = sld_shell3();
	dp.thick_shell4 = thick_shell4();
	dp.sld_shell4 = sld_shell4();
	dp.sld_solv = sld_solv();
	dp.background = 0.0;
	dp.M0_sld_shell1 = M0_sld_shell1();
	dp.M_theta_shell1 = M_theta_shell1();
	dp.M_phi_shell1 = M_phi_shell1();
	dp.M0_sld_shell2 = M0_sld_shell2();
	dp.M_theta_shell2 = M_theta_shell2();
	dp.M_phi_shell2 = M_phi_shell2();
	dp.M0_sld_shell3 = M0_sld_shell3();
	dp.M_theta_shell3 = M_theta_shell3();
	dp.M_phi_shell3 = M_phi_shell3();
	dp.M0_sld_shell4 = M0_sld_shell4();
	dp.M_theta_shell4 = M_theta_shell4();
	dp.M_phi_shell4 = M_phi_shell4();
	dp.M0_sld_core0 = M0_sld_core0();
	dp.M_theta_core0 = M_theta_core0();
	dp.M_phi_core0 = M_phi_core0();
	dp.M0_sld_solv = M0_sld_solv();
	dp.M_theta_solv = M_theta_solv();
	dp.M_phi_solv = M_phi_solv();
	dp.Up_frac_i = Up_frac_i();
	dp.Up_frac_f = Up_frac_f();
	dp.Up_theta = Up_theta();
    
	// Get the dispersion points for the radius
	vector<WeightPoint> weights_rad;
	rad_core0.get_weights(weights_rad);

	// Get the dispersion points for the thick 1
	vector<WeightPoint> weights_s1;
	thick_shell1.get_weights(weights_s1);

	// Get the dispersion points for the thick 2
	vector<WeightPoint> weights_s2;
	thick_shell2.get_weights(weights_s2);

	// Get the dispersion points for the thick 3
	vector<WeightPoint> weights_s3;
	thick_shell3.get_weights(weights_s3);

	// Get the dispersion points for the thick 4
	vector<WeightPoint> weights_s4;
	thick_shell4.get_weights(weights_s4);

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;
	double vol = 0.0;

	// Loop over radius weight points
	for(size_t i=0; i<weights_rad.size(); i++) {
		dp.rad_core0 = weights_rad[i].value;
		// Loop over radius weight points
		for(size_t j=0; j<weights_s1.size(); j++) {
			dp.thick_shell1 = weights_s1[j].value;
			// Loop over radius weight points
			for(size_t k=0; k<weights_s2.size(); k++) {
				dp.thick_shell2 = weights_s2[k].value;
				// Loop over radius weight points
				for(size_t l=0; l<weights_s3.size(); l++) {
					dp.thick_shell3 = weights_s3[l].value;
					// Loop over radius weight points
					for(size_t m=0; m<weights_s4.size(); m++) {
						dp.thick_shell4 = weights_s4[m].value;
						//Un-normalize FourShell by volume
						sum += weights_rad[i].weight*weights_s1[j].weight*weights_s2[k].weight*weights_s3[l].weight*weights_s4[m].weight
							* corefourshell_analytical_2DXY(&dp, qx, qy) * pow((weights_rad[i].value+weights_s1[j].value+weights_s2[k].value+weights_s3[l].value+weights_s4[m].value),3);
						//Find average volume
						vol += weights_rad[i].weight*weights_s1[j].weight*weights_s2[k].weight*weights_s3[l].weight*weights_s4[m].weight
							* pow((weights_rad[i].value+weights_s1[j].value+weights_s2[k].value+weights_s3[l].value+weights_s4[m].value),3);

						norm += weights_rad[i].weight*weights_s1[j].weight*weights_s2[k].weight*weights_s3[l].weight*weights_s4[m].weight;
					}
				}
			}
		}
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
double CoreFourShellModel :: evaluate_rphi(double q, double phi) {
	double qx = q*cos(phi);
	double qy = q*sin(phi);
	return (*this).operator()(qx, qy);
}

/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double CoreFourShellModel :: calculate_ER() {
	CoreFourShellParameters dp;

	dp.scale = scale();
	dp.rad_core0 = rad_core0();
	dp.sld_core0 = sld_core0();
	dp.thick_shell1 = thick_shell1();
	dp.sld_shell1 = sld_shell1();
	dp.thick_shell2 = thick_shell2();
	dp.sld_shell2 = sld_shell2();
	dp.thick_shell3 = thick_shell3();
	dp.sld_shell3 = sld_shell3();
	dp.thick_shell4 = thick_shell4();
	dp.sld_shell4 = sld_shell4();
	dp.sld_solv = sld_solv();
	dp.background = 0.0;

	// Get the dispersion points for the radius
	vector<WeightPoint> weights_rad;
	rad_core0.get_weights(weights_rad);

	// Get the dispersion points for the thick 1
	vector<WeightPoint> weights_s1;
	thick_shell1.get_weights(weights_s1);

	// Get the dispersion points for the thick 2
	vector<WeightPoint> weights_s2;
	thick_shell2.get_weights(weights_s2);

	// Get the dispersion points for the thick 3
	vector<WeightPoint> weights_s3;
	thick_shell3.get_weights(weights_s3);

	// Get the dispersion points for the thick 4
	vector<WeightPoint> weights_s4;
	thick_shell4.get_weights(weights_s4);

	double rad_out = 0.0;
	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;

	// Loop over radius weight points
	for(size_t i=0; i<weights_rad.size(); i++) {
		dp.rad_core0 = weights_rad[i].value;
		// Loop over radius weight points
		for(size_t j=0; j<weights_s1.size(); j++) {
			dp.thick_shell1 = weights_s1[j].value;
			// Loop over radius weight points
			for(size_t k=0; k<weights_s2.size(); k++) {
				dp.thick_shell2 = weights_s2[k].value;
				// Loop over radius weight points
				for(size_t l=0; l<weights_s3.size(); l++) {
					dp.thick_shell3 = weights_s3[l].value;
					// Loop over radius weight points
					for(size_t m=0; m<weights_s4.size(); m++) {
						dp.thick_shell4 = weights_s4[m].value;
						//Un-normalize FourShell by volume
						sum += weights_rad[i].weight*weights_s1[j].weight*weights_s2[k].weight*weights_s3[l].weight*weights_s4[m].weight
							* (dp.rad_core0+dp.thick_shell1+dp.thick_shell2+dp.thick_shell3+dp.thick_shell4);
						norm += weights_rad[i].weight*weights_s1[j].weight*weights_s2[k].weight*weights_s3[l].weight*weights_s4[m].weight;
					}
				}
			}
		}
	}
	if (norm != 0){
		//return the averaged value
		rad_out =  sum/norm;}
	else{
		//return normal value
		rad_out = dp.rad_core0+dp.thick_shell1+dp.thick_shell2+dp.thick_shell3+dp.thick_shell4;}

	return rad_out;
}
double CoreFourShellModel :: calculate_VR() {
  return 1.0;
}
