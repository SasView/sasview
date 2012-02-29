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
#include "hollow_cylinder.h"

extern "C" {
#include "libCylinder.h"
#include "libStructureFactor.h"
}

typedef struct {
  double scale;
  double core_radius;
  double radius;
  double length;
  double sldCyl;
  double sldSolv;
  double background;
  double axis_theta;
  double axis_phi;
} HollowCylinderParameters;

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the hollow cylinder
 * @param q: q-value
 * @param q_x: q_x / q
 * @param q_y: q_y / q
 * @return: function value
 */
static double hollow_cylinder_analytical_2D_scaled(HollowCylinderParameters *pars, double q, double q_x, double q_y) {
  double cyl_x, cyl_y, cyl_z;
  double q_z;
  double  alpha,vol, cos_val;
  double answer;
  //convert angle degree to radian
  double pi = 4.0*atan(1.0);
  double theta = pars->axis_theta * pi/180.0;
  double phi = pars->axis_phi * pi/180.0;

  // Cylinder orientation
  cyl_x = sin(theta) * cos(phi);
  cyl_y = sin(theta) * sin(phi);
  cyl_z = cos(theta);

  // q vector
  q_z = 0;

  // Compute the angle btw vector q and the
  // axis of the cylinder
  cos_val = cyl_x*q_x + cyl_y*q_y + cyl_z*q_z;

  // The following test should always pass
  if (fabs(cos_val)>1.0) {
    printf("core_shell_cylinder_analytical_2D: Unexpected error: cos(alpha)=%g\n", cos_val);
    return 0;
  }

  alpha = acos( cos_val );

  // Call the IGOR library function to get the kernel
  answer = HolCylKernel(q, pars->core_radius, pars->radius, pars->length, cos_val);

  // Multiply by contrast^2
  answer *= (pars->sldCyl - pars->sldSolv)*(pars->sldCyl - pars->sldSolv);

  //normalize by cylinder volume
  vol=pi*((pars->radius*pars->radius)-(pars->core_radius *pars->core_radius))
          *(pars->length);
  answer *= vol;

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
 * @param pars: parameters of the Hollow cylinder
 * @param q: q-value
 * @return: function value
 */
static double hollow_cylinder_analytical_2DXY(HollowCylinderParameters *pars, double qx, double qy) {
  double q;
  q = sqrt(qx*qx+qy*qy);
  return hollow_cylinder_analytical_2D_scaled(pars, q, qx/q, qy/q);
}

HollowCylinderModel :: HollowCylinderModel() {
  scale      = Parameter(1.0);
  core_radius = Parameter(20.0, true);
  core_radius.set_min(0.0);
  radius  = Parameter(30.0, true);
  radius.set_min(0.0);
  length     = Parameter(400.0, true);
  length.set_min(0.0);
  sldCyl  = Parameter(6.3e-6);
  sldSolv  = Parameter(1.0e-6);
  background = Parameter(0.0);
  axis_theta = Parameter(0.0, true);
  axis_phi   = Parameter(0.0, true);
}

/**
 * Function to evaluate 1D scattering function
 * The NIST IGOR library is used for the actual calculation.
 * @param q: q-value
 * @return: function value
 */
double HollowCylinderModel :: operator()(double q) {
  double dp[7];

  dp[0] = scale();
  dp[1] = core_radius();
  dp[2] = radius();
  dp[3] = length();
  dp[4] = sldCyl();
  dp[5] = sldSolv();
  dp[6] = 0.0;

  // Get the dispersion points for the core radius
  vector<WeightPoint> weights_core_radius;
  core_radius.get_weights(weights_core_radius);

  // Get the dispersion points for the shell radius
  vector<WeightPoint> weights_radius;
  radius.get_weights(weights_radius);

  // Get the dispersion points for the length
  vector<WeightPoint> weights_length;
  length.get_weights(weights_length);

  // Perform the computation, with all weight points
  double sum = 0.0;
  double norm = 0.0;
  double vol = 0.0;

  // Loop over core radius weight points
  for(int i=0; i< (int)weights_core_radius.size(); i++) {
    dp[1] = weights_core_radius[i].value;

    // Loop over length weight points
    for(int j=0; j< (int)weights_length.size(); j++) {
      dp[3] = weights_length[j].value;

      // Loop over shell radius weight points
      for(int k=0; k< (int)weights_radius.size(); k++) {
        dp[2] = weights_radius[k].value;
        //Un-normalize  by volume
        sum += weights_core_radius[i].weight
            * weights_length[j].weight
            * weights_radius[k].weight
            * HollowCylinder(dp, q)
        * (pow(weights_radius[k].value,2)-pow(weights_core_radius[i].value,2))
        * weights_length[j].value;
        //Find average volume
        vol += weights_core_radius[i].weight
            * weights_length[j].weight
            * weights_radius[k].weight
            * (pow(weights_radius[k].value,2)-pow(weights_core_radius[i].value,2))
            * weights_length[j].value;

        norm += weights_core_radius[i].weight
            * weights_length[j].weight
            * weights_radius[k].weight;
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
double HollowCylinderModel :: operator()(double qx, double qy) {
  HollowCylinderParameters dp;
  // Fill parameter array
  dp.scale      = scale();
  dp.core_radius     = core_radius();
  dp.radius  = radius();
  dp.length     = length();
  dp.sldCyl   = sldCyl();
  dp.sldSolv  = sldSolv();
  dp.background = 0.0;
  dp.axis_theta = axis_theta();
  dp.axis_phi   = axis_phi();

  // Get the dispersion points for the core radius
  vector<WeightPoint> weights_core_radius;
  core_radius.get_weights(weights_core_radius);

  // Get the dispersion points for the shell radius
  vector<WeightPoint> weights_radius;
  radius.get_weights(weights_radius);

  // Get the dispersion points for the length
  vector<WeightPoint> weights_length;
  length.get_weights(weights_length);

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
  // Loop over core radius weight points
  for(int i=0; i<(int)weights_core_radius.size(); i++) {
    dp.core_radius = weights_core_radius[i].value;


    // Loop over length weight points
    for(int j=0; j<(int)weights_length.size(); j++) {
      dp.length = weights_length[j].value;

      // Loop over shell radius weight points
      for(int m=0; m< (int)weights_radius.size(); m++) {
        dp.radius = weights_radius[m].value;

        // Average over theta distribution
        for(int k=0; k< (int)weights_theta.size(); k++) {
          dp.axis_theta = weights_theta[k].value;

          // Average over phi distribution
          for(int l=0; l< (int)weights_phi.size(); l++) {
            dp.axis_phi = weights_phi[l].value;
            //Un-normalize by volume
            double _ptvalue = weights_core_radius[i].weight
                * weights_length[j].weight
                * weights_radius[m].weight
                * weights_theta[k].weight
                * weights_phi[l].weight
                * hollow_cylinder_analytical_2DXY(&dp, qx, qy)
            / ((pow(weights_radius[m].value,2)-pow(weights_core_radius[i].value,2))
                * weights_length[j].value);
            if (weights_theta.size()>1) {
              _ptvalue *= fabs(sin(weights_theta[k].value * pi/180.0));
            }
            sum += _ptvalue;
            //Find average volume
            vol += weights_core_radius[i].weight
                * weights_length[j].weight
                * weights_radius[m].weight
                * (pow(weights_radius[m].value,2)-pow(weights_core_radius[i].value,2))
                * weights_length[j].value;
            //Find norm for volume
            norm_vol += weights_core_radius[i].weight
                * weights_length[j].weight
                * weights_radius[m].weight;

            norm += weights_core_radius[i].weight
                * weights_length[j].weight
                * weights_radius[m].weight
                * weights_theta[k].weight
                * weights_phi[l].weight;

          }
        }
      }
    }
  }
  // Averaging in theta needs an extra normalization
  // factor to account for the sin(theta) term in the
  // integration (see documentation).
  if (weights_theta.size()>1) norm = norm/asin(1.0);
  if (vol != 0.0 || norm_vol != 0.0) {
    //Re-normalize by avg volume
    sum = sum*(vol/norm_vol);}
  return sum/norm + background();
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the  cylinder
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double HollowCylinderModel :: evaluate_rphi(double q, double phi) {
  double qx = q*cos(phi);
  double qy = q*sin(phi);
  return (*this).operator()(qx, qy);
}
/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double HollowCylinderModel :: calculate_ER() {
  HollowCylinderParameters dp;

  dp.radius  = radius();
  dp.length     = length();

  double rad_out = 0.0;

  // Perform the computation, with all weight points
  double sum = 0.0;
  double norm = 0.0;

  // Get the dispersion points for the major shell
  vector<WeightPoint> weights_length;
  length.get_weights(weights_length);

  // Get the dispersion points for the minor shell
  vector<WeightPoint> weights_radius ;
  radius.get_weights(weights_radius);

  // Loop over major shell weight points
  for(int i=0; i< (int)weights_length.size(); i++) {
    dp.length = weights_length[i].value;
    for(int k=0; k< (int)weights_radius.size(); k++) {
      dp.radius = weights_radius[k].value;
      //Note: output of "DiamCyl(dp.length,dp.radius)" is DIAMETER.
      sum +=weights_length[i].weight
          * weights_radius[k].weight*DiamCyl(dp.length,dp.radius)/2.0;
      norm += weights_length[i].weight* weights_radius[k].weight;
    }
  }
  if (norm != 0){
    //return the averaged value
    rad_out =  sum/norm;}
  else{
    //return normal value
    //Note: output of "DiamCyl(dp.length,dp.radius)" is DIAMETER.
    rad_out = DiamCyl(dp.length,dp.radius)/2.0;}

  return rad_out;
}
/**
 * Function to calculate volf_ratio for shell
 * @return: volf_ratio value
 */
double HollowCylinderModel :: calculate_VR() {
  HollowCylinderParameters dp;
  dp.core_radius = core_radius();
  dp.radius  = radius();
  dp.length  = length();

  double rad_out = 0.0;

  // Perform the computation, with all weight points
  double sum_tot = 0.0;
  double sum_shell = 0.0;

  // Get the dispersion points for the major shell
  vector<WeightPoint> weights_length;
  length.get_weights(weights_length);

  // Get the dispersion points for the minor shell
  vector<WeightPoint> weights_radius ;
  radius.get_weights(weights_radius);

  // Get the dispersion points for the core radius
  vector<WeightPoint> weights_core_radius;
  core_radius.get_weights(weights_core_radius);

  // Loop over major shell weight points
  for(int i=0; i< (int)weights_length.size(); i++) {
    dp.length = weights_length[i].value;
    for(int k=0; k< (int)weights_radius.size(); k++) {
      dp.radius = weights_radius[k].value;
      for(int j=0; j<(int)weights_core_radius.size(); j++) {
    	  dp.core_radius = weights_core_radius[j].value;
		  sum_tot +=weights_length[i].weight* weights_core_radius[j].weight
			  * weights_radius[k].weight*pow(dp.radius, 2);
		  sum_shell += weights_length[i].weight* weights_core_radius[j].weight
			  * weights_radius[k].weight*(pow(dp.radius, 2)-pow(dp.core_radius, 2));
      }
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
