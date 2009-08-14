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
	#include "parallelepiped.h"
}

ParallelepipedModel :: ParallelepipedModel() {
	scale      = Parameter(1.0);
	short_edgeA     = Parameter(35.0, true);
	short_edgeA.set_max(1.0);
	longer_edgeB     = Parameter(75.0, true);
	longer_edgeB.set_min(1.0);
	longuest_edgeC     = Parameter(400.0, true);
	longuest_edgeC.set_min(1.0);
	contrast   = Parameter(53.e-7);
	background = Parameter(0.0);
	parallel_theta  = Parameter(0.0, true);
	parallel_phi    = Parameter(0.0, true);
	parallel_psi    = Parameter(0.0, true);
}

/**
 * Function to evaluate 1D scattering function
 * The NIST IGOR library is used for the actual calculation.
 * @param q: q-value
 * @return: function value
 */
double ParallelepipedModel :: operator()(double q) {
	double dp[6];

	// Fill parameter array for IGOR library
	// Add the background after averaging
	dp[0] = scale();
	dp[1] = short_edgeA();
	dp[2] = longer_edgeB();
	dp[3] = longuest_edgeC();
	dp[4] = contrast();
	dp[5] = 0.0;

	// Get the dispersion points for the short_edgeA
	vector<WeightPoint> weights_short_edgeA;
	short_edgeA.get_weights(weights_short_edgeA);

	// Get the dispersion points for the longer_edgeB
	vector<WeightPoint> weights_longer_edgeB;
	longer_edgeB.get_weights(weights_longer_edgeB);

	// Get the dispersion points for the longuest_edgeC
	vector<WeightPoint> weights_longuest_edgeC;
	longuest_edgeC.get_weights(weights_longuest_edgeC);



	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;

	// Loop over short_edgeA weight points
	for(int i=0; i< (int)weights_short_edgeA.size(); i++) {
		dp[1] = weights_short_edgeA[i].value;

		// Loop over longer_edgeB weight points
		for(int j=0; j< (int)weights_longer_edgeB.size(); j++) {
			dp[2] = weights_longer_edgeB[i].value;

			// Loop over longuest_edgeC weight points
			for(int k=0; k< (int)weights_longuest_edgeC.size(); k++) {
				dp[3] = weights_longuest_edgeC[j].value;

				sum += weights_short_edgeA[i].weight * weights_longer_edgeB[j].weight
					* weights_longuest_edgeC[k].weight * Parallelepiped(dp, q);

				norm += weights_short_edgeA[i].weight
					 * weights_longer_edgeB[j].weight * weights_longuest_edgeC[k].weight;
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
double ParallelepipedModel :: operator()(double qx, double qy) {
	ParallelepipedParameters dp;
	// Fill parameter array
	dp.scale      = scale();
	dp.short_edgeA   = short_edgeA();
	dp.longer_edgeB   = longer_edgeB();
	dp.longuest_edgeC  = longuest_edgeC();
	dp.contrast   = contrast();
	dp.background = 0.0;
	//dp.background = background();
	dp.parallel_theta  = parallel_theta();
	dp.parallel_phi    = parallel_phi();
	dp.parallel_psi    = parallel_psi();


	// Get the dispersion points for the short_edgeA
	vector<WeightPoint> weights_short_edgeA;
	short_edgeA.get_weights(weights_short_edgeA);

	// Get the dispersion points for the longer_edgeB
	vector<WeightPoint> weights_longer_edgeB;
	longer_edgeB.get_weights(weights_longer_edgeB);

	// Get angular averaging for the longuest_edgeC
	vector<WeightPoint> weights_longuest_edgeC;
	longuest_edgeC.get_weights(weights_longuest_edgeC);

	// Get angular averaging for theta
	vector<WeightPoint> weights_parallel_theta;
	parallel_theta.get_weights(weights_parallel_theta);

	// Get angular averaging for phi
	vector<WeightPoint> weights_parallel_phi;
	parallel_phi.get_weights(weights_parallel_phi);

	// Get angular averaging for psi
	vector<WeightPoint> weights_parallel_psi;
	parallel_psi.get_weights(weights_parallel_psi);

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;

	// Loop over radius weight points
	for(int i=0; i< (int)weights_short_edgeA.size(); i++) {
		dp.short_edgeA = weights_short_edgeA[i].value;

		// Loop over longer_edgeB weight points
		for(int j=0; j< (int)weights_longer_edgeB.size(); j++) {
			dp.longer_edgeB = weights_longer_edgeB[j].value;

			// Average over longuest_edgeC distribution
			for(int k=0; k< (int)weights_longuest_edgeC.size(); k++) {
				dp.longuest_edgeC = weights_longuest_edgeC[k].value;

				// Average over theta distribution
				for(int l=0; l< (int)weights_parallel_theta.size(); l++) {
				dp.parallel_theta = weights_parallel_theta[l].value;

					// Average over phi distribution
					for(int m=0; m< (int)weights_parallel_phi.size(); m++) {
						dp.parallel_phi = weights_parallel_phi[m].value;

						// Average over phi distribution
						for(int n=0; n< (int)weights_parallel_psi.size(); n++) {
							dp.parallel_psi = weights_parallel_psi[n].value;

							double _ptvalue = weights_short_edgeA[i].weight
								* weights_longer_edgeB[j].weight
								* weights_longuest_edgeC[k].weight
								* weights_parallel_theta[l].weight
								* weights_parallel_phi[m].weight
								* weights_parallel_psi[n].weight
								* parallelepiped_analytical_2DXY(&dp, qx, qy);
							if (weights_parallel_theta.size()>1) {
								_ptvalue *= sin(weights_parallel_theta[l].value);
							}
							sum += _ptvalue;

							norm += weights_short_edgeA[i].weight
								* weights_longer_edgeB[j].weight
								* weights_longuest_edgeC[k].weight
								* weights_parallel_theta[l].weight
								* weights_parallel_phi[m].weight
								* weights_parallel_psi[n].weight;
						}
					}

				}
			}
		}
	}
	// Averaging in theta needs an extra normalization
	// factor to account for the sin(theta) term in the
	// integration (see documentation).
	if (weights_parallel_theta.size()>1) norm = norm / asin(1.0);
	return sum/norm + background();
}


/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the cylinder
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double ParallelepipedModel :: evaluate_rphi(double q, double phi) {
	double qx = q*cos(phi);
	double qy = q*sin(phi);
	return (*this).operator()(qx, qy);
}
