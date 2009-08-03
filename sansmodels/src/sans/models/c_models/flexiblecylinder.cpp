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
 *	TODO: add 2d
 */

#include <math.h>
#include "models.hh"
#include "parameters.hh"
#include <stdio.h>
using namespace std;

extern "C" {
	#include "libCylinder.h"
	#include "flexible_cylinder.h"
}

FlexibleCylinderModel :: FlexibleCylinderModel() {
	scale      = Parameter(1.0);
	length     = Parameter(1000.0, true);
	length.set_min(0.0);
	kuhn_length = Parameter(100.0, true);
	kuhn_length.set_min(0.0);
	radius  = Parameter(20.0, true);
	radius.set_min(0.0);
	contrast   = Parameter(5.3e-6);
	background = Parameter(0.0001);
}

/**
 * Function to evaluate 1D scattering function
 * The NIST IGOR library is used for the actual calculation.
 * @param q: q-value
 * @return: function value
 */
double FlexibleCylinderModel :: operator()(double q) {
	double dp[6];

	// Fill parameter array for IGOR library
	// Add the background after averaging
	dp[0] = scale();
	dp[1] = length();
	dp[2] = kuhn_length();
	dp[3] = radius();
	dp[4] = contrast();
	dp[5] = background();

	// Get the dispersion points for the length
	vector<WeightPoint> weights_len;
	length.get_weights(weights_len);

	// Get the dispersion points for the kuhn_length
	vector<WeightPoint> weights_kuhn;
	kuhn_length.get_weights(weights_kuhn);

	// Get the dispersion points for the radius
	vector<WeightPoint> weights_rad;
	radius.get_weights(weights_rad);

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;

	// Loop over semi axis A weight points
	for(int i=0; i< (int)weights_len.size(); i++) {
		dp[1] = weights_len[i].value;

		// Loop over semi axis B weight points
		for(int j=0; j< (int)weights_kuhn.size(); j++) {
			dp[2] = weights_kuhn[j].value;

			// Loop over semi axis C weight points
			for(int k=0; k< (int)weights_rad.size(); k++) {
				dp[3] = weights_rad[k].value;

				sum += weights_len[i].weight
					* weights_kuhn[j].weight*weights_rad[k].weight * FlexExclVolCyl(dp, q);
				norm += weights_len[i].weight
					* weights_kuhn[j].weight*weights_rad[k].weight;
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
double FlexibleCylinderModel :: operator()(double qx, double qy) {
	double q = sqrt(qx*qx + qy*qy);
	return (*this).operator()(q);
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the triaxial ellipsoid
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double FlexibleCylinderModel :: evaluate_rphi(double q, double phi) {
	//double qx = q*cos(phi);
	//double qy = q*sin(phi);
	return (*this).operator()(q);
}
