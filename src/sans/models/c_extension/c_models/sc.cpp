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
#include "sc.h"

extern "C" {
#include "libSphere.h"
}

// Convenience structure
typedef struct {
  double scale;
  double dnn;
  double d_factor;
  double radius;
  double sldSph;
  double sldSolv;
  double background;
  double theta;
  double phi;
  double psi;
} SCParameters;

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the SCCrystalModel
 * @param q: q-value
 * @param q_x: q_x / q
 * @param q_y: q_y / q
 * @return: function value
 */
static double sc_analytical_2D_scaled(SCParameters *pars, double q, double q_x, double q_y) {
  double a3_x, a3_y, a2_x, a2_y, a1_x, a1_y; //, a3_z
  double q_z;
  double cos_val_a3, cos_val_a2, cos_val_a1;
  double a1_dot_q, a2_dot_q,a3_dot_q;
  double answer;
  double Pi = 4.0*atan(1.0);
  double aa, Da, qDa_2, latticeScale, Zq;

  double dp[5];
  //convert angle degree to radian
  double theta = pars->theta * Pi/180.0;
  double phi = pars->phi * Pi/180.0;
  double psi = pars->psi * Pi/180.0;
  dp[0] = 1.0;
  dp[1] = pars->radius;
  dp[2] = pars->sldSph;
  dp[3] = pars->sldSolv;
  dp[4] = 0.0;


  aa = pars->dnn;
  Da = pars->d_factor*aa;
  qDa_2 = pow(q*Da,2.0);

  latticeScale = (4.0/3.0)*Pi*(dp[1]*dp[1]*dp[1])/pow(aa,3.0);
  /// Angles here are respect to detector coordinate instead of against q coordinate(PRB 36, 3, 1754)
  // a3 axis orientation
  a3_x = cos(theta) * cos(phi);
  a3_y = sin(theta);
  //a3_z = -cos(theta) * sin(phi);
  // q vector
  q_z = 0.0;

  // Compute the angle btw vector q and the a3 axis
  cos_val_a3 = a3_x*q_x + a3_y*q_y;// + a3_z*q_z;

  // a1 axis orientation
  a1_x = -cos(phi)*sin(psi) * sin(theta)+sin(phi)*cos(psi);
  a1_y = sin(psi)*cos(theta);

  cos_val_a1 = a1_x*q_x + a1_y*q_y;

  // a2 axis orientation
  a2_x = -sin(theta)*cos(psi)*cos(phi)-sin(psi)*sin(phi);
  a2_y = cos(theta)*cos(psi);
  // a2 axis
  cos_val_a2 =  a2_x*q_x + a2_y*q_y;

  // The following test should always pass
  if (fabs(cos_val_a3)>1.0) {
    //printf("parallel_ana_2D: Unexpected error: cos(alpha)>1\n");
    cos_val_a3 = 1.0;
  }
   if (fabs(cos_val_a1)>1.0) {
    //printf("parallel_ana_2D: Unexpected error: cos(alpha)>1\n");
    cos_val_a1 = 1.0;
  }
   if (fabs(cos_val_a2)>1.0) {
    //printf("parallel_ana_2D: Unexpected error: cos(alpha)>1\n");
    cos_val_a3 = 1.0;
  }
  a3_dot_q = aa*q*cos_val_a3;
  a1_dot_q = aa*q*cos_val_a1;//*sin(alpha);
  a2_dot_q = aa*q*cos_val_a2;
  
  // Call Zq=Z1*Z2*Z3
  Zq = (1.0-exp(-qDa_2))/(1.0-2.0*exp(-0.5*qDa_2)*cos(a1_dot_q)+exp(-qDa_2));
  Zq *= (1.0-exp(-qDa_2))/(1.0-2.0*exp(-0.5*qDa_2)*cos(a2_dot_q)+exp(-qDa_2));
  Zq *= (1.0-exp(-qDa_2))/(1.0-2.0*exp(-0.5*qDa_2)*cos(a3_dot_q)+exp(-qDa_2));

  // Use SphereForm directly from libigor
  answer = SphereForm(dp,q)*Zq;

  //consider scales
  answer *= latticeScale * pars->scale;

  // This FIXES a singualrity the kernel in libigor.
  if ( answer == INFINITY || answer == NAN){
    answer = 0.0;
  }

  // add background
  answer += pars->background;

  return answer;
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the SC_ParaCrystal
 * @param q: q-value
 * @return: function value
 */
static double sc_analytical_2DXY(SCParameters *pars, double qx, double qy){
  double q;
  q = sqrt(qx*qx+qy*qy);
  return sc_analytical_2D_scaled(pars, q, qx/q, qy/q);
}

SCCrystalModel :: SCCrystalModel() {
  scale      = Parameter(1.0);
  dnn		= Parameter(220.0);
  d_factor = Parameter(0.06);
  radius     = Parameter(40.0, true);
  radius.set_min(0.0);
  sldSph   = Parameter(3.0e-6);
  sldSolv   = Parameter(6.3e-6);
  background = Parameter(0.0);
  theta  = Parameter(0.0, true);
  phi    = Parameter(0.0, true);
  psi    = Parameter(0.0, true);
}

/**
 * Function to evaluate 1D scattering function
 * The NIST IGOR library is used for the actual calculation.
 * @param q: q-value
 * @return: function value
 */
double SCCrystalModel :: operator()(double q) {
  double dp[7];

  // Fill parameter array for IGOR library
  // Add the background after averaging
  dp[0] = scale();
  dp[1] = dnn();
  dp[2] = d_factor();
  dp[3] = radius();
  dp[4] = sldSph();
  dp[5] = sldSolv();
  dp[6] = 0.0;

  // Get the dispersion points for the radius
  vector<WeightPoint> weights_rad;
  radius.get_weights(weights_rad);

  // Perform the computation, with all weight points
  double sum = 0.0;
  double norm = 0.0;
  double vol = 0.0;
  double result;

  // Loop over radius weight points
  for(size_t i=0; i<weights_rad.size(); i++) {
    dp[3] = weights_rad[i].value;

    //Un-normalize SphereForm by volume
    result = SC_ParaCrystal(dp, q) * pow(weights_rad[i].value,3);
    // This FIXES a singualrity the kernel in libigor.
    if ( result == INFINITY || result == NAN){
      result = 0.0;
    }
    sum += weights_rad[i].weight
        * result;
    //Find average volume
    vol += weights_rad[i].weight
        * pow(weights_rad[i].value,3);

    norm += weights_rad[i].weight;
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
double SCCrystalModel :: operator()(double qx, double qy) {
  SCParameters dp;
  dp.scale      = scale();
  dp.dnn   = dnn();
  dp.d_factor   = d_factor();
  dp.radius  = radius();
  dp.sldSph   = sldSph();
  dp.sldSolv   = sldSolv();
  dp.background = 0.0;
  dp.theta  = theta();
  dp.phi    = phi();
  dp.psi    = psi();

  // Get the dispersion points for the radius
  vector<WeightPoint> weights_rad;
  radius.get_weights(weights_rad);

  // Get angular averaging for theta
  vector<WeightPoint> weights_theta;
  theta.get_weights(weights_theta);

  // Get angular averaging for phi
  vector<WeightPoint> weights_phi;
  phi.get_weights(weights_phi);

  // Get angular averaging for psi
  vector<WeightPoint> weights_psi;
  psi.get_weights(weights_psi);

  // Perform the computation, with all weight points
  double sum = 0.0;
  double norm = 0.0;
  double norm_vol = 0.0;
  double vol = 0.0;
  double pi = 4.0*atan(1.0);
  // Loop over radius weight points
  for(size_t i=0; i<weights_rad.size(); i++) {
    dp.radius = weights_rad[i].value;
    // Average over theta distribution
    for(size_t j=0; j< weights_theta.size(); j++) {
      dp.theta = weights_theta[j].value;
      // Average over phi distribution
      for(size_t k=0; k< weights_phi.size(); k++) {
        dp.phi = weights_phi[k].value;
        // Average over phi distribution
        for(size_t l=0; l< weights_psi.size(); l++) {
          dp.psi = weights_psi[l].value;
          //Un-normalize SphereForm by volume
          double _ptvalue = weights_rad[i].weight
              * weights_theta[j].weight
              * weights_phi[k].weight
              * weights_psi[l].weight
              * sc_analytical_2DXY(&dp, qx, qy);
          //* pow(weights_rad[i].value,3.0);
          // Consider when there is infinte or nan.
          if ( _ptvalue == INFINITY || _ptvalue == NAN){
            _ptvalue = 0.0;
          }
          if (weights_theta.size()>1) {
            _ptvalue *= fabs(cos(weights_theta[j].value*pi/180.0));
          }
          sum += _ptvalue;
          // This model dose not need the volume of spheres correction!!!
          //Find average volume
          //vol += weights_rad[i].weight
          //	* pow(weights_rad[i].value,3);
          //Find norm for volume
          //norm_vol += weights_rad[i].weight;

          norm += weights_rad[i].weight
              * weights_theta[j].weight
              * weights_phi[k].weight
              * weights_psi[l].weight;
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
 * @param pars: parameters of the SCCrystal
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double SCCrystalModel :: evaluate_rphi(double q, double phi) {
  return (*this).operator()(q);
}

/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double SCCrystalModel :: calculate_ER() {
  //NOT implemented yet!!!
  return 0.0;
}
double SCCrystalModel :: calculate_VR() {
  return 1.0;
}
