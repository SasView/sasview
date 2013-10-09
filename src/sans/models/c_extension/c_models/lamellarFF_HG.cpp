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
#include "lamellarFF_HG.h"

extern "C" {
#include "libCylinder.h"
}

LamellarFFHGModel :: LamellarFFHGModel() {
  scale      = Parameter(1.0);
  t_length     = Parameter(15.0, true);
  t_length.set_min(0.0);
  h_thickness    = Parameter(10.0, true);
  h_thickness.set_min(0.0);
  sld_tail   = Parameter(4e-7);
  sld_head  = Parameter(3e-6);
  sld_solvent    = Parameter(6e-6);
  background = Parameter(0.0);

}

/**
 * Function to evaluate 1D scattering function
 * The NIST IGOR library is used for the actual calculation.
 * @param q: q-value
 * @return: function value
 */
double LamellarFFHGModel :: operator()(double q) {
  double dp[7];

  // Fill parameter array for IGOR library
  // Add the background after averaging
  dp[0] = scale();
  dp[1] = t_length();
  dp[2] = h_thickness();
  dp[3] = sld_tail();
  dp[4] = sld_head();
  dp[5] = sld_solvent();
  dp[6] = 0.0;

  // Get the dispersion points for the tail length
  vector<WeightPoint> weights_t_length;
  t_length.get_weights(weights_t_length);

  // Get the dispersion points for the head thickness
  vector<WeightPoint> weights_h_thickness;
  h_thickness.get_weights(weights_h_thickness);

  // Perform the computation, with all weight points
  double sum = 0.0;
  double norm = 0.0;

  // Loop over semi axis A weight points
  for(int i=0; i< (int)weights_t_length.size(); i++) {
    dp[1] = weights_t_length[i].value;

    for (int j=0; j< (int)weights_h_thickness.size(); j++){
      dp[2] = weights_h_thickness[j].value;

      sum += weights_t_length[i].weight* weights_h_thickness[j].weight*LamellarFF_HG(dp, q);
      norm += weights_t_length[i].weight* weights_h_thickness[j].weight;
    }

  }
  return sum/norm + background();
}

/**
 * Function to evaluate 2D scattering function
 * @param q_x: value of Q along x
 * @param q_y: value of Q along y
 * @return: function value
 */

double LamellarFFHGModel :: operator()(double qx, double qy) {
  double q = sqrt(qx*qx + qy*qy);
  return (*this).operator()(q);
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the lamellar
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double LamellarFFHGModel :: evaluate_rphi(double q, double phi) {
  return (*this).operator()(q);
}
/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double LamellarFFHGModel :: calculate_ER() {
  //NOT implemented yet!!!
  return 0.0;
}
double LamellarFFHGModel :: calculate_VR() {
  return 1.0;
}
