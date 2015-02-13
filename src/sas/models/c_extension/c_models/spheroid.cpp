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
#include <stdlib.h>
using namespace std;
#include "spheroid.h"

extern "C" {
#include "libCylinder.h"
#include "libStructureFactor.h"
}

typedef struct {
  double scale;
  double equat_core;
  double polar_core;
  double equat_shell;
  double polar_shell;
  double sld_core;
  double sld_shell;
  double sld_solvent;
  double background;
  double axis_theta;
  double axis_phi;

} SpheroidParameters;

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the prolate
 * @param q: q-value
 * @param q_x: q_x / q
 * @param q_y: q_y / q
 * @return: function value
 */
static double spheroid_analytical_2D_scaled(SpheroidParameters *pars, double q, double q_x, double q_y) {

  double cyl_x, cyl_y;//, cyl_z;
  //double q_z;
  double alpha, vol, cos_val;
  double answer;
  double Pi = 4.0*atan(1.0);
  double sldcs,sldss;

  //convert angle degree to radian
  double theta = pars->axis_theta * Pi/180.0;
  double phi = pars->axis_phi * Pi/180.0;


  // ellipsoid orientation, the axis of the rotation is consistent with the ploar axis.
  cyl_x = cos(theta) * cos(phi);
  cyl_y = sin(theta);
  //cyl_z = -cos(theta) * sin(phi);
  //del sld
  sldcs = pars->sld_core - pars->sld_shell;
  sldss = pars->sld_shell- pars->sld_solvent;

  // q vector
  //q_z = 0;

  // Compute the angle btw vector q and the
  // axis of the cylinder
  cos_val = cyl_x*q_x + cyl_y*q_y;// + cyl_z*q_z;

  // The following test should always pass
  if (fabs(cos_val)>1.0) {
    printf("cyl_ana_2D: Unexpected error: cos(alpha)>1\n");
    return 0;
  }

  // Note: cos(alpha) = 0 and 1 will get an
  // undefined value from CylKernel
  alpha = acos( cos_val );

  // Call the IGOR library function to get the kernel: MUST use gfn4 not gf2 because of the def of params.
  answer = gfn4(cos_val,pars->equat_core,pars->polar_core,pars->equat_shell,pars->polar_shell,sldcs,sldss,q);
  //It seems that it should be normalized somehow. How???

  //normalize by cylinder volume
  //NOTE that for this (Fournet) definition of the integral, one must MULTIPLY by Vcyl
  vol = 4.0*Pi/3.0*pars->equat_shell*pars->equat_shell*pars->polar_shell;
  answer /= vol;

  //convert to [cm-1]
  answer *= 1.0e8;

  //Scale
  answer *= pars->scale;

  // add in the background
  answer += pars->background;

  return answer;
}

CoreShellEllipsoidModel :: CoreShellEllipsoidModel() {
  scale      = Parameter(1.0);
  equat_core     = Parameter(200.0, true);
  equat_core.set_min(0.0);
  polar_core     = Parameter(20.0, true);
  polar_core.set_min(0.0);
  equat_shell   = Parameter(250.0, true);
  equat_shell.set_min(0.0);
  polar_shell    = Parameter(30.0, true);
  polar_shell.set_min(0.0);
  sld_core   = Parameter(2e-6);
  sld_shell  = Parameter(1e-6);
  sld_solvent = Parameter(6.3e-6);
  background = Parameter(0.0);
  axis_theta  = Parameter(0.0, true);
  axis_phi    = Parameter(0.0, true);

}


/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the prolate
 * @param q: q-value
 * @return: function value
 */
static double spheroid_analytical_2DXY(SpheroidParameters *pars, double qx, double qy) {
  double q;
  q = sqrt(qx*qx+qy*qy);
  return spheroid_analytical_2D_scaled(pars, q, qx/q, qy/q);
}

/**
 * Function to evaluate 1D scattering function
 * The NIST IGOR library is used for the actual calculation.
 * @param q: q-value
 * @return: function value
 */
double CoreShellEllipsoidModel :: operator()(double q) {
  double dp[9];

  // Fill parameter array for IGOR library
  // Add the background after averaging
  dp[0] = scale();
  dp[1] = equat_core();
  dp[2] = polar_core();
  dp[3] = equat_shell();
  dp[4] = polar_shell();
  dp[5] = sld_core();
  dp[6] = sld_shell();
  dp[7] = sld_solvent();
  dp[8] = 0.0;

  // Get the dispersion points for the major core
  vector<WeightPoint> weights_equat_core;
  equat_core.get_weights(weights_equat_core);

  // Get the dispersion points for the minor core
  vector<WeightPoint> weights_polar_core;
  polar_core.get_weights(weights_polar_core);

  // Get the dispersion points for the major shell
  vector<WeightPoint> weights_equat_shell;
  equat_shell.get_weights(weights_equat_shell);

  // Get the dispersion points for the minor_shell
  vector<WeightPoint> weights_polar_shell;
  polar_shell.get_weights(weights_polar_shell);


  // Perform the computation, with all weight points
  double sum = 0.0;
  double norm = 0.0;
  double vol = 0.0;

  // Loop over major core weight points
  for(int i=0; i<(int)weights_equat_core.size(); i++) {
    dp[1] = weights_equat_core[i].value;

    // Loop over minor core weight points
    for(int j=0; j<(int)weights_polar_core.size(); j++) {
      dp[2] = weights_polar_core[j].value;

      // Loop over major shell weight points
      for(int k=0; k<(int)weights_equat_shell.size(); k++) {
        dp[3] = weights_equat_shell[k].value;

        // Loop over minor shell weight points
        for(int l=0; l<(int)weights_polar_shell.size(); l++) {
          dp[4] = weights_polar_shell[l].value;
          //Un-normalize  by volume
          sum += weights_equat_core[i].weight* weights_polar_core[j].weight * weights_equat_shell[k].weight
              * weights_polar_shell[l].weight * OblateForm(dp, q)
          * pow(weights_equat_shell[k].value,2)*weights_polar_shell[l].value;
          //Find average volume
          vol += weights_equat_core[i].weight* weights_polar_core[j].weight
              * weights_equat_shell[k].weight
              * weights_polar_shell[l].weight
              * pow(weights_equat_shell[k].value,2)*weights_polar_shell[l].value;
          norm += weights_equat_core[i].weight* weights_polar_core[j].weight * weights_equat_shell[k].weight
              * weights_polar_shell[l].weight;
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
/*
double OblateModel :: operator()(double qx, double qy) {
	double q = sqrt(qx*qx + qy*qy);

	return (*this).operator()(q);
}
 */

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the oblate
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double CoreShellEllipsoidModel :: evaluate_rphi(double q, double phi) {
  double qx = q*cos(phi);
  double qy = q*sin(phi);
  return (*this).operator()(qx, qy);
}

/**
 * Function to evaluate 2D scattering function
 * @param q_x: value of Q along x
 * @param q_y: value of Q along y
 * @return: function value
 */
double CoreShellEllipsoidModel :: operator()(double qx, double qy) {
  SpheroidParameters dp;
  // Fill parameter array
  dp.scale      = scale();
  dp.equat_core = equat_core();
  dp.polar_core = polar_core();
  dp.equat_shell = equat_shell();
  dp.polar_shell = polar_shell();
  dp.sld_core = sld_core();
  dp.sld_shell = sld_shell();
  dp.sld_solvent = sld_solvent();
  dp.background = 0.0;
  dp.axis_theta = axis_theta();
  dp.axis_phi = axis_phi();

  // Get the dispersion points for the major core
  vector<WeightPoint> weights_equat_core;
  equat_core.get_weights(weights_equat_core);

  // Get the dispersion points for the minor core
  vector<WeightPoint> weights_polar_core;
  polar_core.get_weights(weights_polar_core);

  // Get the dispersion points for the major shell
  vector<WeightPoint> weights_equat_shell;
  equat_shell.get_weights(weights_equat_shell);

  // Get the dispersion points for the minor shell
  vector<WeightPoint> weights_polar_shell;
  polar_shell.get_weights(weights_polar_shell);


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
  double pi = 4.0*atan(1.0);
  // Loop over major core weight points
  for(int i=0; i< (int)weights_equat_core.size(); i++) {
    dp.equat_core = weights_equat_core[i].value;

    // Loop over minor core weight points
    for(int j=0; j< (int)weights_polar_core.size(); j++) {
      dp.polar_core = weights_polar_core[j].value;

      // Loop over major shell weight points
      for(int k=0; k< (int)weights_equat_shell.size(); k++) {
        dp.equat_shell = weights_equat_shell[i].value;

        // Loop over minor shell weight points
        for(int l=0; l< (int)weights_polar_shell.size(); l++) {
          dp.polar_shell = weights_polar_shell[l].value;

          // Average over theta distribution
          for(int m=0; m< (int)weights_theta.size(); m++) {
            dp.axis_theta = weights_theta[m].value;

            // Average over phi distribution
            for(int n=0; n< (int)weights_phi.size(); n++) {
              dp.axis_phi = weights_phi[n].value;
              //Un-normalize by volume
              double _ptvalue = weights_equat_core[i].weight *weights_polar_core[j].weight
                  * weights_equat_shell[k].weight * weights_polar_shell[l].weight
                  * weights_theta[m].weight
                  * weights_phi[n].weight
                  * spheroid_analytical_2DXY(&dp, qx, qy)
              * pow(weights_equat_shell[k].value,2)*weights_polar_shell[l].value;
              if (weights_theta.size()>1) {
                _ptvalue *= fabs(cos(weights_theta[m].value*pi/180.0));
              }
              sum += _ptvalue;
              //Find average volume
              vol += weights_equat_shell[k].weight
                  * weights_polar_shell[l].weight
                  * pow(weights_equat_shell[k].value,2)*weights_polar_shell[l].value;
              //Find norm for volume
              norm_vol += weights_equat_shell[k].weight
                  * weights_polar_shell[l].weight;

              norm += weights_equat_core[i].weight *weights_polar_core[j].weight
                  * weights_equat_shell[k].weight * weights_polar_shell[l].weight
                  * weights_theta[m].weight * weights_phi[n].weight;
            }
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
 * Function to calculate effective radius
 * @return: effective radius value
 */
double CoreShellEllipsoidModel :: calculate_ER() {
  SpheroidParameters dp;

  dp.equat_shell = equat_shell();
  dp.polar_shell = polar_shell();

  double rad_out = 0.0;

  // Perform the computation, with all weight points
  double sum = 0.0;
  double norm = 0.0;

  // Get the dispersion points for the major shell
  vector<WeightPoint> weights_equat_shell;
  equat_shell.get_weights(weights_equat_shell);

  // Get the dispersion points for the minor shell
  vector<WeightPoint> weights_polar_shell;
  polar_shell.get_weights(weights_polar_shell);

  // Loop over major shell weight points
  for(int i=0; i< (int)weights_equat_shell.size(); i++) {
    dp.equat_shell = weights_equat_shell[i].value;
    for(int k=0; k< (int)weights_polar_shell.size(); k++) {
      dp.polar_shell = weights_polar_shell[k].value;
      //Note: output of "DiamEllip(dp.polar_shell,dp.equat_shell)" is DIAMETER.
      sum +=weights_equat_shell[i].weight
          * weights_polar_shell[k].weight*DiamEllip(dp.polar_shell,dp.equat_shell)/2.0;
      norm += weights_equat_shell[i].weight* weights_polar_shell[k].weight;
    }
  }
  if (norm != 0){
    //return the averaged value
    rad_out =  sum/norm;}
  else{
    //return normal value
    //Note: output of "DiamEllip(dp.polar_shell,dp.equat_shell)" is DIAMETER.
    rad_out = DiamEllip(dp.polar_shell,dp.equat_shell)/2.0;}

  return rad_out;
}
double CoreShellEllipsoidModel :: calculate_VR() {
  return 1.0;
}
