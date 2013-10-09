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
#include "ellipsoid.h"

extern "C" {
#include "libCylinder.h"
#include "libStructureFactor.h"
}

typedef struct {
  double scale;
  double radius_a;
  double radius_b;
  double sldEll;
  double sldSolv;
  double background;
  double axis_theta;
  double axis_phi;
} EllipsoidParameters;

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the ellipsoid
 * @param q: q-value
 * @param q_x: q_x / q
 * @param q_y: q_y / q
 * @return: function value
 */
static double ellipsoid_analytical_2D_scaled(EllipsoidParameters *pars, double q, double q_x, double q_y) {
  double cyl_x, cyl_y;//, cyl_z;
  //double q_z;
  double alpha, vol, cos_val;
  double answer;
  //convert angle degree to radian
  double pi = 4.0*atan(1.0);
  double theta = pars->axis_theta * pi/180.0;
  double phi = pars->axis_phi * pi/180.0;

  // Ellipsoid orientation
  cyl_x = cos(theta) * cos(phi);
  cyl_y = sin(theta);
  //cyl_z = -cos(theta) * sin(phi);

  // q vector
  //q_z = 0.0;

  // Compute the angle btw vector q and the
  // axis of the cylinder
  cos_val = cyl_x*q_x + cyl_y*q_y;// + cyl_z*q_z;

  // The following test should always pass
  if (fabs(cos_val)>1.0) {
    printf("ellipsoid_ana_2D: Unexpected error: cos(alpha)>1\n");
    return 0;
  }

  // Angle between rotation axis and q vector
  alpha = acos( cos_val );

  // Call the IGOR library function to get the kernel
  answer = EllipsoidKernel(q, pars->radius_b, pars->radius_a, cos_val);

  // Multiply by contrast^2
  answer *= (pars->sldEll - pars->sldSolv) * (pars->sldEll - pars->sldSolv);

  //normalize by cylinder volume
  vol = 4.0/3.0 * acos(-1.0) * pars->radius_b * pars->radius_b * pars->radius_a;
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
 * @param pars: parameters of the ellipsoid
 * @param q: q-value
 * @return: function value
 */
static double ellipsoid_analytical_2DXY(EllipsoidParameters *pars, double qx, double qy) {
  double q;
  q = sqrt(qx*qx+qy*qy);
  return ellipsoid_analytical_2D_scaled(pars, q, qx/q, qy/q);
}

EllipsoidModel :: EllipsoidModel() {
  scale      = Parameter(1.0);
  radius_a   = Parameter(20.0, true);
  radius_a.set_min(0.0);
  radius_b   = Parameter(400.0, true);
  radius_b.set_min(0.0);
  sldEll   = Parameter(4.e-6);
  sldSolv   = Parameter(1.e-6);
  background = Parameter(0.0);
  axis_theta  = Parameter(57.325, true);
  axis_phi    = Parameter(0.0, true);
}

/**
 * Function to evaluate 1D scattering function
 * The NIST IGOR library is used for the actual calculation.
 * @param q: q-value
 * @return: function value
 */
double EllipsoidModel :: operator()(double q) {
  double dp[6];

  // Fill parameter array for IGOR library
  // Add the background after averaging
  dp[0] = scale();
  dp[1] = radius_a();
  dp[2] = radius_b();
  dp[3] = sldEll();
  dp[4] = sldSolv();
  dp[5] = 0.0;

  // Get the dispersion points for the radius_a
  vector<WeightPoint> weights_rad_a;
  radius_a.get_weights(weights_rad_a);

  // Get the dispersion points for the radius_b
  vector<WeightPoint> weights_rad_b;
  radius_b.get_weights(weights_rad_b);

  // Perform the computation, with all weight points
  double sum = 0.0;
  double norm = 0.0;
  double vol = 0.0;

  // Loop over radius_a weight points
  for(size_t i=0; i<weights_rad_a.size(); i++) {
    dp[1] = weights_rad_a[i].value;

    // Loop over radius_b weight points
    for(size_t j=0; j<weights_rad_b.size(); j++) {
      dp[2] = weights_rad_b[j].value;
      //Un-normalize  by volume
      sum += weights_rad_a[i].weight
          * weights_rad_b[j].weight * EllipsoidForm(dp, q)
      * pow(weights_rad_b[j].value,2) * weights_rad_a[i].value;

      //Find average volume
      vol += weights_rad_a[i].weight
          * weights_rad_b[j].weight
          * pow(weights_rad_b[j].value,2)
      * weights_rad_a[i].value;
      norm += weights_rad_a[i].weight
          * weights_rad_b[j].weight;
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
double EllipsoidModel :: operator()(double qx, double qy) {
  EllipsoidParameters dp;
  // Fill parameter array
  dp.scale      = scale();
  dp.radius_a   = radius_a();
  dp.radius_b   = radius_b();
  dp.sldEll   = sldEll();
  dp.sldSolv   = sldSolv();
  dp.background = 0.0;
  dp.axis_theta = axis_theta();
  dp.axis_phi   = axis_phi();

  // Get the dispersion points for the radius_a
  vector<WeightPoint> weights_rad_a;
  radius_a.get_weights(weights_rad_a);

  // Get the dispersion points for the radius_b
  vector<WeightPoint> weights_rad_b;
  radius_b.get_weights(weights_rad_b);

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
  for(size_t i=0; i<weights_rad_a.size(); i++) {
    dp.radius_a = weights_rad_a[i].value;


    // Loop over length weight points
    for(size_t j=0; j<weights_rad_b.size(); j++) {
      dp.radius_b = weights_rad_b[j].value;

      // Average over theta distribution
      for(size_t k=0; k<weights_theta.size(); k++) {
        dp.axis_theta = weights_theta[k].value;

        // Average over phi distribution
        for(size_t l=0; l<weights_phi.size(); l++) {
          dp.axis_phi = weights_phi[l].value;
          //Un-normalize by volume
          double _ptvalue = weights_rad_a[i].weight
              * weights_rad_b[j].weight
              * weights_theta[k].weight
              * weights_phi[l].weight
              * ellipsoid_analytical_2DXY(&dp, qx, qy)
          * pow(weights_rad_b[j].value,2) * weights_rad_a[i].value;
          if (weights_theta.size()>1) {
            _ptvalue *= fabs(cos(weights_theta[k].value*pi/180.0));
          }
          sum += _ptvalue;
          //Find average volume
          vol += weights_rad_a[i].weight
              * weights_rad_b[j].weight
              * pow(weights_rad_b[j].value,2) * weights_rad_a[i].value;
          //Find norm for volume
          norm_vol += weights_rad_a[i].weight
              * weights_rad_b[j].weight;

          norm += weights_rad_a[i].weight
              * weights_rad_b[j].weight
              * weights_theta[k].weight
              * weights_phi[l].weight;

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
double EllipsoidModel :: evaluate_rphi(double q, double phi) {
  double qx = q*cos(phi);
  double qy = q*sin(phi);
  return (*this).operator()(qx, qy);
}

/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double EllipsoidModel :: calculate_ER() {
  EllipsoidParameters dp;

  dp.radius_a = radius_a();
  dp.radius_b = radius_b();

  double rad_out = 0.0;

  // Perform the computation, with all weight points
  double sum = 0.0;
  double norm = 0.0;

  // Get the dispersion points for the major shell
  vector<WeightPoint> weights_radius_a;
  radius_a.get_weights(weights_radius_a);

  // Get the dispersion points for the minor shell
  vector<WeightPoint> weights_radius_b;
  radius_b.get_weights(weights_radius_b);

  // Loop over major shell weight points
  for(int i=0; i< (int)weights_radius_b.size(); i++) {
    dp.radius_b = weights_radius_b[i].value;
    for(int k=0; k< (int)weights_radius_a.size(); k++) {
      dp.radius_a = weights_radius_a[k].value;
      sum +=weights_radius_b[i].weight
          * weights_radius_a[k].weight*DiamEllip(dp.radius_a,dp.radius_b)/2.0;
      norm += weights_radius_b[i].weight* weights_radius_a[k].weight;
    }
  }
  if (norm != 0){
    //return the averaged value
    rad_out =  sum/norm;}
  else{
    //return normal value
    rad_out = DiamEllip(dp.radius_a,dp.radius_b)/2.0;}

  return rad_out;
}
double EllipsoidModel :: calculate_VR() {
  return 1.0;
}
