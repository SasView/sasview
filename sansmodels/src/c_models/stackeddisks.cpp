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
 *	TODO: refactor so that we pull in the old sansmodels.c_extensions
 *	TODO: add 2d
 */

#include <math.h>
#include "parameters.hh"
#include <stdio.h>
using namespace std;
#include "stacked_disks.h"

extern "C" {
#include "libCylinder.h"
#include "libStructureFactor.h"
}

typedef struct {
  double scale;
  double radius;
  double core_thick;
  double layer_thick;
  double core_sld;
  double layer_sld;
  double solvent_sld;
  double n_stacking;
  double sigma_d;
  double background;
  double axis_theta;
  double axis_phi;
} StackedDisksParameters;


/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the staked disks
 * @param q: q-value
 * @param q_x: q_x / q
 * @param q_y: q_y / q
 * @return: function value
 */
static double stacked_disks_analytical_2D_scaled(StackedDisksParameters *pars, double q, double q_x, double q_y) {
  double cyl_x, cyl_y, cyl_z;
  double q_z;
  double alpha, vol, cos_val;
  double d, dum, halfheight;
  double answer;



  // parallelepiped orientation
  cyl_x = sin(pars->axis_theta) * cos(pars->axis_phi);
  cyl_y = sin(pars->axis_theta) * sin(pars->axis_phi);
  cyl_z = cos(pars->axis_theta);

  // q vector
  q_z = 0;

  // Compute the angle btw vector q and the
  // axis of the parallelepiped
  cos_val = cyl_x*q_x + cyl_y*q_y + cyl_z*q_z;

  // The following test should always pass
  if (fabs(cos_val)>1.0) {
    printf("parallel_ana_2D: Unexpected error: cos(alpha)>1\n");
    return 0;
  }

  // Note: cos(alpha) = 0 and 1 will get an
  // undefined value from Stackdisc_kern
  alpha = acos( cos_val );

  // Call the IGOR library function to get the kernel
  d = 2 * pars->layer_thick + pars->core_thick;
  halfheight = pars->core_thick/2.0;
  dum =alpha ;
  answer = Stackdisc_kern(q, pars->radius, pars->core_sld,pars->layer_sld,
      pars->solvent_sld, halfheight, pars->layer_thick, dum, pars->sigma_d, d, pars->n_stacking)/sin(alpha);

  // Multiply by contrast^2
  //answer *= pars->contrast*pars->contrast;

  //normalize by staked disks volume
  vol = acos(-1.0) * pars->radius * pars->radius * d * pars->n_stacking;
  answer /= vol;

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
 * @param pars: parameters of the staked disks
 * @param q: q-value
 * @return: function value
 */
static double stacked_disks_analytical_2DXY(StackedDisksParameters *pars, double qx, double qy) {
  double q;
  q = sqrt(qx*qx+qy*qy);
  return stacked_disks_analytical_2D_scaled(pars, q, qx/q, qy/q);
}

StackedDisksModel :: StackedDisksModel() {
  scale      = Parameter(1.0);
  radius     = Parameter(3000.0, true);
  radius.set_min(0.0);
  core_thick  = Parameter(10.0, true);
  core_thick.set_min(0.0);
  layer_thick     = Parameter(15.0);
  layer_thick.set_min(0.0);
  core_sld = Parameter(4.0e-6);
  layer_sld  = Parameter(-4.0e-7);
  solvent_sld  = Parameter(5.0e-6);
  n_stacking   = Parameter(1);
  sigma_d   = Parameter(0);
  background = Parameter(0.001);
  axis_theta  = Parameter(0.0, true);
  axis_phi    = Parameter(0.0, true);
}

/**
 * Function to evaluate 1D scattering function
 * The NIST IGOR library is used for the actual calculation.
 * @param q: q-value
 * @return: function value
 */
double StackedDisksModel :: operator()(double q) {
  double dp[10];

  // Fill parameter array for IGOR library
  // Add the background after averaging
  dp[0] = scale();
  dp[1] = radius();
  dp[2] = core_thick();
  dp[3] = layer_thick();
  dp[4] = core_sld();
  dp[5] = layer_sld();
  dp[6] = solvent_sld();
  dp[7] = n_stacking();
  dp[8] = sigma_d();
  dp[9] = 0.0;

  // Get the dispersion points for the radius
  vector<WeightPoint> weights_radius;
  radius.get_weights(weights_radius);

  // Get the dispersion points for the core_thick
  vector<WeightPoint> weights_core_thick;
  core_thick.get_weights(weights_core_thick);

  // Get the dispersion points for the layer_thick
  vector<WeightPoint> weights_layer_thick;
  layer_thick.get_weights(weights_layer_thick);

  // Perform the computation, with all weight points
  double sum = 0.0;
  double norm = 0.0;
  double vol = 0.0;

  // Loop over length weight points
  for(int i=0; i< (int)weights_radius.size(); i++) {
    dp[1] = weights_radius[i].value;

    // Loop over radius weight points
    for(int j=0; j< (int)weights_core_thick.size(); j++) {
      dp[2] = weights_core_thick[j].value;

      // Loop over thickness weight points
      for(int k=0; k< (int)weights_layer_thick.size(); k++) {
        dp[3] = weights_layer_thick[k].value;
        //Un-normalize by volume
        sum += weights_radius[i].weight
            * weights_core_thick[j].weight * weights_layer_thick[k].weight* StackedDiscs(dp, q)
        *pow(weights_radius[i].value,2)*(weights_core_thick[j].value+2*weights_layer_thick[k].value);
        //Find average volume
        vol += weights_radius[i].weight
            * weights_core_thick[j].weight * weights_layer_thick[k].weight
            *pow(weights_radius[i].value,2)*(weights_core_thick[j].value+2*weights_layer_thick[k].value);
        norm += weights_radius[i].weight
            * weights_core_thick[j].weight* weights_layer_thick[k].weight;
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
double StackedDisksModel :: operator()(double qx, double qy) {
  StackedDisksParameters dp;
  // Fill parameter array
  dp.scale      = scale();
  dp.core_thick    = core_thick();
  dp.radius	  = radius();
  dp.layer_thick  = layer_thick();
  dp.core_sld   = core_sld();
  dp.layer_sld  = layer_sld();
  dp.solvent_sld= solvent_sld();
  dp.n_stacking	  = n_stacking();
  dp.sigma_d   = sigma_d();
  dp.background = 0.0;
  dp.axis_theta = axis_theta();
  dp.axis_phi   = axis_phi();

  // Get the dispersion points for the length
  vector<WeightPoint> weights_core_thick;
  core_thick.get_weights(weights_core_thick);

  // Get the dispersion points for the radius
  vector<WeightPoint> weights_radius;
  radius.get_weights(weights_radius);

  // Get the dispersion points for the thickness
  vector<WeightPoint> weights_layer_thick;
  layer_thick.get_weights(weights_layer_thick);

  // Get angular averaging for theta
  vector<WeightPoint> weights_theta;
  axis_theta.get_weights(weights_theta);

  // Get angular averaging for phi
  vector<WeightPoint> weights_phi;
  axis_phi.get_weights(weights_phi);

  // Perform the computation, with all weight points
  double sum = 0.0;
  double norm = 0.0;
  double norm_vol = 0.0;
  double vol = 0.0;

  // Loop over length weight points
  for(int i=0; i< (int)weights_core_thick.size(); i++) {
    dp.core_thick = weights_core_thick[i].value;

    // Loop over radius weight points
    for(int j=0; j< (int)weights_radius.size(); j++) {
      dp.radius = weights_radius[j].value;

      // Loop over thickness weight points
      for(int k=0; k< (int)weights_layer_thick.size(); k++) {
        dp.layer_thick = weights_layer_thick[k].value;

        for(int l=0; l< (int)weights_theta.size(); l++) {
          dp.axis_theta = weights_theta[l].value;

          // Average over phi distribution
          for(int m=0; m <(int)weights_phi.size(); m++) {
            dp.axis_phi = weights_phi[m].value;

            //Un-normalize by volume
            double _ptvalue = weights_core_thick[i].weight
                * weights_radius[j].weight
                * weights_layer_thick[k].weight
                * weights_theta[l].weight
                * weights_phi[m].weight
                * stacked_disks_analytical_2DXY(&dp, qx, qy)
            *pow(weights_radius[j].value,2)*(weights_core_thick[i].value+2*weights_layer_thick[k].value);
            if (weights_theta.size()>1) {
              _ptvalue *= fabs(sin(weights_theta[l].value));
            }
            sum += _ptvalue;
            //Find average volume
            vol += weights_radius[j].weight
                * weights_core_thick[i].weight * weights_layer_thick[k].weight
                *pow(weights_radius[j].value,2)*(weights_core_thick[i].value+2*weights_layer_thick[k].value);
            //Find norm for volume
            norm_vol += weights_radius[j].weight
                * weights_core_thick[i].weight * weights_layer_thick[k].weight;

            norm += weights_core_thick[i].weight
                * weights_radius[j].weight
                * weights_layer_thick[k].weight
                * weights_theta[l].weight
                * weights_phi[m].weight;
          }
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
 * @param pars: parameters of the triaxial ellipsoid
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double StackedDisksModel :: evaluate_rphi(double q, double phi) {
  double qx = q*cos(phi);
  double qy = q*sin(phi);
  return (*this).operator()(qx, qy);
}
/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double StackedDisksModel :: calculate_ER() {
  StackedDisksParameters dp;

  dp.core_thick    = core_thick();
  dp.radius	  = radius();
  dp.layer_thick  = layer_thick();
  dp.n_stacking	  = n_stacking();

  double rad_out = 0.0;
  if (dp.n_stacking <= 0.0){
    return rad_out;
  }

  // Perform the computation, with all weight points
  double sum = 0.0;
  double norm = 0.0;

  // Get the dispersion points for the length
  vector<WeightPoint> weights_core_thick;
  core_thick.get_weights(weights_core_thick);

  // Get the dispersion points for the radius
  vector<WeightPoint> weights_radius;
  radius.get_weights(weights_radius);

  // Get the dispersion points for the thickness
  vector<WeightPoint> weights_layer_thick;
  layer_thick.get_weights(weights_layer_thick);

  // Loop over major shell weight points
  for(int i=0; i< (int)weights_core_thick.size(); i++) {
    dp.core_thick = weights_core_thick[i].value;
    for(int j=0; j< (int)weights_layer_thick.size(); j++) {
      dp.layer_thick = weights_layer_thick[j].value;
      for(int k=0; k< (int)weights_radius.size(); k++) {
        dp.radius = weights_radius[k].value;
        //Note: output of "DiamCyl(dp.length,dp.radius)" is DIAMETER.
        sum +=weights_core_thick[i].weight*weights_layer_thick[j].weight
            * weights_radius[k].weight*DiamCyl(dp.n_stacking*(dp.layer_thick*2.0+dp.core_thick),dp.radius)/2.0;
        norm += weights_core_thick[i].weight*weights_layer_thick[j].weight* weights_radius[k].weight;
      }
    }
  }
  if (norm != 0){
    //return the averaged value
    rad_out =  sum/norm;}
  else{
    //return normal value
    //Note: output of "DiamCyl(dp.length,dp.radius)" is DIAMETER.
    rad_out = DiamCyl(dp.n_stacking*(dp.layer_thick*2.0+dp.core_thick),dp.radius)/2.0;}

  return rad_out;
}
double StackedDisksModel :: calculate_VR() {
  return 1.0;
}
