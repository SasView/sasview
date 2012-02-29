
#include <math.h>
#include "parameters.hh"
#include <stdio.h>
using namespace std;
#include "linearpearls.h"

extern "C" {
#include "libmultifunc/libfunc.h"
}

static double linear_pearls_kernel(double dp[], double q) {
  //fit parameters
  double scale = dp[0];
  double radius = dp[1];
  double edge_separation = dp[2];
  double num_pearls = dp[3];
  double sld_pearl = dp[4];
  double sld_solv = dp[5];
  double background = dp[6];
  //others
  double psi = 0.0;
  double n_contrib = 0.0;
  double form_factor = 0.0;
  //Pi
  double pi = 4.0 * atan(1.0);
  //relative sld
  double contrast_pearl = sld_pearl - sld_solv;
  //each volume
  double pearl_vol = 4.0 /3.0 * pi * pow(radius, 3.0);
  //total volume
  double tot_vol = num_pearls * pearl_vol;
  //mass
  double m_s = contrast_pearl * pearl_vol;
  //center to center distance between the neighboring pearls
  double separation = edge_separation + 2.0 * radius;
  //integer
  int num = 0;
  int n_max = 0;
  // constraints
  if (scale<=0 || radius<=0 || edge_separation<0 || num_pearls<=0){
	  return 0.0;
  }
  //sine functions of a pearl
  psi = sin(q * radius);
  psi -= q * radius * cos(q * radius);
  psi /= pow((q * radius), 3.0);

  // N pearls contribution
  n_max = num_pearls - 1;
  for(num=0; num<=n_max; num++) {

	  if (num == 0){
		  n_contrib = num_pearls;
		  continue;
	  }
	  n_contrib += (2.0*(num_pearls-double(num))*sinc(q*separation*double(num)));
  }
  // form factor for num_pearls
  form_factor = n_contrib;
  form_factor *= pow((m_s*psi*3.0), 2.0);
  form_factor /= (tot_vol * 1.0e-8); // norm by volume and A^-1 to cm^-1

  // scale and background
  form_factor *= scale;
  form_factor += background;
  return (form_factor);
}

LinearPearlsModel :: LinearPearlsModel() {
  scale = Parameter(1.0);
  radius = Parameter(80.0, true);
  radius.set_min(0.0);
  edge_separation = Parameter(350.0, true);
  edge_separation.set_min(0.0);
  num_pearls = Parameter(3);
  num_pearls.set_min(0.0);
  sld_pearl = Parameter(1.0e-06);
  sld_solv = Parameter(6.3e-06);
  background = Parameter(0.0);
}

/**
 * Function to evaluate 1D LinearPearlsModel function
 * @param q: q-value
 * @return: function value
 */
double LinearPearlsModel :: operator()(double q) {
  double dp[7];
  // Add the background after averaging
  dp[0] = scale();
  dp[1] = radius();
  dp[2] = edge_separation();
  dp[3] = num_pearls();
  dp[4] = sld_pearl();
  dp[5] = sld_solv();
  dp[6] = 0.0;
  double pi = 4.0*atan(1.0);
  // No polydispersion supported in this model.
  // Get the dispersion points for the radius
  vector<WeightPoint> weights_radius;
  radius.get_weights(weights_radius);
  vector<WeightPoint> weights_edge_separation;
  edge_separation.get_weights(weights_edge_separation);
  // Perform the computation, with all weight points
  double sum = 0.0;
  double norm = 0.0;
  double vol = 0.0;
  double pearl_vol = 0.0;
  double tot_vol = 0.0;
  // Loop over core weight points
  for(size_t i=0; i<weights_radius.size(); i++) {
    dp[1] = weights_radius[i].value;
    // Loop over thick_inter0 weight points
    for(size_t j=0; j<weights_edge_separation.size(); j++) {
      dp[2] = weights_edge_separation[j].value;
      pearl_vol = 4.0 /3.0 * pi * pow(dp[1], 3);
      tot_vol += dp[3] * pearl_vol;
      //Un-normalize Sphere by volume
      sum += weights_radius[i].weight * weights_edge_separation[j].weight
          * linear_pearls_kernel(dp,q) * tot_vol;
      //Find average volume
      vol += weights_radius[i].weight * weights_edge_separation[j].weight
          * tot_vol;
      norm += weights_radius[i].weight * weights_edge_separation[j].weight;
    }
  }
  if (vol != 0.0 && norm != 0.0) {
    //Re-normalize by avg volume
    sum = sum/(vol/norm);}
  return sum/norm + background();
}

/**
 * Function to evaluate 2D LinearPearlsModel function
 * @param q_x: value of Q along x
 * @param q_y: value of Q along y
 * @return: function value
 */
double LinearPearlsModel :: operator()(double qx, double qy) {
  double q = sqrt(qx*qx + qy*qy);
  return (*this).operator()(q);
}

/**
 * Function to evaluate LinearPearlsModel function
 * @param pars: parameters of the StringOfPearlsModel
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double LinearPearlsModel :: evaluate_rphi(double q, double phi) {
  return (*this).operator()(q);
}

/**
 * Function to calculate TOTAL radius
 * Todo: decide whether or not we keep this calculation
 * @return: effective radius value
 */
// No polydispersion supported in this model.
// Calculate max radius assumming max_radius = effective radius
// Note that this max radius is not affected by sld of layer, sld of interface, or
// sld of solvent.
double LinearPearlsModel :: calculate_ER() {
	LinearPearlsParameters dp;

  dp.scale = scale();
  dp.radius = radius();
  dp.edge_separation = edge_separation();
  dp.num_pearls = num_pearls();

  double rad_out = 0.0;
  // Perform the computation, with all weight points
  double sum = 0.0;
  double norm = 0.0;
  double pi = 4.0*atan(1.0);
  // Get the dispersion points for the radius
  vector<WeightPoint> weights_radius;
  radius.get_weights(weights_radius);
  vector<WeightPoint> weights_edge_separation;
  edge_separation.get_weights(weights_edge_separation);
  // Perform the computation, with all weight points
  double pearl_vol = 0.0;
  double tot_vol = 0.0;
  // Loop over core weight points
  for(size_t i=0; i<weights_radius.size(); i++) {
    dp.radius = weights_radius[i].value;
    // Loop over thick_inter0 weight points
    for(size_t j=0; j<weights_edge_separation.size(); j++) {
      dp.edge_separation = weights_edge_separation[j].value;
      pearl_vol = 4.0 /3.0 * pi * pow(dp.radius , 3);
      tot_vol = dp.num_pearls * pearl_vol;
      //Find  volume
      // This may be a too much approximation
      //Todo: decided whether or not we keep this calculation
      sum += weights_radius[i].weight * weights_edge_separation[j].weight
          * pow(3.0*tot_vol/4.0/pi,0.333333);
      norm += weights_radius[i].weight * weights_edge_separation[j].weight;
    }
  }

  if (norm != 0){
    //return the averaged value
    rad_out =  sum/norm;}
  else{
    //return normal value
    pearl_vol = 4.0 /3.0 * pi * pow(dp.radius , 3);
    tot_vol = dp.num_pearls * pearl_vol;

    rad_out =  pow((3.0*tot_vol/4.0/pi), 0.33333);
  }

  return rad_out;

}
double LinearPearlsModel :: calculate_VR() {
  return 1.0;
}
