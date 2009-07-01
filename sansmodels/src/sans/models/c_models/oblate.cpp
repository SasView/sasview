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
	#include "oblate.h"
}

OblateModel :: OblateModel() {
	scale      = Parameter(1.0);
	major_core     = Parameter(200.0, true);
	major_core.set_min(0.0);
	minor_core     = Parameter(20.0, true);
	minor_core.set_min(0.0);
	major_shell   = Parameter(250.0, true);
	major_shell.set_min(0.0);
	minor_shell    = Parameter(30.0, true);
	minor_shell.set_min(0.0);
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
double OblateModel :: operator()(double q) {
	double dp[8];

	// Fill parameter array for IGOR library
	// Add the background after averaging
	dp[0] = scale();
	dp[1] = major_core();
	dp[2] = minor_core();
	dp[3] = major_shell();
	dp[4] = minor_shell();
	dp[5] = contrast();
	dp[6] = sld_solvent();
	dp[7] = background();
	
	// Get the dispersion points for the major core
	vector<WeightPoint> weights_major_core;
	major_core.get_weights(weights_major_core);

	// Get the dispersion points for the minor core
	vector<WeightPoint> weights_minor_core;
	minor_core.get_weights(weights_minor_core);

	// Get the dispersion points for the major shell
	vector<WeightPoint> weights_major_shell;
	major_shell.get_weights(weights_major_shell);

	// Get the dispersion points for the minor_shell
	vector<WeightPoint> weights_minor_shell;
	minor_shell.get_weights(weights_minor_shell);


	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;

	// Loop over major core weight points
	for(int i=0; i<(int)weights_major_core.size(); i++) {
		dp[1] = weights_major_core[i].value;

		// Loop over minor core weight points
		for(int j=0; j<(int)weights_minor_core.size(); j++) {
			dp[2] = weights_minor_core[j].value;

			// Loop over major shell weight points
			for(int k=0; k<(int)weights_major_shell.size(); k++) {
				dp[3] = weights_major_shell[k].value;

				// Loop over minor shell weight points
				for(int l=0; l<(int)weights_minor_shell.size(); l++) {
					dp[4] = weights_minor_shell[l].value;

					sum += weights_major_core[i].weight* weights_minor_core[j].weight * weights_major_shell[k].weight 
						* weights_minor_shell[l].weight * OblateForm(dp, q);
					norm += weights_major_core[i].weight* weights_minor_core[j].weight * weights_major_shell[k].weight 
							* weights_minor_shell[l].weight;
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
double OblateModel :: operator()(double qx, double qy) {
	OblateParameters dp;
	// Fill parameter array
	dp.scale      = scale();
	dp.major_core = major_core();
	dp.minor_core = minor_core();
	dp.major_shell = major_shell();
	dp.minor_shell = minor_shell();
	dp.contrast = contrast();
	dp.sld_solvent = sld_solvent();
	dp.background = background();
	dp.axis_theta = axis_theta();
	dp.axis_phi = axis_phi();

	// Get the dispersion points for the major core
	vector<WeightPoint> weights_major_core;
	major_core.get_weights(weights_major_core);

	// Get the dispersion points for the minor core
	vector<WeightPoint> weights_minor_core;
	minor_core.get_weights(weights_minor_core);

	// Get the dispersion points for the major shell
	vector<WeightPoint> weights_major_shell;
	major_shell.get_weights(weights_major_shell);

	// Get the dispersion points for the minor shell
	vector<WeightPoint> weights_minor_shell;
	minor_shell.get_weights(weights_minor_shell);


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
	for(int i=0; i< (int)weights_major_core.size(); i++) {
		dp.major_core = weights_major_core[i].value;

		// Loop over minor core weight points
		for(int j=0; j< (int)weights_minor_core.size(); j++) {
			dp.minor_core = weights_minor_core[j].value;

			// Loop over major shell weight points
			for(int k=0; k< (int)weights_major_shell.size(); k++) {
				dp.major_shell = weights_major_shell[i].value;

				// Loop over minor shell weight points
				for(int l=0; l< (int)weights_minor_shell.size(); l++) {
					dp.minor_shell = weights_minor_shell[l].value;

					// Average over theta distribution
					for(int m=0; m< (int)weights_theta.size(); m++) {
						dp.axis_theta = weights_theta[m].value;

						// Average over phi distribution
						for(int n=0; n< (int)weights_phi.size(); n++) {
							dp.axis_phi = weights_phi[n].value;

							double _ptvalue = weights_major_core[i].weight *weights_minor_core[j].weight
								* weights_major_shell[k].weight * weights_minor_shell[l].weight
								* weights_theta[m].weight
								* weights_phi[n].weight
								* oblate_analytical_2DXY(&dp, qx, qy);
							if (weights_theta.size()>1) {
								_ptvalue *= sin(weights_theta[k].value);
							}
							sum += _ptvalue;

							norm += weights_major_core[i].weight *weights_minor_core[j].weight
								* weights_major_shell[k].weight * weights_minor_shell[l].weight
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

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the oblate
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double OblateModel :: evaluate_rphi(double q, double phi) {
	double qx = q*cos(phi);
	double qy = q*sin(phi);
	return (*this).operator()(qx, qy);
}
