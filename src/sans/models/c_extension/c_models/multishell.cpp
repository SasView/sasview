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
#include "multishell.h"

extern "C" {
#include "libSphere.h"
}

typedef struct {
  double scale;
  double core_radius;
  double s_thickness;
  double w_thickness;
  double core_sld;
  double shell_sld;
  double n_pairs;
  double background;

} MultiShellParameters;

MultiShellModel :: MultiShellModel() {
  scale      = Parameter(1.0);
  core_radius     = Parameter(60.0, true);
  core_radius.set_min(0.0);
  s_thickness  = Parameter(10.0, true);
  s_thickness.set_min(0.0);
  w_thickness   = Parameter(10.0, true);
  w_thickness.set_min(0.0);
  core_sld   = Parameter(6.4e-6);
  shell_sld   = Parameter(4.0e-7);
  n_pairs   = Parameter(2);
  background = Parameter(0.0);
}

/**
 * Function to evaluate 1D scattering function
 * The NIST IGOR library is used for the actual calculation.
 * @param q: q-value
 * @return: function value
 */
double MultiShellModel :: operator()(double q) {
  double dp[8];

  // Fill parameter array for IGOR library
  // Add the background after averaging
  dp[0] = scale();
  dp[1] = core_radius();
  dp[2] = s_thickness();
  dp[3] = w_thickness();
  dp[4] = core_sld();
  dp[5] = shell_sld();
  dp[6] = n_pairs();
  dp[7] = 0.0;

  // Get the dispersion points for the core radius
  vector<WeightPoint> weights_core_radius;
  core_radius.get_weights(weights_core_radius);

  // Get the dispersion points for the s_thickness
  vector<WeightPoint> weights_s_thickness;
  s_thickness.get_weights(weights_s_thickness);

  // Get the dispersion points for the w_thickness
  vector<WeightPoint> weights_w_thickness;
  w_thickness.get_weights(weights_w_thickness);

  // Perform the computation, with all weight points
  double sum = 0.0;
  double norm = 0.0;
  double vol = 0.0;

  // Loop over radius weight points
  for(int i=0; i< (int)weights_core_radius.size(); i++) {
    dp[1] = weights_core_radius[i].value;
    for(int j=0; j< (int)weights_s_thickness.size(); j++){
      dp[2] = weights_s_thickness[j].value;
      for(int k=0; k< (int)weights_w_thickness.size(); k++){
        dp[3] = weights_w_thickness[k].value;
        //Un-normalize SphereForm by volume
        sum += weights_core_radius[i].weight*weights_s_thickness[j].weight
            *weights_w_thickness[k].weight* MultiShell(dp, q)
        *pow(weights_core_radius[i].value+dp[6]*weights_s_thickness[j].value+(dp[6]-1)*weights_w_thickness[k].value,3);
        //Find average volume
        vol += weights_core_radius[i].weight*weights_s_thickness[j].weight
            *weights_w_thickness[k].weight
            *pow(weights_core_radius[i].value+dp[6]*weights_s_thickness[j].value+(dp[6]-1)*weights_w_thickness[k].value,3);
        norm += weights_core_radius[i].weight*weights_s_thickness[j].weight
            *weights_w_thickness[k].weight;
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
double MultiShellModel :: operator()(double qx, double qy) {
  double q = sqrt(qx*qx + qy*qy);
  return (*this).operator()(q);
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the multishell
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double MultiShellModel :: evaluate_rphi(double q, double phi) {
  return (*this).operator()(q);
}
/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double MultiShellModel :: calculate_ER() {
  MultiShellParameters dp;

  dp.core_radius     = core_radius();
  dp.s_thickness  = s_thickness();
  dp.w_thickness  = w_thickness();
  dp.n_pairs = n_pairs();

  double rad_out = 0.0;

  // Perform the computation, with all weight points
  double sum = 0.0;
  double norm = 0.0;
  if (dp.n_pairs <= 0.0 ){
    dp.n_pairs = 0.0;
  }

  // Get the dispersion points for the core radius
  vector<WeightPoint> weights_core_radius;
  core_radius.get_weights(weights_core_radius);

  // Get the dispersion points for the s_thickness
  vector<WeightPoint> weights_s_thickness;
  s_thickness.get_weights(weights_s_thickness);

  // Get the dispersion points for the w_thickness
  vector<WeightPoint> weights_w_thickness;
  w_thickness.get_weights(weights_w_thickness);

  // Loop over major shell weight points
  for(int i=0; i< (int)weights_s_thickness.size(); i++) {
    dp.s_thickness = weights_s_thickness[i].value;
    for(int j=0; j< (int)weights_w_thickness.size(); j++) {
      dp.w_thickness = weights_w_thickness[j].value;
      for(int k=0; k< (int)weights_core_radius.size(); k++) {
        dp.core_radius = weights_core_radius[k].value;
        sum += weights_s_thickness[i].weight*weights_w_thickness[j].weight
            * weights_core_radius[k].weight*(dp.core_radius+dp.n_pairs*dp.s_thickness+(dp.n_pairs-1.0)*dp.w_thickness);
        norm += weights_s_thickness[i].weight*weights_w_thickness[j].weight* weights_core_radius[k].weight;
      }
    }
  }
  if (norm != 0){
    //return the averaged value
    rad_out =  sum/norm;}
  else{
    //return normal value
    rad_out = (dp.core_radius+dp.n_pairs*dp.s_thickness+(dp.n_pairs-1.0)*dp.w_thickness);}

  return rad_out;
}
double MultiShellModel :: calculate_VR() {
  return 1.0;
}
