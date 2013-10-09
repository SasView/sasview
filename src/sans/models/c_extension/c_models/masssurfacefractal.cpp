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
#include "masssurfacefractal.h"



static double mass_surface_fractal_kernel(double dp[], double q) {
  //fit parameters
  double scale = dp[0];
  double mass_dim = dp[1];
  double surface_dim = dp[2];
  double cluster_rg = dp[3];
  double primary_rg = dp[4];
  double background = dp[5];

  //others
  double tot_dim = 0.0;
  double rc_norm = 0.0;
  double rp_norm = 0.0;
  double x_val1 = 0.0;
  double x_val2 = 0.0;
  double form_factor = 0.0;
  double inv_form = 0.0;

  // This model is valid only for 0<dm<=6 and 0<ds<=6
  // Not valid values => reject as 0.0
  if (mass_dim < 1e-16){
	  return background;
  }
  if (mass_dim > 6.0){
	  return background;
  }
  if (surface_dim < 1e-16){
	  return background;
  }
  if (surface_dim > 6.0){
	  return background;
  }
  tot_dim = 6.0 - surface_dim - mass_dim;
  //singulars
  if (tot_dim < 0.0){
	  return background;
  }

  //computation
  mass_dim /= 2.0;
  tot_dim /= 2.0;
  rc_norm = cluster_rg * cluster_rg / (3.0 * mass_dim);
  if (tot_dim < 1.0e-16){
	  tot_dim = 1.0e-16;
  }
  rp_norm = primary_rg * primary_rg / (3.0 * tot_dim);

  //x for P
  x_val1 = 1.0 +  q * q * rc_norm;
  x_val2 = 1.0 +  q * q * rp_norm;

  inv_form = pow(x_val1, mass_dim) * pow(x_val2, tot_dim);

  //another singular
  if (inv_form == 0.0) return background;

  form_factor = 1.0;
  form_factor /= inv_form;

  //scale and background
  form_factor *= scale;
  form_factor += background;
  return (form_factor);
}

MassSurfaceFractal :: MassSurfaceFractal() {
  scale      = Parameter(1.0);
  mass_dim = Parameter(1.8);
  surface_dim = Parameter(2.3);
  cluster_rg = Parameter(86.7);
  primary_rg = Parameter(4000.0);
  background = Parameter(0.0);
}

/**
 * Function to evaluate 1D scattering function
 * @param q: q-value
 * @return: function value
 */
double MassSurfaceFractal :: operator()(double q) {
  double dp[6];

  // Fill parameter array for IGOR library
  // Add the background after averaging
  dp[0] = scale();
  dp[1] = mass_dim();
  dp[2] = surface_dim();
  dp[3] = cluster_rg();
  dp[4] = primary_rg();
  dp[5] = 0.0;

  //computation: no polydispersion
  double sum = 0.0;
  sum = mass_surface_fractal_kernel(dp, q);

  return sum + background();
}

/**
 * Function to evaluate 2D scattering function
 * @param q_x: value of Q along x
 * @param q_y: value of Q along y
 * @return: function value
 */
double MassSurfaceFractal :: operator()(double qx, double qy) {
  double q = sqrt(qx*qx + qy*qy);
  return (*this).operator()(q);
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the FractalModel
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double MassSurfaceFractal :: evaluate_rphi(double q, double phi) {
  return (*this).operator()(q);
}

/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double MassSurfaceFractal :: calculate_ER() {
  //NOT implemented yet!!! 'cause None shape Model
  return 0.0;
}
double MassSurfaceFractal :: calculate_VR() {
  return 1.0;
}
