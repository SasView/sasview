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
#include "fractal.h"

extern "C" {
#include "libTwoPhase.h"
}

FractalModel :: FractalModel() {
  scale      = Parameter(1.0);
  radius = Parameter(5.0, true);
  radius.set_min(0.0);
  fractal_dim = Parameter(2.0);
  cor_length = Parameter(100.0);
  sldBlock = Parameter(2.0e-6);
  sldSolv= Parameter(6.35e-6);
  background = Parameter(0.0);
}

/**
 * Function to evaluate 1D scattering function
 * The NIST IGOR library is used for the actual calculation.
 * @param q: q-value
 * @return: function value
 */
double FractalModel :: operator()(double q) {
  double dp[7];

  // Fill parameter array for IGOR library
  // Add the background after averaging
  dp[0] = scale();
  dp[1] = radius();
  dp[2] = fractal_dim();
  dp[3] = cor_length();
  dp[4] = sldBlock();
  dp[5] = sldSolv();
  dp[6] = 0.0;

  // Get the dispersion points for the radius
  vector<WeightPoint> weights_rad;
  radius.get_weights(weights_rad);

  // Perform the computation, with all weight points
  double sum = 0.0;
  double norm = 0.0;
  double vol = 0.0;

  // Loop over radius weight points
  for(size_t i=0; i<weights_rad.size(); i++) {
    dp[1] = weights_rad[i].value;

    //Un-normalize Fractal by volume
    sum += weights_rad[i].weight
        * Fractal(dp, fabs(q)) * pow(weights_rad[i].value,3);
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
double FractalModel :: operator()(double qx, double qy) {
  double q = sqrt(qx*qx + qy*qy);
  return (*this).operator()(q);
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the FractalModel
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double FractalModel :: evaluate_rphi(double q, double phi) {
  return (*this).operator()(q);
}

/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double FractalModel :: calculate_ER() {
  //NOT implemented yet!!! 'cause None shape Model
  return 0.0;
}
double FractalModel :: calculate_VR() {
  return 1.0;
}
