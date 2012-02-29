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
#include "vesicle.h"

extern "C" {
#include "libSphere.h"
}

typedef struct {
  double scale;
  double radius;
  double thickness;
  double solv_sld;
  double shell_sld;
  double background;
} VesicleParameters;

VesicleModel :: VesicleModel() {
  scale      = Parameter(1.0);
  radius     = Parameter(100.0, true);
  radius.set_min(0.0);
  thickness  = Parameter(30.0, true);
  thickness.set_min(0.0);
  solv_sld   = Parameter(6.36e-6);
  shell_sld   = Parameter(5.0e-7);
  background = Parameter(0.0);
}

/**
 * Function to evaluate 1D scattering function
 * The NIST IGOR library is used for the actual calculation.
 * @param q: q-value
 * @return: function value
 */
double VesicleModel :: operator()(double q) {
  double dp[6];

  // Fill parameter array for IGOR library
  // Add the background after averaging
  dp[0] = scale();
  dp[1] = radius();
  dp[2] = thickness();
  dp[3] = solv_sld();
  dp[4] = shell_sld();
  dp[5] = 0.0;


  // Get the dispersion points for the core radius
  vector<WeightPoint> weights_radius;
  radius.get_weights(weights_radius);
  // Get the dispersion points for the thickness
  vector<WeightPoint> weights_thickness;
  thickness.get_weights(weights_thickness);

  // Perform the computation, with all weight points
  double sum = 0.0;
  double norm = 0.0;
  double vol = 0.0;

  // Loop over radius weight points
  for(int i=0; i< (int)weights_radius.size(); i++) {
    dp[1] = weights_radius[i].value;
    for(int j=0; j< (int)weights_thickness.size(); j++) {
      dp[2] = weights_thickness[j].value;
      sum += weights_radius[i].weight
          * weights_thickness[j].weight * VesicleForm(dp, q)
      *(pow(weights_radius[i].value+weights_thickness[j].value,3)-pow(weights_radius[i].value,3));
      //Find average volume
      vol += weights_radius[i].weight * weights_thickness[j].weight
          *(pow(weights_radius[i].value+weights_thickness[j].value,3)-pow(weights_radius[i].value,3));
      norm += weights_radius[i].weight * weights_thickness[j].weight;
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
double VesicleModel :: operator()(double qx, double qy) {
  double q = sqrt(qx*qx + qy*qy);
  return (*this).operator()(q);
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the vesicle
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double VesicleModel :: evaluate_rphi(double q, double phi) {
  return (*this).operator()(q);
}
/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double VesicleModel :: calculate_ER() {
  VesicleParameters dp;

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
/**
 * Function to calculate volf_ratio for shell
 * @return: volf_ratio value
 */
double VesicleModel :: calculate_VR() {
  VesicleParameters dp;

  dp.radius     = radius();
  dp.thickness  = thickness();

  double rad_out = 0.0;

  // Perform the computation, with all weight points
  double sum_tot = 0.0;
  double sum_shell = 0.0;


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
      sum_tot += weights_thickness[j].weight
          * weights_radius[k].weight*pow((dp.radius+dp.thickness), 3);
      sum_shell += weights_thickness[j].weight
		  * weights_radius[k].weight*(pow((dp.radius+dp.thickness), 3)
				  - pow((dp.radius), 3));
    }
  }
  if (sum_tot == 0.0){
    //return the default value
    rad_out =  1.0;}
  else{
    //return ratio value
    return sum_shell/sum_tot;
  }
}
