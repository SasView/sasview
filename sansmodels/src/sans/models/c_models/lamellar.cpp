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
 */

#include <math.h>
#include "models.hh"
#include "parameters.hh"
#include <stdio.h>
using namespace std;

extern "C" {
	#include "libCylinder.h"
	#include "lamellar.h"
}

LamellarModel :: LamellarModel() {
	scale      = Parameter(1.0);
	delta     = Parameter(50.0, true);
	delta.set_min(0.0);
	sigma    = Parameter(0.15, true);
	contrast   = Parameter(5.3e-6);
	background = Parameter(0.0);

}

/**
 * Function to evaluate 1D scattering function
 * The NIST IGOR library is used for the actual calculation.
 * @param q: q-value
 * @return: function value
 */
double LamellarModel :: operator()(double q) {
	double dp[5];

	// Fill parameter array for IGOR library
	// Add the background after averaging
	dp[0] = scale();
	dp[1] = delta();
	dp[2] = sigma();
	dp[3] = contrast();
	dp[4] = background();


	// Get the dispersion points for the bilayer thickness(delta)
	vector<WeightPoint> weights_delta;
	delta.get_weights(weights_delta);

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;

	// Loop over semi axis A weight points
	for(int i=0; i< (int)weights_delta.size(); i++) {
		dp[1] = weights_delta[i].value;
		sum += weights_delta[i].weight* LamellarFF(dp, q);
		norm += weights_delta[i].weight;
				
	}
	return sum/norm + background();
}

/**
 * Function to evaluate 2D scattering function
 * @param q_x: value of Q along x
 * @param q_y: value of Q along y
 * @return: function value
 */

double LamellarModel :: operator()(double qx, double qy) {
	LamellarParameters dp;

	// Fill parameter array for IGOR library
	// Add the background after averaging
	dp.scale = scale();
	dp.delta = delta();
	dp.sigma = sigma();
	dp.contrast = contrast();
	dp.background = background();


	// Get the dispersion points for the bilayer thickness(delta)
	vector<WeightPoint> weights_delta;
	delta.get_weights(weights_delta);

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;

	// Loop over detla  weight points
	for(int i=0; i< (int)weights_delta.size(); i++) {
		dp.delta = weights_delta[i].value;
		sum += weights_delta[i].weight* lamellar_analytical_2DXY(&dp, qx, qy);
		norm += weights_delta[i].weight;
				
	}
	return sum/norm + background();
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the lamellar
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double LamellarModel :: evaluate_rphi(double q, double phi) {
	double qx = q*cos(phi);
	double qy = q*sin(phi);
	return (*this).operator()(qx, qy);
}
