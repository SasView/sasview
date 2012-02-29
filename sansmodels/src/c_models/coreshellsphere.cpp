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
}

typedef struct {
  double scale;
  double radius;
  double thickness;
  double core_sld;
  double shell_sld;
  double solvent_sld;
  double background;
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
 * @param q_x: value of Q along x
 * @param q_y: value of Q along y
 * @return: function value
 */
double CoreShellModel :: operator()(double qx, double qy) {
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
double CoreShellModel :: evaluate_rphi(double q, double phi) {
  return (*this).operator()(q);
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
