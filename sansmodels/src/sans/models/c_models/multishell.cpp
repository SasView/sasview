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

MultiShellModel :: MultiShellModel() {
	scale      = Parameter(1.0);
	core_radius     = Parameter(60.0, true);
	core_radius.set_min(0.0);
	s_thickness  = Parameter(10.0);
	w_thickness   = Parameter(10.0);
	core_sld   = Parameter(6.4e-6);
	shell_sld   = Parameter(4.0e-7);
	n_pairs   = Parameter(2);
	background = Parameter(0.0);
}

/**
 * Function to evaluate 1D scattering function
 * The NIST IGOR library is used for the actual calculation.
 * @param q: q-value
 * @return: function value
 */
double MultiShellModel :: operator()(double q) {
	double dp[8];

	// Fill parameter array for IGOR library
	// Add the background after averaging
	dp[0] = scale();
	dp[1] = core_radius();
	dp[2] = s_thickness();
	dp[3] = w_thickness();
	dp[4] = core_sld();
	dp[5] = shell_sld();
	dp[6] = n_pairs();
	dp[7] = background();

	// Get the dispersion points for the core radius
	vector<WeightPoint> weights_core_radius;
	core_radius.get_weights(weights_core_radius);

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;

	// Loop over radius weight points
	for(int i=0; i< (int)weights_core_radius.size(); i++) {
		dp[1] = weights_core_radius[i].value;

		sum += weights_core_radius[i].weight
			* MultiShell(dp, q);
		norm += weights_core_radius[i].weight;
	}
	return sum/norm + background();
}

/**
 * Function to evaluate 2D scattering function
 * @param q_x: value of Q along x
 * @param q_y: value of Q along y
 * @return: function value
 */
double MultiShellModel :: operator()(double qx, double qy) {
	double q = sqrt(qx*qx + qy*qy);
	return (*this).operator()(q);
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the multishell
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double MultiShellModel :: evaluate_rphi(double q, double phi) {
	return (*this).operator()(q);
}
