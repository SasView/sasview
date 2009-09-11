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
	#include "libStructureFactor.h"
	#include "parallelepiped.h"
}

ParallelepipedModel :: ParallelepipedModel() {
	scale      = Parameter(1.0);
	short_a     = Parameter(35.0, true);
	short_a.set_min(1.0);
	short_b     = Parameter(75.0, true);
	short_b.set_min(1.0);
	long_c     = Parameter(400.0, true);
	long_c.set_min(1.0);
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
	dp[1] = short_a();
	dp[2] = short_b();
	dp[3] = long_c();
	dp[4] = contrast();
	dp[5] = 0.0;

	// Get the dispersion points for the short_edgeA
	vector<WeightPoint> weights_short_a;
	short_a.get_weights(weights_short_a);

	// Get the dispersion points for the longer_edgeB
	vector<WeightPoint> weights_short_b;
	short_b.get_weights(weights_short_b);

	// Get the dispersion points for the longuest_edgeC
	vector<WeightPoint> weights_long_c;
	long_c.get_weights(weights_long_c);



	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;

	// Loop over short_edgeA weight points
	for(int i=0; i< (int)weights_short_a.size(); i++) {
		dp[1] = weights_short_a[i].value;

		// Loop over longer_edgeB weight points
		for(int j=0; j< (int)weights_short_b.size(); j++) {
			dp[2] = weights_short_b[j].value;

			// Loop over longuest_edgeC weight points
			for(int k=0; k< (int)weights_long_c.size(); k++) {
				dp[3] = weights_long_c[k].value;
				sum += weights_short_a[i].weight * weights_short_b[j].weight
					* weights_long_c[k].weight * Parallelepiped(dp, q);

				norm += weights_short_a[i].weight
					 * weights_short_b[j].weight * weights_long_c[k].weight;
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
	dp.short_a   = short_a();
	dp.short_b   = short_b();
	dp.long_c  = long_c();
	dp.contrast   = contrast();
	dp.background = 0.0;
	//dp.background = background();
	dp.parallel_theta  = parallel_theta();
	dp.parallel_phi    = parallel_phi();
	dp.parallel_psi    = parallel_psi();


	// Get the dispersion points for the short_edgeA
	vector<WeightPoint> weights_short_a;
	short_a.get_weights(weights_short_a);

	// Get the dispersion points for the longer_edgeB
	vector<WeightPoint> weights_short_b;
	short_b.get_weights(weights_short_b);

	// Get angular averaging for the longuest_edgeC
	vector<WeightPoint> weights_long_c;
	long_c.get_weights(weights_long_c);

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
	for(int i=0; i< (int)weights_short_a.size(); i++) {
		dp.short_a = weights_short_a[i].value;

		// Loop over longer_edgeB weight points
		for(int j=0; j< (int)weights_short_b.size(); j++) {
			dp.short_b = weights_short_b[j].value;

			// Average over longuest_edgeC distribution
			for(int k=0; k< (int)weights_long_c.size(); k++) {
				dp.long_c = weights_long_c[k].value;

				// Average over theta distribution
				for(int l=0; l< (int)weights_parallel_theta.size(); l++) {
				dp.parallel_theta = weights_parallel_theta[l].value;

					// Average over phi distribution
					for(int m=0; m< (int)weights_parallel_phi.size(); m++) {
						dp.parallel_phi = weights_parallel_phi[m].value;

						// Average over phi distribution
						for(int n=0; n< (int)weights_parallel_psi.size(); n++) {
							dp.parallel_psi = weights_parallel_psi[n].value;

							double _ptvalue = weights_short_a[i].weight
								* weights_short_b[j].weight
								* weights_long_c[k].weight
								* weights_parallel_theta[l].weight
								* weights_parallel_phi[m].weight
								* weights_parallel_psi[n].weight
								* parallelepiped_analytical_2DXY(&dp, qx, qy);
							if (weights_parallel_theta.size()>1) {
								_ptvalue *= sin(weights_parallel_theta[l].value);
							}
							sum += _ptvalue;

							norm += weights_short_a[i].weight
								* weights_short_b[j].weight
								* weights_long_c[k].weight
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
/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double ParallelepipedModel :: calculate_ER() {
	ParallelepipedParameters dp;
	dp.short_a   = short_a();
	dp.short_b   = short_b();
	dp.long_c  = long_c();
	double rad_out = 0.0;
	double pi = 4.0*atan(1.0);
	double suf_rad = sqrt(dp.short_a*dp.short_b/pi);

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;

	// Get the dispersion points for the short_edgeA
	vector<WeightPoint> weights_short_a;
	short_a.get_weights(weights_short_a);

	// Get the dispersion points for the longer_edgeB
	vector<WeightPoint> weights_short_b;
	short_b.get_weights(weights_short_b);

	// Get angular averaging for the longuest_edgeC
	vector<WeightPoint> weights_long_c;
	long_c.get_weights(weights_long_c);

	// Loop over radius weight points
	for(int i=0; i< (int)weights_short_a.size(); i++) {
		dp.short_a = weights_short_a[i].value;

		// Loop over longer_edgeB weight points
		for(int j=0; j< (int)weights_short_b.size(); j++) {
			dp.short_b = weights_short_b[j].value;

			// Average over longuest_edgeC distribution
			for(int k=0; k< (int)weights_long_c.size(); k++) {
				dp.long_c = weights_long_c[k].value;
				//Calculate surface averaged radius
				//This is rough approximation.
				suf_rad = sqrt(dp.short_a*dp.short_b/pi);

				//Note: output of "DiamCyl(dp.length,dp.radius)" is DIAMETER.
				sum +=weights_short_a[i].weight* weights_short_b[j].weight
					* weights_long_c[k].weight*DiamCyl(dp.long_c, suf_rad)/2.0;
				norm += weights_short_a[i].weight* weights_short_b[j].weight*weights_long_c[k].weight;
			}
		}
	}

	if (norm != 0){
		//return the averaged value
		rad_out =  sum/norm;}
	else{
		//return normal value
		//Note: output of "DiamCyl(length,radius)" is DIAMETER.
		rad_out = DiamCyl(dp.long_c, suf_rad)/2.0;}
	return rad_out;

}
