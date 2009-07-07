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
	#include "hollow_cylinder.h"
}

HollowCylinderModel :: HollowCylinderModel() {
	scale      = Parameter(1.0);
	core_radius = Parameter(20.0, true);
	core_radius.set_min(0.0);
	shell_radius  = Parameter(30.0, true);
	shell_radius.set_min(0.0);
	length     = Parameter(400.0, true);
	length.set_min(0.0);
	contrast  = Parameter(5.3e-6);
	background = Parameter(0.0);
	axis_theta = Parameter(0.0, true);
	axis_phi   = Parameter(0.0, true);
}

/**
 * Function to evaluate 1D scattering function
 * The NIST IGOR library is used for the actual calculation.
 * @param q: q-value
 * @return: function value
 */
double HollowCylinderModel :: operator()(double q) {
	double dp[6];

	dp[0] = scale();
	dp[1] = core_radius();
	dp[2] = shell_radius();
	dp[3] = length();
	dp[4] = contrast();
	dp[5] = background();

	// Get the dispersion points for the core radius
	vector<WeightPoint> weights_core_radius;
	core_radius.get_weights(weights_core_radius);

	// Get the dispersion points for the shell radius
	vector<WeightPoint> weights_shell_radius;
	shell_radius.get_weights(weights_shell_radius);

	// Get the dispersion points for the length
	vector<WeightPoint> weights_length;
	length.get_weights(weights_length);

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;

	// Loop over core radius weight points
	for(int i=0; i< (int)weights_core_radius.size(); i++) {
		dp[1] = weights_core_radius[i].value;

		// Loop over length weight points
		for(int j=0; j< (int)weights_length.size(); j++) {
			dp[3] = weights_length[j].value;

			// Loop over shell radius weight points
			for(int k=0; k< (int)weights_shell_radius.size(); k++) {
				dp[2] = weights_shell_radius[k].value;

				sum += weights_core_radius[i].weight
					* weights_length[j].weight
					* weights_shell_radius[k].weight
					* HollowCylinder(dp, q);
				norm += weights_core_radius[i].weight
				* weights_length[j].weight
				* weights_shell_radius[k].weight;
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
double HollowCylinderModel :: operator()(double qx, double qy) {
	HollowCylinderParameters dp;
	// Fill parameter array
	dp.scale      = scale();
	dp.core_radius     = core_radius();
	dp.shell_radius  = shell_radius();
	dp.length     = length();
	dp.contrast   = contrast();
	dp.background = background();
	dp.axis_theta = axis_theta();
	dp.axis_phi   = axis_phi();

	// Get the dispersion points for the core radius
	vector<WeightPoint> weights_core_radius;
	core_radius.get_weights(weights_core_radius);

	// Get the dispersion points for the shell radius
	vector<WeightPoint> weights_shell_radius;
	shell_radius.get_weights(weights_shell_radius);

	// Get the dispersion points for the length
	vector<WeightPoint> weights_length;
	length.get_weights(weights_length);

	// Get angular averaging for theta
	vector<WeightPoint> weights_theta;
	axis_theta.get_weights(weights_theta);

	// Get angular averaging for phi
	vector<WeightPoint> weights_phi;
	axis_phi.get_weights(weights_phi);

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;

	// Loop over core radius weight points
	for(int i=0; i<(int)weights_core_radius.size(); i++) {
		dp.core_radius = weights_core_radius[i].value;


		// Loop over length weight points
		for(int j=0; j<(int)weights_length.size(); j++) {
			dp.length = weights_length[j].value;

			// Loop over shell radius weight points
			for(int m=0; m< (int)weights_shell_radius.size(); m++) {
				dp.shell_radius = weights_shell_radius[m].value;

			// Average over theta distribution
			for(int k=0; k< (int)weights_theta.size(); k++) {
				dp.axis_theta = weights_theta[k].value;

				// Average over phi distribution
				for(int l=0; l< (int)weights_phi.size(); l++) {
					dp.axis_phi = weights_phi[l].value;

					double _ptvalue = weights_core_radius[i].weight
						* weights_length[j].weight
						* weights_shell_radius[m].weight
						* weights_theta[k].weight
						* weights_phi[l].weight
						* hollow_cylinder_analytical_2DXY(&dp, qx, qy);
					if (weights_theta.size()>1) {
						_ptvalue *= sin(weights_theta[k].value);
					}
					sum += _ptvalue;

					norm += weights_core_radius[i].weight
						* weights_length[j].weight
						* weights_shell_radius[m].weight
						* weights_theta[k].weight
						* weights_phi[l].weight;

				}
			}
			}
		}
	}
	// Averaging in theta needs an extra normalization
	// factor to account for the sin(theta) term in the
	// integration (see documentation).
	if (weights_theta.size()>1) norm = norm / asin(1.0);
	return sum/norm + background();
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the  cylinder
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double HollowCylinderModel :: evaluate_rphi(double q, double phi) {
	double qx = q*cos(phi);
	double qy = q*sin(phi);
	return (*this).operator()(qx, qy);
}
