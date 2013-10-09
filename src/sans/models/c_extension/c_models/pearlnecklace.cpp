
#include <math.h>
#include "parameters.hh"
#include <stdio.h>
using namespace std;
#include "pearlnecklace.h"

extern "C" {
#include "libmultifunc/libfunc.h"
}

static double pearl_necklace_kernel(double dp[], double q) {
  // fit parameters
  double scale = dp[0];
  double radius = dp[1];
  double edge_separation = dp[2];
  double thick_string = dp[3];
  double num_pearls = dp[4];
  double sld_pearl = dp[5];
  double sld_string = dp[6];
  double sld_solv = dp[7];
  double background = dp[8];

  //relative slds
  double contrast_pearl = sld_pearl - sld_solv;
  double contrast_string = sld_string - sld_solv;

  // number of string segments
  double num_strings = num_pearls - 1.0;

  //Pi
  double pi = 4.0*atan(1.0);

  // each volumes
  double string_vol = edge_separation * pi * pow((thick_string / 2.0), 2);
  double pearl_vol = 4.0 /3.0 * pi * pow(radius, 3);

  //total volume
  double tot_vol;
  //each masses
  double m_r= contrast_string * string_vol;
  double m_s= contrast_pearl * pearl_vol;
  double psi;
  double gamma;
  double beta;
  //form factors
  double sss; //pearls
  double srr; //strings
  double srs; //cross
  double A_s;
  double srr_1;
  double srr_2;
  double srr_3;
  double form_factor;

  tot_vol = num_strings * string_vol;
  tot_vol += num_pearls * pearl_vol;

  //sine functions of a pearl
  psi = sin(q*radius);
  psi -= q * radius * cos(q * radius);
  psi /= pow((q * radius), 3);
  psi *= 3.0;

  // Note take only 20 terms in Si series: 10 terms may be enough though.
  gamma = Si(q* edge_separation);
  gamma /= (q* edge_separation);
  beta = Si(q * (edge_separation + radius));
  beta -= Si(q * radius);
  beta /= (q* edge_separation);

  // center to center distance between the neighboring pearls
  A_s = edge_separation + 2.0 * radius;

  // form factor for num_pearls
  sss = 1.0 - pow(sinc(q*A_s), num_pearls );
  sss /= pow((1.0-sinc(q*A_s)), 2);
  sss *= -sinc(q*A_s);
  sss -= num_pearls/2.0;
  sss += num_pearls/(1.0-sinc(q*A_s));
  sss *= 2.0 * pow((m_s*psi), 2);

  // form factor for num_strings (like thin rods)
  srr_1 = -pow(sinc(q*edge_separation/2.0), 2);

  srr_1 += 2.0 * gamma;
  srr_1 *= num_strings;
  srr_2 = 2.0/(1.0-sinc(q*A_s));
  srr_2 *= num_strings;
  srr_2 *= pow(beta, 2);
  srr_3 = 1.0 - pow(sinc(q*A_s), num_strings);
  srr_3 /= pow((1.0-sinc(q*A_s)), 2);
  srr_3 *= pow(beta, 2);
  srr_3 *= -2.0;

  // total srr
  srr = srr_1 + srr_2 + srr_3;
  srr *= pow(m_r, 2);

  // form factor for correlations
  srs = 1.0;
  srs -= pow(sinc(q*A_s), num_strings);
  srs /= pow((1.0-sinc(q*A_s)), 2);
  srs *= -sinc(q*A_s);
  srs += (num_strings/(1.0-sinc(q*A_s)));
  srs *= 4.0;
  srs *= (m_r * m_s * beta * psi);

  form_factor = sss + srr + srs;
  form_factor /= (tot_vol * 1.0e-8); // norm by volume and A^-1 to cm^-1

  // scale and background
  form_factor *= scale;
  form_factor += background;
  return (form_factor);
}

PearlNecklaceModel :: PearlNecklaceModel() {
  scale = Parameter(1.0);
  radius = Parameter(80.0, true);
  radius.set_min(0.0);
  edge_separation = Parameter(350.0, true);
  edge_separation.set_min(0.0);
  thick_string = Parameter(2.5, true);
  thick_string.set_min(0.0);
  num_pearls = Parameter(3);
  num_pearls.set_min(0.0);
  sld_pearl = Parameter(1.0e-06);
  sld_string = Parameter(1.0e-06);
  sld_solv = Parameter(6.3e-06);
  background = Parameter(0.0);

}

/**
 * Function to evaluate 1D PearlNecklaceModel function
 * @param q: q-value
 * @return: function value
 */
double PearlNecklaceModel :: operator()(double q) {
  double dp[9];
  // Fill parameter array for IGOR library
  // Add the background after averaging
  dp[0] = scale();
  dp[1] = radius();
  dp[2] = edge_separation();
  dp[3] = thick_string();
  dp[4] = num_pearls();
  dp[5] = sld_pearl();
  dp[6] = sld_string();
  dp[7] = sld_solv();
  dp[8] = 0.0;
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
  double string_vol = 0.0;
  double pearl_vol = 0.0;
  double tot_vol = 0.0;
  // Loop over core weight points
  for(size_t i=0; i<weights_radius.size(); i++) {
    dp[1] = weights_radius[i].value;
    // Loop over thick_inter0 weight points
    for(size_t j=0; j<weights_edge_separation.size(); j++) {
      dp[2] = weights_edge_separation[j].value;
      pearl_vol = 4.0 /3.0 * pi * pow(dp[1], 3);
      string_vol =dp[2] * pi * pow((dp[3] / 2.0), 2);
      tot_vol = (dp[4] - 1.0) * string_vol;
      tot_vol += dp[4] * pearl_vol;
      //Un-normalize Sphere by volume
      sum += weights_radius[i].weight * weights_edge_separation[j].weight
          * pearl_necklace_kernel(dp,q) * tot_vol;
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
 * Function to evaluate 2D PearlNecklaceModel function
 * @param q_x: value of Q along x
 * @param q_y: value of Q along y
 * @return: function value
 */
double PearlNecklaceModel :: operator()(double qx, double qy) {
  double q = sqrt(qx*qx + qy*qy);
  return (*this).operator()(q);
}

/**
 * Function to evaluate PearlNecklaceModel function
 * @param pars: parameters of the PearlNecklaceModel
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double PearlNecklaceModel :: evaluate_rphi(double q, double phi) {
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
double PearlNecklaceModel :: calculate_ER() {
  PeralNecklaceParameters dp;

  dp.scale = scale();
  dp.radius = radius();
  dp.edge_separation = edge_separation();
  dp.thick_string = thick_string();
  dp.num_pearls = num_pearls();

  double rad_out = 0.0;
  // Perform the computation, with all weight points
  double sum = 0.0;
  double norm = 0.0;
  double pi = 4.0*atan(1.0);
  // No polydispersion supported in this model.
  // Get the dispersion points for the radius
  vector<WeightPoint> weights_radius;
  radius.get_weights(weights_radius);
  vector<WeightPoint> weights_edge_separation;
  edge_separation.get_weights(weights_edge_separation);
  // Perform the computation, with all weight points
  double string_vol = 0.0;
  double pearl_vol = 0.0;
  double tot_vol = 0.0;
  // Loop over core weight points
  for(size_t i=0; i<weights_radius.size(); i++) {
    dp.radius = weights_radius[i].value;
    // Loop over thick_inter0 weight points
    for(size_t j=0; j<weights_edge_separation.size(); j++) {
      dp.edge_separation = weights_edge_separation[j].value;
      pearl_vol = 4.0 /3.0 * pi * pow(dp.radius , 3);
      string_vol =dp.edge_separation * pi * pow((dp.thick_string / 2.0), 2);
      tot_vol = (dp.num_pearls - 1.0) * string_vol;
      tot_vol += dp.num_pearls * pearl_vol;
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
    string_vol =dp.edge_separation * pi * pow((dp.thick_string / 2.0), 2);
    tot_vol = (dp.num_pearls - 1.0) * string_vol;
    tot_vol += dp.num_pearls * pearl_vol;

    rad_out =  pow((3.0*tot_vol/4.0/pi), 0.33333);
  }

  return rad_out;

}
double PearlNecklaceModel :: calculate_VR() {
  return 1.0;
}
