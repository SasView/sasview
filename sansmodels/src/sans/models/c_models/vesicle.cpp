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

VesicleModel :: VesicleModel() {
	scale      = Parameter(1.0);
	core_radius     = Parameter(100.0, true);
	core_radius.set_min(0.0);
	thickness  = Parameter(30.0, true);
	thickness.set_min(0.0);
	core_sld   = Parameter(6.36e-6);
	shell_sld   = Parameter(5.0e-7);
	background = Parameter(0.0);
}

/**
 * Function to evaluate 1D scattering function
 * The NIST IGOR library is used for the actual calculation.
 * @param q: q-value
 * @return: function value
 */
double VesicleModel :: operator()(double q) {
	double dp[6];

	// Fill parameter array for IGOR library
	// Add the background after averaging
	dp[0] = scale();
	dp[1] = core_radius();
	dp[2] = thickness();
	dp[3] = core_sld();
	dp[4] = shell_sld();
	dp[5] = background();


	// Get the dispersion points for the core radius
	vector<WeightPoint> weights_core_radius;
	core_radius.get_weights(weights_core_radius);
	// Get the dispersion points for the thickness
	vector<WeightPoint> weights_thickness;
	thickness.get_weights(weights_thickness);

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;

	// Loop over radius weight points
	for(int i=0; i< (int)weights_core_radius.size(); i++) {
		dp[1] = weights_core_radius[i].value;
		for(int j=0; j< (int)weights_core_radius.size(); j++) {
			dp[2] = weights_thickness[j].value;
			sum += weights_core_radius[i].weight
				* weights_thickness[j].weight * VesicleForm(dp, q);
			norm += weights_core_radius[i].weight * weights_thickness[j].weight;
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
double VesicleModel :: operator()(double qx, double qy) {
	double q = sqrt(qx*qx + qy*qy);
	return (*this).operator()(q);
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the vesicle
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double VesicleModel :: evaluate_rphi(double q, double phi) {
	return (*this).operator()(q);
}
