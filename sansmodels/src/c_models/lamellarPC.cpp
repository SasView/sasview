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
 */

#include <math.h>
#include "parameters.hh"
#include <stdio.h>
using namespace std;
#include "lamellarPC.h"

extern "C" {
#include "libCylinder.h"
}

LamellarPCrystalModel :: LamellarPCrystalModel() {
  scale      = Parameter(1.0);
  thickness     = Parameter(33.0, true);
  thickness.set_min(0.0);
  Nlayers    = Parameter(20.0, true);
  Nlayers.set_min(0.0);
  spacing   = Parameter(250);
  pd_spacing   = Parameter(0.0);
  sld_layer  = Parameter(1.0e-6);
  sld_solvent    = Parameter(6.34e-6);
  background = Parameter(0.0);

}

/**
 * Function to evaluate 1D scattering function
 * The NIST IGOR library is used for the actual calculation.
 * @param q: q-value
 * @return: function value
 */
double LamellarPCrystalModel :: operator()(double q) {
  double dp[8];

  // Fill parameter array for IGOR library
  // Add the background after averaging
  dp[0] = scale();
  dp[1] = thickness();
  dp[2] = Nlayers();
  dp[3] = spacing();
  dp[4] = pd_spacing();
  dp[5] = sld_layer();
  dp[6] = sld_solvent();
  dp[7] = 0.0; // Do not apply background here.

  // Get the dispersion points for the head thickness
  vector<WeightPoint> weights_thickness;
  thickness.get_weights(weights_thickness);

  // Let's provide from the func which is more accurate especially for small q region.
  // Get the dispersion points for the tail length
  //vector<WeightPoint> weights_spacing;
  //spacing.get_weights(weights_spacing);

  // Perform the computation, with all weight points
  double sum = 0.0;
  double norm = 0.0;

  // Loop over thickness and spacing weight points
  for(int i=0; i< (int)weights_thickness.size(); i++) {
    dp[1] = weights_thickness[i].value;
    //for (int j=0; j< (int)weights_spacing.size(); j++){
    //dp[3] = weights_spacing[j].value;
    sum += weights_thickness[i].weight*Lamellar_ParaCrystal(dp, q);
    norm += weights_thickness[i].weight;
    //}
  }
  //apply norm and background
  return sum/norm + background();
}

/**
 * Function to evaluate 2D scattering function
 * @param q_x: value of Q along x
 * @param q_y: value of Q along y
 * @return: function value
 */

double LamellarPCrystalModel :: operator()(double qx, double qy) {
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
double LamellarPCrystalModel :: evaluate_rphi(double q, double phi) {
  return (*this).operator()(q);
}
/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double LamellarPCrystalModel :: calculate_ER() {
  //NOT implemented yet!!!
  return 0.0;
}
double LamellarPCrystalModel :: calculate_VR() {
  return 1.0;
}
