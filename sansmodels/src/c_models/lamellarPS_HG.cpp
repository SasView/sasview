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
 *	TODO: add 2D function
 */

#include <math.h>
#include "parameters.hh"
#include <stdio.h>
using namespace std;
#include "lamellarPS_HG.h"

extern "C" {
	#include "libCylinder.h"
}

LamellarPSHGModel :: LamellarPSHGModel() {
	scale      = Parameter(1.0);
	spacing    = Parameter(40.0, true);
	spacing.set_min(0.0);
	deltaT     = Parameter(10.0, true);
	deltaT.set_min(0.0);
	deltaH     = Parameter(2.0, true);
	deltaH.set_min(0.0);
	sld_tail    = Parameter(4e-7);
	sld_head    = Parameter(2e-6);
	sld_solvent   = Parameter(6e-6);
	n_plates     = Parameter(30);
	caille = Parameter(0.001);
	background = Parameter(0.001);

}

/**
 * Function to evaluate 1D scattering function
 * The NIST IGOR library is used for the actual calculation.
 * @param q: q-value
 * @return: function value
 */
double LamellarPSHGModel :: operator()(double q) {
	double dp[10];

	// Fill parameter array for IGOR library
	// Add the background after averaging
	dp[0] = scale();
	dp[1] = spacing();
	dp[2] = deltaT();
	dp[3] = deltaH();
	dp[4] = sld_tail();
	dp[5] = sld_head();
	dp[6] = sld_solvent();
	dp[7] = n_plates();
	dp[8] = caille();
	dp[9] = 0.0;


	// Get the dispersion points for (deltaT) thickness of the tail
	vector<WeightPoint> weights_deltaT;
	deltaT.get_weights(weights_deltaT);

	// Get the dispersion points for (deltaH) thickness of the head
	vector<WeightPoint> weights_deltaH;
	deltaH.get_weights(weights_deltaH);

	// Get the dispersion points for spacing
	vector<WeightPoint> weights_spacing;
	spacing.get_weights(weights_spacing);

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;

	// Loop over deltaT  weight points
	for(int i=0; i< (int)weights_deltaT.size(); i++) {
		dp[2] = weights_deltaT[i].value;

		// Loop over deltaH weight points
		for(int j=0; j< (int)weights_deltaH.size(); j++) {
			dp[3] = weights_deltaH[j].value;
			// Loop over spacing weight points
			for(int k=0; k< (int)weights_spacing.size(); k++) {
				dp[1] = weights_spacing[k].value;

				sum += weights_deltaT[i].weight * weights_deltaH[j].weight *weights_spacing[k].weight
								*LamellarPS_HG(dp, q);
				norm += weights_deltaT[i].weight * weights_deltaH[j].weight * weights_spacing[k].weight;
			}
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
double LamellarPSHGModel :: operator()(double qx, double qy) {
	double q = sqrt(qx*qx + qy*qy);
	return (*this).operator()(q);
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the lamellarPS_HG
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double LamellarPSHGModel :: evaluate_rphi(double q, double phi) {
	return (*this).operator()(q);
}
/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double LamellarPSHGModel :: calculate_ER() {
//NOT implemented yet!!!
	return 0.0;
}
double LamellarPSHGModel :: calculate_VR() {
  return 1.0;
}
