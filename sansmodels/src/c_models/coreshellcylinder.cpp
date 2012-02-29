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
#include "core_shell_cylinder.h"

extern "C" {
#include "libCylinder.h"
#include "libStructureFactor.h"
}

typedef struct {
  double scale;
  double radius;
  double thickness;
  double length;
  double core_sld;
  double shell_sld;
  double solvent_sld;
  double background;
  double axis_theta;
  double axis_phi;
} CoreShellCylinderParameters;


/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the core-shell cylinder
 * @param q: q-value
 * @param q_x: q_x / q
 * @param q_y: q_y / q
 * @return: function value
 */
static double core_shell_cylinder_analytical_2D_scaled(CoreShellCylinderParameters *pars, double q, double q_x, double q_y) {
  double cyl_x, cyl_y, cyl_z;
  double q_z;
  double alpha, vol, cos_val;
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
  answer = CoreShellCylKernel(q, pars->radius, pars->thickness,
      pars->core_sld,pars->shell_sld,
      pars->solvent_sld, pars->length/2.0, alpha) / fabs(sin(alpha));

  //normalize by cylinder volume
  vol=pi*(pars->radius+pars->thickness)
          *(pars->radius+pars->thickness)
          *(pars->length+2.0*pars->thickness);
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
 * @param pars: parameters of the core-shell cylinder
 * @param q: q-value
 * @return: function value
 */
static double core_shell_cylinder_analytical_2DXY(CoreShellCylinderParameters *pars, double qx, double qy) {
  double q;
  q = sqrt(qx*qx+qy*qy);
  return core_shell_cylinder_analytical_2D_scaled(pars, q, qx/q, qy/q);
}


CoreShellCylinderModel :: CoreShellCylinderModel() {
  scale      = Parameter(1.0);
  radius     = Parameter(20.0, true);
  radius.set_min(0.0);
  thickness  = Parameter(10.0, true);
  thickness.set_min(0.0);
  length     = Parameter(400.0, true);
  length.set_min(0.0);
  core_sld   = Parameter(1.e-6);
  shell_sld  = Parameter(4.e-6);
  solvent_sld= Parameter(1.e-6);
  background = Parameter(0.0);
  axis_theta = Parameter(90.0, true);
  axis_phi   = Parameter(0.0, true);
}

/**
 * Function to evaluate 1D scattering function
 * The NIST IGOR library is used for the actual calculation.
 * @param q: q-value
 * @return: function value
 */
double CoreShellCylinderModel :: operator()(double q) {
  double dp[8];

  dp[0] = scale();
  dp[1] = radius();
  dp[2] = thickness();
  dp[3] = length();
  dp[4] = core_sld();
  dp[5] = shell_sld();
  dp[6] = solvent_sld();
  dp[7] = 0.0;

  // Get the dispersion points for the radius
  vector<WeightPoint> weights_rad;
  radius.get_weights(weights_rad);

  // Get the dispersion points for the thickness
  vector<WeightPoint> weights_thick;
  thickness.get_weights(weights_thick);

  // Get the dispersion points for the length
  vector<WeightPoint> weights_len;
  length.get_weights(weights_len);

  // Perform the computation, with all weight points
  double sum = 0.0;
  double norm = 0.0;
  double vol = 0.0;

  // Loop over radius weight points
  for(size_t i=0; i<weights_rad.size(); i++) {
    dp[1] = weights_rad[i].value;

    // Loop over length weight points
    for(size_t j=0; j<weights_len.size(); j++) {
      dp[3] = weights_len[j].value;

      // Loop over thickness weight points
      for(size_t k=0; k<weights_thick.size(); k++) {
        dp[2] = weights_thick[k].value;
        //Un-normalize by volume
        sum += weights_rad[i].weight
            * weights_len[j].weight
            * weights_thick[k].weight
            * CoreShellCylinder(dp, q)
        * pow(weights_rad[i].value+weights_thick[k].value,2)
        *(weights_len[j].value+2.0*weights_thick[k].value);
        //Find average volume
        vol += weights_rad[i].weight
            * weights_len[j].weight
            * weights_thick[k].weight
            * pow(weights_rad[i].value+weights_thick[k].value,2)
        *(weights_len[j].value+2.0*weights_thick[k].value);
        norm += weights_rad[i].weight
            * weights_len[j].weight
            * weights_thick[k].weight;
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
double CoreShellCylinderModel :: operator()(double qx, double qy) {
  CoreShellCylinderParameters dp;
  // Fill parameter array
  dp.scale      = scale();
  dp.radius     = radius();
  dp.thickness  = thickness();
  dp.length     = length();
  dp.core_sld   = core_sld();
  dp.shell_sld  = shell_sld();
  dp.solvent_sld= solvent_sld();
  dp.background = 0.0;
  dp.axis_theta = axis_theta();
  dp.axis_phi   = axis_phi();

  // Get the dispersion points for the radius
  vector<WeightPoint> weights_rad;
  radius.get_weights(weights_rad);

  // Get the dispersion points for the thickness
  vector<WeightPoint> weights_thick;
  thickness.get_weights(weights_thick);

  // Get the dispersion points for the length
  vector<WeightPoint> weights_len;
  length.get_weights(weights_len);

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
  // Loop over radius weight points
  for(size_t i=0; i<weights_rad.size(); i++) {
    dp.radius = weights_rad[i].value;


    // Loop over length weight points
    for(size_t j=0; j<weights_len.size(); j++) {
      dp.length = weights_len[j].value;

      // Loop over thickness weight points
      for(size_t m=0; m<weights_thick.size(); m++) {
        dp.thickness = weights_thick[m].value;

        // Average over theta distribution
        for(size_t k=0; k<weights_theta.size(); k++) {
          dp.axis_theta = weights_theta[k].value;

          // Average over phi distribution
          for(size_t l=0; l<weights_phi.size(); l++) {
            dp.axis_phi = weights_phi[l].value;
            //Un-normalize by volume
            double _ptvalue = weights_rad[i].weight
                * weights_len[j].weight
                * weights_thick[m].weight
                * weights_theta[k].weight
                * weights_phi[l].weight
                * core_shell_cylinder_analytical_2DXY(&dp, qx, qy)
            * pow(weights_rad[i].value+weights_thick[m].value,2)
            *(weights_len[j].value+2.0*weights_thick[m].value);

            if (weights_theta.size()>1) {
              _ptvalue *= fabs(sin(weights_theta[k].value*pi/180.0));
            }
            sum += _ptvalue;

            //Find average volume
            vol += weights_rad[i].weight
                * weights_len[j].weight
                * weights_thick[m].weight
                * pow(weights_rad[i].value+weights_thick[m].value,2)
            *(weights_len[j].value+2.0*weights_thick[m].value);
            //Find norm for volume
            norm_vol += weights_rad[i].weight
                * weights_len[j].weight
                * weights_thick[m].weight;

            norm += weights_rad[i].weight
                * weights_len[j].weight
                * weights_thick[m].weight
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
  if (weights_theta.size()>1) norm = norm / asin(1.0);

  if (vol != 0.0 && norm_vol != 0.0) {
    //Re-normalize by avg volume
    sum = sum/(vol/norm_vol);}

  return sum/norm + background();
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the cylinder
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double CoreShellCylinderModel :: evaluate_rphi(double q, double phi) {
  double qx = q*cos(phi);
  double qy = q*sin(phi);
  return (*this).operator()(qx, qy);
}
/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double CoreShellCylinderModel :: calculate_ER() {
  CoreShellCylinderParameters dp;

  dp.radius     = radius();
  dp.thickness  = thickness();
  dp.length     = length();
  double rad_out = 0.0;

  // Perform the computation, with all weight points
  double sum = 0.0;
  double norm = 0.0;

  // Get the dispersion points for the length
  vector<WeightPoint> weights_length;
  length.get_weights(weights_length);

  // Get the dispersion points for the thickness
  vector<WeightPoint> weights_thickness;
  thickness.get_weights(weights_thickness);

  // Get the dispersion points for the radius
  vector<WeightPoint> weights_radius ;
  radius.get_weights(weights_radius);

  // Loop over major shell weight points
  for(int i=0; i< (int)weights_length.size(); i++) {
    dp.length = weights_length[i].value;
    for(int j=0; j< (int)weights_thickness.size(); j++) {
      dp.thickness = weights_thickness[j].value;
      for(int k=0; k< (int)weights_radius.size(); k++) {
        dp.radius = weights_radius[k].value;
        //Note: output of "DiamCyl( )" is DIAMETER.
        sum +=weights_length[i].weight * weights_thickness[j].weight
            * weights_radius[k].weight*DiamCyl(dp.length+2.0*dp.thickness,dp.radius+dp.thickness)/2.0;
        norm += weights_length[i].weight* weights_thickness[j].weight* weights_radius[k].weight;
      }
    }
  }
  if (norm != 0){
    //return the averaged value
    rad_out =  sum/norm;}
  else{
    //return normal value
    //Note: output of "DiamCyl()" is DIAMETER.
    rad_out = DiamCyl(dp.length+2.0*dp.thickness,dp.radius+dp.thickness)/2.0;}

  return rad_out;
}
double CoreShellCylinderModel :: calculate_VR() {
  return 1.0;
}
