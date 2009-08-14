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
	#include "spheroid.h"
}

CoreShellSpheroidModel :: CoreShellSpheroidModel() {
	scale      = Parameter(1.0);
	equat_core     = Parameter(200.0, true);
	equat_core.set_min(0.0);
	polar_core     = Parameter(20.0, true);
	polar_core.set_min(0.0);
	equat_shell   = Parameter(250.0, true);
	equat_shell.set_min(0.0);
	polar_shell    = Parameter(30.0, true);
	polar_shell.set_min(0.0);
	contrast   = Parameter(1e-6);
	sld_solvent = Parameter(6.3e-6);
	background = Parameter(0.0);
	axis_theta  = Parameter(0.0, true);
	axis_phi    = Parameter(0.0, true);

}

/**
 * Function to evaluate 1D scattering function
 * The NIST IGOR library is used for the actual calculation.
 * @param q: q-value
 * @return: function value
 */
double CoreShellSpheroidModel :: operator()(double q) {
	double dp[8];

	// Fill parameter array for IGOR library
	// Add the background after averaging
	dp[0] = scale();
	dp[1] = equat_core();
	dp[2] = polar_core();
	dp[3] = equat_shell();
	dp[4] = polar_shell();
	dp[5] = contrast();
	dp[6] = sld_solvent();
	dp[7] = 0.0;

	// Get the dispersion points for the major core
	vector<WeightPoint> weights_equat_core;
	equat_core.get_weights(weights_equat_core);

	// Get the dispersion points for the minor core
	vector<WeightPoint> weights_polar_core;
	polar_core.get_weights(weights_polar_core);

	// Get the dispersion points for the major shell
	vector<WeightPoint> weights_equat_shell;
	equat_shell.get_weights(weights_equat_shell);

	// Get the dispersion points for the minor_shell
	vector<WeightPoint> weights_polar_shell;
	polar_shell.get_weights(weights_polar_shell);


	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;

	// Loop over major core weight points
	for(int i=0; i<(int)weights_equat_core.size(); i++) {
		dp[1] = weights_equat_core[i].value;

		// Loop over minor core weight points
		for(int j=0; j<(int)weights_polar_core.size(); j++) {
			dp[2] = weights_polar_core[j].value;

			// Loop over major shell weight points
			for(int k=0; k<(int)weights_equat_shell.size(); k++) {
				dp[3] = weights_equat_shell[k].value;

				// Loop over minor shell weight points
				for(int l=0; l<(int)weights_polar_shell.size(); l++) {
					dp[4] = weights_polar_shell[l].value;

					sum += weights_equat_core[i].weight* weights_polar_core[j].weight * weights_equat_shell[k].weight
						* weights_polar_shell[l].weight * OblateForm(dp, q);
					norm += weights_equat_core[i].weight* weights_polar_core[j].weight * weights_equat_shell[k].weight
							* weights_polar_shell[l].weight;
				}
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
/*
double OblateModel :: operator()(double qx, double qy) {
	double q = sqrt(qx*qx + qy*qy);

	return (*this).operator()(q);
}
*/

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the oblate
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double CoreShellSpheroidModel :: evaluate_rphi(double q, double phi) {
	return (*this).operator()(q);
}


double CoreShellSpheroidModel :: operator()(double qx, double qy) {
	SpheroidParameters dp;
	// Fill parameter array
	dp.scale      = scale();
	dp.equat_core = equat_core();
	dp.polar_core = polar_core();
	dp.equat_shell = equat_shell();
	dp.polar_shell = polar_shell();
	dp.contrast = contrast();
	dp.sld_solvent = sld_solvent();
	dp.background = background();
	dp.axis_theta = axis_theta();
	dp.axis_phi = axis_phi();

	// Get the dispersion points for the major core
	vector<WeightPoint> weights_equat_core;
	equat_core.get_weights(weights_equat_core);

	// Get the dispersion points for the minor core
	vector<WeightPoint> weights_polar_core;
	polar_core.get_weights(weights_polar_core);

	// Get the dispersion points for the major shell
	vector<WeightPoint> weights_equat_shell;
	equat_shell.get_weights(weights_equat_shell);

	// Get the dispersion points for the minor shell
	vector<WeightPoint> weights_polar_shell;
	polar_shell.get_weights(weights_polar_shell);


	// Get angular averaging for theta
	vector<WeightPoint> weights_theta;
	axis_theta.get_weights(weights_theta);

	// Get angular averaging for phi
	vector<WeightPoint> weights_phi;
	axis_phi.get_weights(weights_phi);

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;

	// Loop over major core weight points
	for(int i=0; i< (int)weights_equat_core.size(); i++) {
		dp.equat_core = weights_equat_core[i].value;

		// Loop over minor core weight points
		for(int j=0; j< (int)weights_polar_core.size(); j++) {
			dp.polar_core = weights_polar_core[j].value;

			// Loop over major shell weight points
			for(int k=0; k< (int)weights_equat_shell.size(); k++) {
				dp.equat_shell = weights_equat_shell[i].value;

				// Loop over minor shell weight points
				for(int l=0; l< (int)weights_polar_shell.size(); l++) {
					dp.polar_shell = weights_polar_shell[l].value;

					// Average over theta distribution
					for(int m=0; m< (int)weights_theta.size(); m++) {
						dp.axis_theta = weights_theta[m].value;

						// Average over phi distribution
						for(int n=0; n< (int)weights_phi.size(); n++) {
							dp.axis_phi = weights_phi[n].value;

							double _ptvalue = weights_equat_core[i].weight *weights_polar_core[j].weight
								* weights_equat_shell[k].weight * weights_polar_shell[l].weight
								* weights_theta[m].weight
								* weights_phi[n].weight
								* spheroid_analytical_2DXY(&dp, qx, qy);
							if (weights_theta.size()>1) {
								_ptvalue *= sin(weights_theta[m].value);
							}
							sum += _ptvalue;

							norm += weights_equat_core[i].weight *weights_polar_core[j].weight
								* weights_equat_shell[k].weight * weights_polar_shell[l].weight
								* weights_theta[m].weight * weights_phi[n].weight;
						}
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

