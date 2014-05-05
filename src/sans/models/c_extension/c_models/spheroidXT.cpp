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
// RKH 03Apr2014 a re-parametrised CoreShellEllipsoid with core axial ratio X and shell thickness T
#include <math.h>
#include "parameters.hh"
#include <stdio.h>
#include <stdlib.h>
using namespace std;
#include "spheroidXT.h"

extern "C" {
#include "libCylinder.h"
#include "libStructureFactor.h"
}

typedef struct {
  double scale;
  double equat_core;
  double X_core;
  double T_shell;
  double XpolarShell;
  double sld_core;
  double sld_shell;
  double sld_solvent;
  double background;
  double axis_theta;
  double axis_phi;

} SpheroidXTParameters;

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the prolate
 * @param q: q-value
 * @param q_x: q_x / q
 * @param q_y: q_y / q
 * @return: function value
 */
static double spheroidXT_analytical_2D_scaled(SpheroidXTParameters *pars, double q, double q_x, double q_y) {

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
 // was    answer = gfn4(cos_val,pars->equat_core,pars->polar_core,pars->equat_shell,pars->polar_shell,sldcs,sldss,q);
  answer = gfn4(cos_val,pars->equat_core,  pars->equat_core*pars->X_core,   pars->equat_core + pars->T_shell,   pars->equat_core*pars->X_core + pars->T_shell*pars->XpolarShell ,sldcs,sldss,q);
  //It seems that it should be normalized somehow. How???

  //normalize by cylinder volume
  //NOTE that for this (Fournet) definition of the integral, one must MULTIPLY by Vcyl
  // was vol = 4.0*Pi/3.0*pars->equat_shell*pars->equat_shell*pars->polar_shell;
  vol = 4.0*Pi/3.0*(pars->equat_core + pars->T_shell)* (pars->equat_core + pars->T_shell) * ( pars->equat_core*pars->X_core + pars->T_shell*pars->XpolarShell);
  answer /= vol;

  //convert to [cm-1]
  answer *= 1.0e8;

  //Scale
  answer *= pars->scale;

  // add in the background
  answer += pars->background;

  return answer;
}

CoreShellEllipsoidXTModel :: CoreShellEllipsoidXTModel() {
  scale      = Parameter(1.0);
  equat_core     = Parameter(20.0, true);
  equat_core.set_min(0.0);
  X_core     = Parameter(3.0, true);
  X_core.set_min(0.001);
  T_shell   = Parameter(30.0, true);
  T_shell.set_min(0.0);
  XpolarShell    = Parameter(1.0, true);
  XpolarShell.set_min(0.0);
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

static double spheroidXT_analytical_2DXY(SpheroidXTParameters *pars, double qx, double qy) {
  double q;
  q = sqrt(qx*qx+qy*qy);
  return spheroidXT_analytical_2D_scaled(pars, q, qx/q, qy/q);
}

/**
 * Function to evaluate 1D scattering function
 * The NIST IGOR library is used for the actual calculation.
 * @param q: q-value
 * @return: function value
 */
double CoreShellEllipsoidXTModel :: operator()(double q) {
  double dp[9];

  // Fill parameter array for IGOR library
  // Add the background after averaging
  dp[0] = scale();
  dp[1] = equat_core();
  //dp[2] = polar_core();
  //dp[3] = equat_shell();
  //dp[4] = polar_shell();
  dp[2] = equat_core()*X_core();
  dp[3] = equat_core() + T_shell();
  dp[4] = equat_core()*X_core() + T_shell()*XpolarShell();
  dp[5] = sld_core();
  dp[6] = sld_shell();
  dp[7] = sld_solvent();
  dp[8] = 0.0;

  // Get the dispersion points for the major core
  vector<WeightPoint> weights_equat_core;
  equat_core.get_weights(weights_equat_core);

  // Get the dispersion points
  vector<WeightPoint> weights_X_core;
  X_core.get_weights(weights_X_core);

  // Get the dispersion points
  vector<WeightPoint> weights_T_shell;
  T_shell.get_weights(weights_T_shell);

  // Get the dispersion points
  vector<WeightPoint> weights_XpolarShell;
  XpolarShell.get_weights(weights_XpolarShell);


  // Perform the computation, with all weight points
  double sum = 0.0;
  double norm = 0.0;
  double vol = 0.0;
  double wproduct = 0.0;

  // Loop over equat core weight points
  for(int i=0; i<(int)weights_equat_core.size(); i++) {
    dp[1] = weights_equat_core[i].value;

    // Loop over polar core weight points
    for(int j=0; j<(int)weights_X_core.size(); j++) {
      dp[2] = dp[1]*weights_X_core[j].value;

      // Loop over equat outer weight points
      for(int k=0; k<(int)weights_T_shell.size(); k++) {
        dp[3] = dp[1] + weights_T_shell[k].value;

        // Loop over polar outer weight points
        for(int l=0; l<(int)weights_XpolarShell.size(); l++) {
          dp[4] = dp[2] + weights_XpolarShell[l].value*weights_T_shell[k].value;

          //Un-normalize  by volume
          wproduct =weights_equat_core[i].weight* weights_X_core[j].weight * weights_T_shell[k].weight
                  * weights_XpolarShell[l].weight;
          sum +=  wproduct * OblateForm(dp, q) * dp[3]*dp[3]*dp[4];
          //Find average volume
          vol += wproduct * dp[3]*dp[3]*dp[4];
          // was pow(weights_equat_shell[k].value,2)*weights_polar_shell[l].value;
          norm += wproduct;
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
double CoreShellEllipsoidXTModel :: evaluate_rphi(double q, double phi) {
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
double CoreShellEllipsoidXTModel :: operator()(double qx, double qy) {
  SpheroidXTParameters dp;
  // Fill parameter array
  dp.scale      = scale();
  dp.equat_core = equat_core();
  dp.X_core = X_core();
  dp.T_shell = T_shell();
  dp.XpolarShell = XpolarShell();
  dp.sld_core = sld_core();
  dp.sld_shell = sld_shell();
  dp.sld_solvent = sld_solvent();
  dp.background = 0.0;
  dp.axis_theta = axis_theta();
  dp.axis_phi = axis_phi();

  // Get the dispersion points for the major core
  vector<WeightPoint> weights_equat_core;
  equat_core.get_weights(weights_equat_core);

  // Get the dispersion points
  vector<WeightPoint> weights_X_core;
  X_core.get_weights(weights_X_core);

  // Get the dispersion points
  vector<WeightPoint> weights_T_shell;
  T_shell.get_weights(weights_T_shell);

  // Get the dispersion points
  vector<WeightPoint> weights_XpolarShell;
  XpolarShell.get_weights(weights_XpolarShell);


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
  double equat_outer = 0.0;
  double polar_outer = 0.0;

  // Loop over major core weight points
  for(int i=0; i< (int)weights_equat_core.size(); i++) {
    dp.equat_core = weights_equat_core[i].value;

    // Loop over minor core weight points
    for(int j=0; j< (int)weights_X_core.size(); j++) {
      dp.X_core = weights_X_core[j].value;

      // Loop over equat outer weight points
      for(int k=0; k< (int)weights_T_shell.size(); k++) {
        dp.T_shell = weights_T_shell[k].value;
        equat_outer = weights_equat_core[i].value + weights_T_shell[k].value;

        // Loop over polar outer weight points
        for(int l=0; l< (int)weights_XpolarShell.size(); l++) {
          dp.XpolarShell = weights_XpolarShell[l].value;
          polar_outer = weights_equat_core[i].value*weights_X_core[j].value + weights_T_shell[k].value*weights_XpolarShell[l].value;

          // Average over theta distribution
          for(int m=0; m< (int)weights_theta.size(); m++) {
            dp.axis_theta = weights_theta[m].value;

            // Average over phi distribution
            for(int n=0; n< (int)weights_phi.size(); n++) {
              dp.axis_phi = weights_phi[n].value;
              //Un-normalize by volume
               double _ptvalue = weights_equat_core[i].weight *weights_X_core[j].weight
                  * weights_T_shell[k].weight * weights_XpolarShell[l].weight
                  * weights_theta[m].weight
                  * weights_phi[n].weight
                  // rkh NOTE this passes the NEW parameters
                  * spheroidXT_analytical_2DXY(&dp, qx, qy) * pow(equat_outer,2)*polar_outer;
              if (weights_theta.size()>1) {
                _ptvalue *= fabs(cos(weights_theta[m].value*pi/180.0));
              }
              sum += _ptvalue;
              //Find average volume
              // rkh had to change this, original weighted by outer shell volume weights only, see spheroid.cpp, which looks odd,
              // (as has to assume that weights of other loops sume to unity) and here we need all four loops to get the outer size.
              vol += weights_equat_core[i].weight *weights_X_core[j].weight
                      * weights_T_shell[k].weight * weights_XpolarShell[l].weight
                      * pow(equat_outer,2)*polar_outer;
              //Find norm for volume
              norm_vol += weights_equat_core[i].weight *weights_X_core[j].weight
                      * weights_T_shell[k].weight * weights_XpolarShell[l].weight;

              norm += weights_equat_core[i].weight *weights_X_core[j].weight
                  * weights_T_shell[k].weight * weights_XpolarShell[l].weight
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
 * rkh This now needs to integrate over all four variables as above not just two
 */
double CoreShellEllipsoidXTModel :: calculate_ER() {
  SpheroidXTParameters dp;

  dp.equat_core = equat_core();
  dp.X_core = X_core();
  dp.T_shell = T_shell();
  dp.XpolarShell = XpolarShell();

  double rad_out = 0.0;
  double equat_outer = 0.0;
  double polar_outer = 0.0;

  // Perform the computation, with all weight points
  double sum = 0.0;
  double norm = 0.0;

  // Get the dispersion points for the core
  vector<WeightPoint> weights_equat_core;
  equat_core.get_weights(weights_equat_core);

  // Get the dispersion points
  vector<WeightPoint> weights_X_core;
  X_core.get_weights(weights_X_core);

  // Get the dispersion points
  vector<WeightPoint> weights_T_shell;
  T_shell.get_weights(weights_T_shell);

  // Get the dispersion points
  vector<WeightPoint> weights_XpolarShell;
  XpolarShell.get_weights(weights_XpolarShell);


  // Loop over core weight points
  for(int i=0; i< (int)weights_equat_core.size(); i++) {
    dp.equat_core = weights_equat_core[i].value;
    // Loop over weight points
    for(int j=0; j< (int)weights_X_core.size(); j++) {
      // Loop over weight points
      for(int k=0; k< (int)weights_T_shell.size(); k++) {
        equat_outer = weights_equat_core[i].value + weights_T_shell[k].value;
        // Loop over polar outer weight points
        for(int l=0; l< (int)weights_XpolarShell.size(); l++) {
          polar_outer = weights_equat_core[i].value*weights_X_core[j].value + weights_T_shell[k].value*weights_XpolarShell[l].value;
        //Note: output of "DiamEllip(dp.polar_shell,dp.equat_shell)" is DIAMETER.
          sum +=weights_equat_core[i].weight *weights_X_core[j].weight
                  * weights_T_shell[k].weight * weights_XpolarShell[l].weight*DiamEllip(polar_outer,equat_outer)/2.0;
          norm += weights_equat_core[i].weight *weights_X_core[j].weight
                  * weights_T_shell[k].weight * weights_XpolarShell[l].weight;
        }
      }
    }
  }
  if (norm != 0){
    //return the averaged value
    rad_out =  sum/norm;}
  else{
    //return normal value
    //Note: output of "DiamEllip(dp.polar_shell,dp.equat_shell)" is DIAMETER.
    rad_out = DiamEllip(dp.equat_core + dp.T_shell, dp.equat_core * dp.X_core + dp.T_shell*dp.XpolarShell)/2.0;}

  return rad_out;
}
double CoreShellEllipsoidXTModel :: calculate_VR() {
  return 1.0;
}
