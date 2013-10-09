/**
 * Scattering model classes
 *
 */

#include <math.h>
#include "parameters.hh"
#include <stdio.h>
using namespace std;
#include "coresecondmoment.h"

static double core_secondmoment_kernel(double dp[], double q) {
  //fit parameters
  double scale = dp[0];
  double density_poly = dp[1];
  double sld_poly = dp[2];
  double radius_core = dp[3];
  double volf_cores = dp[4];
  double ads_amount = dp[5];
  double second_moment = dp[6];
  double sld_solv = dp[7];
  double background = dp[8];
  // Not valid for very small r
  if (radius_core < 0.001){
	  return 0.0;
  }
  //others
  double form_factor = 0.0;
  double x_val = 0.0;
  //Pi
  double pi = 4.0 * atan(1.0);
  //relative sld
  double contrast = sld_poly - sld_solv;
  //x for exp
  x_val = q*second_moment;
  x_val *= x_val;
  //computation
  form_factor = contrast * ads_amount;
  form_factor /= (q * density_poly);
  form_factor *= form_factor;
  form_factor *= (6.0 * pi * volf_cores * 1.0e+10);
  form_factor /= radius_core;
  form_factor *= exp(-x_val);

  // scale and background
  form_factor *= scale;
  form_factor += background;
  return (form_factor);
}

Core2ndMomentModel :: Core2ndMomentModel() {
	scale = Parameter(1.0);
	density_poly = Parameter(0.7);
	sld_poly = Parameter(1.5e-6);
	radius_core = Parameter(500.0, true);
	radius_core.set_min(0.0);
	volf_cores = Parameter(0.14);
	ads_amount = Parameter(1.9);
	second_moment = Parameter(23.0);
	sld_solv   = Parameter(6.3e-6);
	background = Parameter(0.0);
}

/**
 * Function to evaluate 1D scattering function
 * @param q: q-value
 * @return: function value
 */
double Core2ndMomentModel :: operator()(double q) {
	double dp[9];

	// Add the background after averaging
	dp[0] = scale();
	dp[1] = density_poly();
	dp[2] = sld_poly();
	dp[3] = radius_core();
	dp[4] = volf_cores();
	dp[5] = ads_amount();
	dp[6] = second_moment();
	dp[7] = sld_solv();
	dp[8] = 0.0;

	// Get the dispersion points for the radius
	vector<WeightPoint> weights_rad;
	radius_core.get_weights(weights_rad);

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;

	// Loop over radius weight points
	for(size_t i=0; i<weights_rad.size(); i++) {
		dp[3] = weights_rad[i].value;
		//weighted sum
		sum += weights_rad[i].weight
			* core_secondmoment_kernel(dp, q);
		norm += weights_rad[i].weight;
	}
	return sum/norm + background();
}

/**
 * Function to evaluate 2D scattering function
 * @param q_x: value of Q along x
 * @param q_y: value of Q along y
 * @return: function value
 */
double Core2ndMomentModel :: operator()(double qx, double qy) {
	double q = sqrt(qx*qx + qy*qy);
	return (*this).operator()(q);
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the sphere
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double Core2ndMomentModel :: evaluate_rphi(double q, double phi) {
	return (*this).operator()(q);
}

/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double Core2ndMomentModel :: calculate_ER() {
	return 0.0;
}
double Core2ndMomentModel :: calculate_VR() {
  return 1.0;
}
