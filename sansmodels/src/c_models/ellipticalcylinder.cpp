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
#include "elliptical_cylinder.h"

extern "C" {
#include "libCylinder.h"
#include "libStructureFactor.h"
}

typedef struct {
  double scale;
  double r_minor;
  double r_ratio;
  double length;
  double sldCyl;
  double sldSolv;
  double background;
  double cyl_theta;
  double cyl_phi;
  double cyl_psi;
} EllipticalCylinderParameters;


static double elliptical_cylinder_kernel(EllipticalCylinderParameters *pars, double q, double alpha, double nu) {
  double qr;
  double qL;
  double Be,Si;
  double r_major;
  double kernel;

  r_major = pars->r_ratio * pars->r_minor;

  qr = q*sin(alpha)*sqrt( r_major*r_major*sin(nu)*sin(nu) + pars->r_minor*pars->r_minor*cos(nu)*cos(nu) );
  qL = q*pars->length*cos(alpha)/2.0;

  if (qr==0){
    Be = 0.5;
  }else{
    Be = NR_BessJ1(qr)/qr;
  }
  if (qL==0){
    Si = 1.0;
  }else{
    Si = sin(qL)/qL;
  }


  kernel = 2.0*Be * Si;
  return kernel*kernel;
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the cylinder
 * @param q: q-value
 * @param q_x: q_x / q
 * @param q_y: q_y / q
 * @return: function value
 */
static double elliptical_cylinder_analytical_2D_scaled(EllipticalCylinderParameters *pars, double q, double q_x, double q_y) {
  double cyl_x, cyl_y, cyl_z;
  double ell_x, ell_y;
  double q_z;
  double alpha, vol, cos_val;
  double nu, cos_nu;
  double answer;
  //convert angle degree to radian
  double pi = 4.0*atan(1.0);
  double theta = pars->cyl_theta * pi/180.0;
  double phi = pars->cyl_phi * pi/180.0;
  double psi = pars->cyl_psi * pi/180.0;

  //Cylinder orientation
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
    printf("cyl_ana_2D: Unexpected error: cos(alpha)>1\n");
    return 0;
  }

  // Note: cos(alpha) = 0 and 1 will get an
  // undefined value from CylKernel
  alpha = acos( cos_val );

  //ellipse orientation:
  // the elliptical corss section was transformed and projected
  // into the detector plane already through sin(alpha)and furthermore psi remains as same
  // on the detector plane.
  // So, all we need is to calculate the angle (nu) of the minor axis of the ellipse wrt
  // the wave vector q.

  //x- y- component on the detector plane.
  ell_x =  cos(psi);
  ell_y =  sin(psi);

  // calculate the axis of the ellipse wrt q-coord.
  cos_nu = ell_x*q_x + ell_y*q_y;
  nu = acos(cos_nu);

  // The following test should always pass
  if (fabs(cos_nu)>1.0) {
    printf("cyl_ana_2D: Unexpected error: cos(nu)>1\n");
    return 0;
  }

  answer = elliptical_cylinder_kernel(pars, q, alpha,nu);

  // Multiply by contrast^2
  answer *= (pars->sldCyl - pars->sldSolv) * (pars->sldCyl - pars->sldSolv);

  //normalize by cylinder volume
  //NOTE that for this (Fournet) definition of the integral, one must MULTIPLY by Vcyl
  vol = acos(-1.0) * pars->r_minor * pars->r_minor * pars->r_ratio * pars->length;
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
 * @param pars: parameters of the cylinder
 * @param q: q-value
 * @return: function value
 */
static double elliptical_cylinder_analytical_2DXY(EllipticalCylinderParameters *pars, double qx, double qy) {
  double q;
  q = sqrt(qx*qx+qy*qy);
  return elliptical_cylinder_analytical_2D_scaled(pars, q, qx/q, qy/q);
}

EllipticalCylinderModel :: EllipticalCylinderModel() {
  scale      = Parameter(1.0);
  r_minor    = Parameter(20.0, true);
  r_minor.set_min(0.0);
  r_ratio    = Parameter(1.5, true);
  r_ratio.set_min(0.0);
  length     = Parameter(400.0, true);
  length.set_min(0.0);
  sldCyl   = Parameter(4.e-6);
  sldSolv   = Parameter(1.e-6);
  background = Parameter(0.0);
  cyl_theta  = Parameter(57.325, true);
  cyl_phi    = Parameter(0.0, true);
  cyl_psi    = Parameter(0.0, true);
}

/**
 * Function to evaluate 1D scattering function
 * The NIST IGOR library is used for the actual calculation.
 * @param q: q-value
 * @return: function value
 */
double EllipticalCylinderModel :: operator()(double q) {
  double dp[7];

  dp[0] = scale();
  dp[1] = r_minor();
  dp[2] = r_ratio();
  dp[3] = length();
  dp[4] = sldCyl();
  dp[5] = sldSolv();
  dp[6] = 0.0;

  // Get the dispersion points for the r_minor
  vector<WeightPoint> weights_rad;
  r_minor.get_weights(weights_rad);

  // Get the dispersion points for the r_ratio
  vector<WeightPoint> weights_rat;
  r_ratio.get_weights(weights_rat);

  // Get the dispersion points for the length
  vector<WeightPoint> weights_len;
  length.get_weights(weights_len);

  // Perform the computation, with all weight points
  double sum = 0.0;
  double norm = 0.0;
  double vol = 0.0;

  // Loop over r_minor weight points
  for(size_t i=0; i<weights_rad.size(); i++) {
    dp[1] = weights_rad[i].value;

    // Loop over r_ratio weight points
    for(size_t j=0; j<weights_rat.size(); j++) {
      dp[2] = weights_rat[j].value;

      // Loop over length weight points
      for(size_t k=0; k<weights_len.size(); k++) {
        dp[3] = weights_len[k].value;
        //Un-normalize  by volume
        sum += weights_rad[i].weight
            * weights_len[k].weight
            * weights_rat[j].weight
            * EllipCyl20(dp, q)
        * pow(weights_rad[i].value,2) * weights_rat[j].value
        * weights_len[k].value;
        //Find average volume
        vol += weights_rad[i].weight
            * weights_len[k].weight
            * weights_rat[j].weight
            * pow(weights_rad[i].value,2) * weights_rat[j].value
            * weights_len[k].value;
        norm += weights_rad[i].weight
            * weights_len[k].weight
            * weights_rat[j].weight;
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
double EllipticalCylinderModel :: operator()(double qx, double qy) {
  EllipticalCylinderParameters dp;
  // Fill parameter array
  dp.scale      = scale();
  dp.r_minor    = r_minor();
  dp.r_ratio    = r_ratio();
  dp.length     = length();
  dp.sldCyl   = sldCyl();
  dp.sldSolv   = sldSolv();
  dp.background = 0.0;
  dp.cyl_theta  = cyl_theta();
  dp.cyl_phi    = cyl_phi();
  dp.cyl_psi    = cyl_psi();

  // Get the dispersion points for the r_minor
  vector<WeightPoint> weights_rad;
  r_minor.get_weights(weights_rad);

  // Get the dispersion points for the r_ratio
  vector<WeightPoint> weights_rat;
  r_ratio.get_weights(weights_rat);

  // Get the dispersion points for the length
  vector<WeightPoint> weights_len;
  length.get_weights(weights_len);

  // Get angular averaging for theta
  vector<WeightPoint> weights_theta;
  cyl_theta.get_weights(weights_theta);

  // Get angular averaging for phi
  vector<WeightPoint> weights_phi;
  cyl_phi.get_weights(weights_phi);

  // Get angular averaging for psi
  vector<WeightPoint> weights_psi;
  cyl_psi.get_weights(weights_psi);

  // Perform the computation, with all weight points
  double sum = 0.0;
  double norm = 0.0;
  double norm_vol = 0.0;
  double vol = 0.0;
  double pi = 4.0*atan(1.0);
  // Loop over minor radius weight points
  for(size_t i=0; i<weights_rad.size(); i++) {
    dp.r_minor = weights_rad[i].value;


    // Loop over length weight points
    for(size_t j=0; j<weights_len.size(); j++) {
      dp.length = weights_len[j].value;

      // Loop over r_ration weight points
      for(size_t m=0; m<weights_rat.size(); m++) {
        dp.r_ratio = weights_rat[m].value;

        // Average over theta distribution
        for(size_t k=0; k<weights_theta.size(); k++) {
          dp.cyl_theta = weights_theta[k].value;

          // Average over phi distribution
          for(size_t l=0; l<weights_phi.size(); l++) {
            dp.cyl_phi = weights_phi[l].value;

            // Average over phi distribution
            for(size_t o=0; o<weights_psi.size(); o++) {
              dp.cyl_psi = weights_psi[o].value;
              //Un-normalize by volume
              double _ptvalue = weights_rad[i].weight
                  * weights_len[j].weight
                  * weights_rat[m].weight
                  * weights_theta[k].weight
                  * weights_phi[l].weight
                  * weights_psi[o].weight
                  * elliptical_cylinder_analytical_2DXY(&dp, qx, qy)
              * pow(weights_rad[i].value,2)
              * weights_len[j].value
              * weights_rat[m].value;
              if (weights_theta.size()>1) {
                _ptvalue *= fabs(sin(weights_theta[k].value*pi/180.0));
              }
              sum += _ptvalue;
              //Find average volume
              vol += weights_rad[i].weight
                  * weights_len[j].weight
                  * weights_rat[m].weight
                  * pow(weights_rad[i].value,2)
              * weights_len[j].value
              * weights_rat[m].value;
              //Find norm for volume
              norm_vol += weights_rad[i].weight
                  * weights_len[j].weight
                  * weights_rat[m].weight;

              norm += weights_rad[i].weight
                  * weights_len[j].weight
                  * weights_rat[m].weight
                  * weights_theta[k].weight
                  * weights_phi[l].weight
                  * weights_psi[o].weight;

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
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the cylinder
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double EllipticalCylinderModel :: evaluate_rphi(double q, double phi) {
  double qx = q*cos(phi);
  double qy = q*sin(phi);
  return (*this).operator()(qx, qy);
}
/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double EllipticalCylinderModel :: calculate_ER() {
  EllipticalCylinderParameters dp;
  dp.r_minor    = r_minor();
  dp.r_ratio    = r_ratio();
  dp.length     = length();
  double rad_out = 0.0;
  double suf_rad = sqrt(dp.r_minor*dp.r_minor*dp.r_ratio);

  // Perform the computation, with all weight points
  double sum = 0.0;
  double norm = 0.0;

  // Get the dispersion points for the r_minor
  vector<WeightPoint> weights_rad;
  r_minor.get_weights(weights_rad);

  // Get the dispersion points for the r_ratio
  vector<WeightPoint> weights_rat;
  r_ratio.get_weights(weights_rat);

  // Get the dispersion points for the length
  vector<WeightPoint> weights_len;
  length.get_weights(weights_len);

  // Loop over minor radius weight points
  for(size_t i=0; i<weights_rad.size(); i++) {
    dp.r_minor = weights_rad[i].value;

    // Loop over length weight points
    for(size_t j=0; j<weights_len.size(); j++) {
      dp.length = weights_len[j].value;

      // Loop over r_ration weight points
      for(size_t m=0; m<weights_rat.size(); m++) {
        dp.r_ratio = weights_rat[m].value;
        //Calculate surface averaged radius
        suf_rad = sqrt(dp.r_minor * dp.r_minor * dp.r_ratio);

        //Note: output of "DiamCyl(dp.length,dp.radius)" is DIAMETER.
        sum +=weights_rad[i].weight *weights_len[j].weight
            * weights_rat[m].weight*DiamCyl(dp.length, suf_rad)/2.0;
        norm += weights_rad[i].weight *weights_len[j].weight* weights_rat[m].weight;
      }
    }
  }
  if (norm != 0){
    //return the averaged value
    rad_out =  sum/norm;}
  else{
    //return normal value
    //Note: output of "DiamCyl(dp.length,dp.radius)" is DIAMETER.
    rad_out = DiamCyl(dp.length, suf_rad)/2.0;}

  return rad_out;
}
double EllipticalCylinderModel :: calculate_VR() {
  return 1.0;
}
