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
#include "models.hh"
#include "parameters.hh"
#include <stdio.h>
using namespace std;

extern "C" {
	#include "libSphere.h"
}

SphereModel :: SphereModel() {
	scale      = Parameter(1.0);
	radius     = Parameter(20.0, true);
	radius.set_min(0.0);
	contrast   = Parameter(3.e-6);
	background = Parameter(0.0);
}

/**
 * Function to evaluate 1D scattering function
 * The NIST IGOR library is used for the actual calculation.
 * @param q: q-value
 * @return: function value
 */
double SphereModel :: operator()(double q) {
	double dp[4];

	// Fill parameter array for IGOR library
	// Add the background after averaging
	dp[0] = scale();
	dp[1] = radius();
	dp[2] = contrast();
	dp[3] = 0.0;

	// Get the dispersion points for the radius
	vector<WeightPoint> weights_rad;
	radius.get_weights(weights_rad);

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;

	// Loop over radius weight points
	for(int i=0; i<weights_rad.size(); i++) {
		dp[1] = weights_rad[i].value;

		sum += weights_rad[i].weight
			* SphereForm(dp, q);
		norm += weights_rad[i].weight;
	}
	return sum/norm + background();
}

/**
 * Function to evaluate 2D scattering function
 * @param q_x: value of Q along x
 * @param q_y: value of Q along y
 * @return: function value
 */
double SphereModel :: operator()(double qx, double qy) {
	double q = sqrt(qx*qx + qy*qy);
	return (*this).operator()(q);
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the sphere
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double SphereModel :: evaluate_rphi(double q, double phi) {
	return (*this).operator()(q);
}
