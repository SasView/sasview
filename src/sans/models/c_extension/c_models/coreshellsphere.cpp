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
#include "core_shell.h"

extern "C" {
#include "libSphere.h"
#include "libmultifunc/libfunc.h"
}

typedef struct {
  double scale;
  double radius;
  double thickness;
  double core_sld;
  double shell_sld;
  double solvent_sld;
  double background;
  double M0_sld_shell;
  double M_theta_shell;
  double M_phi_shell;
  double M0_sld_core;
  double M_theta_core;
  double M_phi_core;
  double M0_sld_solv;
  double M_theta_solv;
  double M_phi_solv;
  double Up_frac_i;
  double Up_frac_f;
  double Up_theta;
} CoreShellParameters;

CoreShellModel :: CoreShellModel() {
  scale      = Parameter(1.0);
  radius     = Parameter(60.0, true);
  radius.set_min(0.0);
  thickness  = Parameter(10.0, true);
  thickness.set_min(0.0);
  core_sld   = Parameter(1.e-6);
  shell_sld  = Parameter(2.e-6);
  solvent_sld = Parameter(3.e-6);
  background = Parameter(0.0);
  M0_sld_shell = Parameter(0.0e-6);
  M_theta_shell = Parameter(0.0);
  M_phi_shell = Parameter(0.0);
  M0_sld_core = Parameter(0.0e-6);
  M_theta_core = Parameter(0.0);
  M_phi_core = Parameter(0.0);
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
double CoreShellModel :: operator()(double q) {
  double dp[7];

  // Fill parameter array for IGOR library
  // Add the background after averaging

  dp[0] = scale();
  dp[1] = radius();
  dp[2] = thickness();
  dp[3] = core_sld();
  dp[4] = shell_sld();
  dp[5] = solvent_sld();
  dp[6] = 0.0;

  //im
  ///dp[7] = 0.0;
  ///dp[8] = 0.0;
  ///dp[9] = 0.0;

  // Get the dispersion points for the radius
  vector<WeightPoint> weights_rad;
  radius.get_weights(weights_rad);

  // Get the dispersion points for the thickness
  vector<WeightPoint> weights_thick;
  thickness.get_weights(weights_thick);

  // Perform the computation, with all weight points
  double sum = 0.0;
  double norm = 0.0;
  double vol = 0.0;

  // Loop over radius weight points
  for(size_t i=0; i<weights_rad.size(); i++) {
    dp[1] = weights_rad[i].value;

    // Loop over thickness weight points
    for(size_t j=0; j<weights_thick.size(); j++) {
      dp[2] = weights_thick[j].value;
      //Un-normalize SphereForm by volume
      sum += weights_rad[i].weight
          * weights_thick[j].weight * CoreShellForm(dp, q)* pow(weights_rad[i].value+weights_thick[j].value,3);

      //Find average volume
      vol += weights_rad[i].weight * weights_thick[j].weight
          * pow(weights_rad[i].value+weights_thick[j].value,3);
      norm += weights_rad[i].weight
          * weights_thick[j].weight;
    }
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

static double coreshell_analytical_2D_scaled(CoreShellParameters *pars, double q, double q_x, double q_y) {
	double dp[7];
	//convert angle degree to radian
	dp[0] = pars->scale;
	dp[1] = pars->radius;
	dp[2] = pars->thickness;
	dp[3] = 0.0;
	dp[4] = 0.0;
	dp[5] = 0.0;
	dp[6] = 0.0;
	//im
	///dp[7] = 0.0;
	///dp[8] = 0.0;
	///dp[9] = 0.0;

    double sld_core = pars->core_sld;
    double sld_shell = pars->shell_sld;
	double sld_solv = pars->solvent_sld;
	double answer = 0.0;
	double m_max = pars->M0_sld_core;
	double m_max_shell = pars->M0_sld_shell;
	double m_max_solv = pars->M0_sld_solv;

	if (m_max < 1.0e-32 && m_max_solv < 1.0e-32 && m_max_shell < 1.0e-32){
		dp[3] = sld_core;
		dp[4] = sld_shell;
		dp[5] = sld_solv;
		answer = CoreShellForm(dp, q);
	}
	else{
		double qx = q_x;
		double qy = q_y;
		double s_theta = pars->Up_theta;
		double m_phi = pars->M_phi_core;
		double m_theta = pars->M_theta_core;
		double m_phi_shell = pars->M_phi_shell;
		double m_theta_shell = pars->M_theta_shell;
		double m_phi_solv = pars->M_phi_solv;
		double m_theta_solv = pars->M_theta_solv;
		double in_spin = pars->Up_frac_i;
		double out_spin = pars->Up_frac_f;
		polar_sld p_sld_core;
		polar_sld p_sld_shell;
		polar_sld p_sld_solv;
		//Find (b+m) slds
		p_sld_core = cal_msld(1, qx, qy, sld_core, m_max, m_theta, m_phi,
								in_spin, out_spin, s_theta);
		p_sld_shell = cal_msld(1, qx, qy, sld_shell, m_max_shell, m_theta_shell, m_phi_shell,
								in_spin, out_spin, s_theta);
		p_sld_solv = cal_msld(1, qx, qy, sld_solv, m_max_solv, m_theta_solv, m_phi_solv,
						 		in_spin, out_spin, s_theta);
		//up_up
		if (in_spin > 0.0 && out_spin > 0.0){
			dp[3] = p_sld_core.uu;
			dp[4] = p_sld_shell.uu;
			dp[5] = p_sld_solv.uu;
			answer += CoreShellForm(dp, q);
			}
		//down_down
		if (in_spin < 1.0 && out_spin < 1.0){
			dp[3] = p_sld_core.dd;
			dp[4] = p_sld_shell.dd;
			dp[5] = p_sld_solv.dd;
			answer += CoreShellForm(dp, q);
			}
		//up_down
		if (in_spin > 0.0 && out_spin < 1.0){
			dp[3] = p_sld_core.re_ud;
			dp[4] = p_sld_shell.re_ud;
			dp[5] = p_sld_solv.re_ud;
			answer += CoreShellForm(dp, q);
			dp[3] = p_sld_core.im_ud;
			dp[4] = p_sld_shell.im_ud;
			dp[5] = p_sld_solv.im_ud;
			answer += CoreShellForm(dp, q);
			}
		//down_up
		if (in_spin < 1.0 && out_spin > 0.0){
			dp[3] = p_sld_core.re_du;
			dp[4] = p_sld_shell.re_du;
			dp[5] = p_sld_solv.re_du;
			answer += CoreShellForm(dp, q);
			dp[3] = p_sld_core.im_du;
			dp[4] = p_sld_shell.im_du;
			dp[5] = p_sld_solv.im_du;
			answer += CoreShellForm(dp, q);
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
static double coreshell_analytical_2DXY(CoreShellParameters *pars, double qx, double qy) {
  double q;
  q = sqrt(qx*qx+qy*qy);
  return coreshell_analytical_2D_scaled(pars, q, qx/q, qy/q);
}


/**
 * Function to evaluate 2D scattering function
 * @param q_x: value of Q along x
 * @param q_y: value of Q along y
 * @return: function value
 */
double CoreShellModel :: operator()(double qx, double qy) {
	CoreShellParameters dp;
    dp.scale = scale();
    dp.radius = radius();
    dp.thickness = thickness();
    dp.core_sld = core_sld();
    dp.shell_sld = shell_sld();
    dp.solvent_sld = solvent_sld();
    dp.background = 0.0;
    dp.M0_sld_shell = M0_sld_shell();
    dp.M_theta_shell = M_theta_shell();
    dp.M_phi_shell = M_phi_shell();
    dp.M0_sld_core = M0_sld_core();
    dp.M_theta_core = M_theta_core();
    dp.M_phi_core = M_phi_core();
    dp.M0_sld_solv = M0_sld_solv();
    dp.M_theta_solv = M_theta_solv();
    dp.M_phi_solv = M_phi_solv();
    dp.Up_frac_i = Up_frac_i();
    dp.Up_frac_f = Up_frac_f();
    dp.Up_theta = Up_theta();

	// Get the dispersion points for the radius
	vector<WeightPoint> weights_rad;
	radius.get_weights(weights_rad);

	// Get the dispersion points for the thickness
	vector<WeightPoint> weights_thick;
	thickness.get_weights(weights_thick);

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;
	double vol = 0.0;

	// Loop over radius weight points
	for(size_t i=0; i<weights_rad.size(); i++) {
	dp.radius = weights_rad[i].value;

	// Loop over thickness weight points
	for(size_t j=0; j<weights_thick.size(); j++) {
	  dp.thickness = weights_thick[j].value;
	  //Un-normalize SphereForm by volume
	  sum += weights_rad[i].weight
		  * weights_thick[j].weight * coreshell_analytical_2DXY(&dp, qx, qy) *
		  	pow(weights_rad[i].value+weights_thick[j].value,3);

	  //Find average volume
	  vol += weights_rad[i].weight * weights_thick[j].weight
		  * pow(weights_rad[i].value+weights_thick[j].value,3);
	  norm += weights_rad[i].weight
		  * weights_thick[j].weight;
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
double CoreShellModel :: evaluate_rphi(double q, double phi) {
	double qx = q*cos(phi);
	double qy = q*sin(phi);
	return (*this).operator()(qx, qy);
}
/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double CoreShellModel :: calculate_ER() {
  CoreShellParameters dp;

  dp.radius     = radius();
  dp.thickness  = thickness();

  double rad_out = 0.0;

  // Perform the computation, with all weight points
  double sum = 0.0;
  double norm = 0.0;


  // Get the dispersion points for the major shell
  vector<WeightPoint> weights_thickness;
  thickness.get_weights(weights_thickness);

  // Get the dispersion points for the minor shell
  vector<WeightPoint> weights_radius ;
  radius.get_weights(weights_radius);

  // Loop over major shell weight points
  for(int j=0; j< (int)weights_thickness.size(); j++) {
    dp.thickness = weights_thickness[j].value;
    for(int k=0; k< (int)weights_radius.size(); k++) {
      dp.radius = weights_radius[k].value;
      sum += weights_thickness[j].weight
          * weights_radius[k].weight*(dp.radius+dp.thickness);
      norm += weights_thickness[j].weight* weights_radius[k].weight;
    }
  }
  if (norm != 0){
    //return the averaged value
    rad_out =  sum/norm;}
  else{
    //return normal value
    rad_out = (dp.radius+dp.thickness);}

  return rad_out;
}
double CoreShellModel :: calculate_VR() {
  return 1.0;
}
