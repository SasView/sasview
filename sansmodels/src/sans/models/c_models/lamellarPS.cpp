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
 *	TODO: refactor so that we pull in the old sansmodels.c_extensions
 *	TODO: add 2D function
 */

#include <math.h>
#include "models.hh"
#include "parameters.hh"
#include <stdio.h>
using namespace std;

extern "C" {
	#include "libCylinder.h"
	#include "lamellarPS.h"
}

LamellarPSModel :: LamellarPSModel() {
	scale      = Parameter(1.0);
	spacing    = Parameter(400.0, true);
	spacing.set_min(0.0);
	delta     = Parameter(30.0);
	delta.set_min(0.0);
	contrast   = Parameter(5.3e-6);
	n_plates     = Parameter(20.0);
	caille = Parameter(0.1);
	background = Parameter(0.0);

}

/**
 * Function to evaluate 1D scattering function
 * The NIST IGOR library is used for the actual calculation.
 * @param q: q-value
 * @return: function value
 */
double LamellarPSModel :: operator()(double q) {
	double dp[7];

	// Fill parameter array for IGOR library
	// Add the background after averaging
	dp[0] = scale();
	dp[1] = spacing();
	dp[2] = delta();
	dp[3] = contrast();
	dp[4] = n_plates();
	dp[5] = caille();
	dp[6] = 0.0;


	// Get the dispersion points for spacing and delta (thickness)
	vector<WeightPoint> weights_spacing;
	spacing.get_weights(weights_spacing);
	vector<WeightPoint> weights_delta;
	delta.get_weights(weights_delta);

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;

	// Loop over short_edgeA weight points
	for(int i=0; i< (int)weights_spacing.size(); i++) {
		dp[1] = weights_spacing[i].value;
		for(int j=0; j< (int)weights_spacing.size(); j++) {
			dp[2] = weights_delta[i].value;

			sum += weights_spacing[i].weight * weights_delta[j].weight * LamellarPS_kernel(dp, q);
			norm += weights_spacing[i].weight * weights_delta[j].weight;
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
double LamellarPSModel :: operator()(double qx, double qy) {
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
double LamellarPSModel :: evaluate_rphi(double q, double phi) {
	return (*this).operator()(q);
}
/**
 * Function to calculate effective radius
 * @param pars: parameters of the sphere
 * @return: effective radius value
 */
double LamellarPSModel :: calculate_ER() {
//NOT implemented yet!!!
}

