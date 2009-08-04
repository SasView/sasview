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
	#include "stacked_disks.h"
}

StackedDisksModel :: StackedDisksModel() {
	scale      = Parameter(1.0);
	radius     = Parameter(3000.0, true);
	radius.set_min(0.0);
	length     = Parameter(10.0, true);
	length.set_min(0.0);
	thickness     = Parameter(15.0);
	thickness.set_min(0.0);
	core_sld = Parameter(4.0e-6);
	layer_sld  = Parameter(-4.0e-7);
	solvent_sld  = Parameter(5.0e-6);
	nlayers   = Parameter(1);
	spacing   = Parameter(0);
	background = Parameter(0.001);
	axis_theta  = Parameter(0.0, true);
	axis_phi    = Parameter(0.0, true);
}

/**
 * Function to evaluate 1D scattering function
 * The NIST IGOR library is used for the actual calculation.
 * @param q: q-value
 * @return: function value
 */
double StackedDisksModel :: operator()(double q) {
	double dp[10];

	// Fill parameter array for IGOR library
	// Add the background after averaging
	dp[0] = scale();
	dp[1] = radius();
	dp[2] = length();
	dp[3] = thickness();
	dp[4] = core_sld();
	dp[5] = layer_sld();
	dp[6] = solvent_sld();
	dp[7] = nlayers();
	dp[8] = spacing();
	dp[9] = 0.0;

	// Get the dispersion points for the length
	vector<WeightPoint> weights_length;
	length.get_weights(weights_length);

	// Get the dispersion points for the radius
	vector<WeightPoint> weights_radius;
	radius.get_weights(weights_radius);

	// Get the dispersion points for the thickness
	vector<WeightPoint> weights_thickness;
	thickness.get_weights(weights_thickness);

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;

	// Loop over length weight points
	for(int i=0; i< (int)weights_length.size(); i++) {
		dp[1] = weights_length[i].value;

		// Loop over radius weight points
		for(int j=0; j< (int)weights_radius.size(); j++) {
			dp[2] = weights_radius[j].value;

			// Loop over thickness weight points
			for(int k=0; k< (int)weights_radius.size(); k++) {
				dp[3] = weights_radius[k].value;

				sum += weights_length[i].weight
					* weights_radius[j].weight * weights_thickness[k].weight* StackedDiscs(dp, q);
				norm += weights_length[i].weight
					* weights_radius[j].weight* weights_thickness[k].weight;
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
double StackedDisksModel :: operator()(double qx, double qy) {
	StackedDisksParameters dp;
	// Fill parameter array
	dp.scale      = scale();
	dp.length     = length();
	dp.radius	  = radius();
	dp.thickness  = thickness();
	dp.core_sld   = core_sld();
	dp.layer_sld  = layer_sld();
	dp.solvent_sld= solvent_sld();
	dp.nlayers	  = nlayers();
	dp.spacing    = spacing();
	dp.background = 0.0;
	dp.axis_theta = axis_theta();
	dp.axis_phi   = axis_phi();

	// Get the dispersion points for the length
	vector<WeightPoint> weights_length;
	length.get_weights(weights_length);

	// Get the dispersion points for the radius
	vector<WeightPoint> weights_radius;
	radius.get_weights(weights_radius);

	// Get the dispersion points for the thickness
	vector<WeightPoint> weights_thickness;
	thickness.get_weights(weights_thickness);

	// Get angular averaging for theta
	vector<WeightPoint> weights_theta;
	axis_theta.get_weights(weights_theta);

	// Get angular averaging for phi
	vector<WeightPoint> weights_phi;
	axis_phi.get_weights(weights_phi);

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;

	// Loop over length weight points
	for(int i=0; i< (int)weights_length.size(); i++) {
		dp.length = weights_length[i].value;

		// Loop over radius weight points
		for(int j=0; j< (int)weights_radius.size(); j++) {
			dp.radius = weights_radius[j].value;

				// Loop over thickness weight points
				for(int k=0; k< (int)weights_thickness.size(); k++) {
				dp.thickness = weights_thickness[k].value;

					for(int l=0; l< (int)weights_theta.size(); l++) {
					dp.axis_theta = weights_theta[l].value;

						// Average over phi distribution
						for(int m=0; m <(int)weights_phi.size(); m++) {
							dp.axis_phi = weights_phi[m].value;

							double _ptvalue = weights_length[i].weight
								* weights_radius[j].weight
								* weights_thickness[k].weight
								* weights_theta[l].weight
								* weights_phi[m].weight
								* stacked_disks_analytical_2DXY(&dp, qx, qy);
							if (weights_theta.size()>1) {
								_ptvalue *= sin(weights_theta[l].value);
							}
							sum += _ptvalue;

							norm += weights_length[i].weight
								* weights_radius[j].weight
								* weights_thickness[k].weight
								* weights_theta[l].weight
								* weights_phi[m].weight;
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
 * @param pars: parameters of the triaxial ellipsoid
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double StackedDisksModel :: evaluate_rphi(double q, double phi) {
	double qx = q*cos(phi);
	double qy = q*sin(phi);
	return (*this).operator()(qx, qy);
}
