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
#include "Hardsphere.h"

extern "C" {
#include "libStructureFactor.h"
}

HardsphereStructure :: HardsphereStructure() {
  effect_radius      = Parameter(50.0, true);
  effect_radius.set_min(0.0);
  volfraction = Parameter(0.20, true);
  volfraction.set_min(0.0);
}

/**
 * Function to evaluate 1D scattering function
 * The NIST IGOR library is used for the actual calculation.
 * @param q: q-value
 * @return: function value
 */
double HardsphereStructure :: operator()(double q) {
  double dp[2];

  // Fill parameter array for IGOR library
  // Add the background after averaging
  dp[0] = effect_radius();
  dp[1] = volfraction();

  // Get the dispersion points for the radius
  vector<WeightPoint> weights_rad;
  effect_radius.get_weights(weights_rad);

  // Perform the computation, with all weight points
  double sum = 0.0;
  double norm = 0.0;

  // Loop over radius weight points
  for(size_t i=0; i<weights_rad.size(); i++) {
    dp[0] = weights_rad[i].value;

    sum += weights_rad[i].weight
        * HardSphereStruct(dp, q);
    norm += weights_rad[i].weight;
  }
  return sum/norm ;
}

/**
 * Function to evaluate 2D scattering function
 * @param q_x: value of Q along x
 * @param q_y: value of Q along y
 * @return: function value
 */
double HardsphereStructure :: operator()(double qx, double qy) {
  double q = sqrt(qx*qx + qy*qy);
  return (*this).operator()(q);
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the cylinder
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double HardsphereStructure :: evaluate_rphi(double q, double phi) {
  double qx = q*cos(phi);
  double qy = q*sin(phi);
  return (*this).operator()(qx, qy);
}
/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double HardsphereStructure :: calculate_ER() {
  //NOT implemented yet!!!
  return 0.0;
}
double HardsphereStructure :: calculate_VR() {
  return 1.0;
}
