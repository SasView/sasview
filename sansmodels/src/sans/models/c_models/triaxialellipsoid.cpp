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
	#include "libStructureFactor.h"
	#include "triaxial_ellipsoid.h"
}

TriaxialEllipsoidModel :: TriaxialEllipsoidModel() {
	scale      = Parameter(1.0);
	semi_axisA     = Parameter(35.0, true);
	semi_axisA.set_min(0.0);
	semi_axisB     = Parameter(100.0, true);
	semi_axisB.set_min(0.0);
	semi_axisC  = Parameter(400.0, true);
	semi_axisC.set_min(0.0);
	contrast   = Parameter(5.3e-6);
	background = Parameter(0.0);
	axis_theta  = Parameter(1.0, true);
	axis_phi    = Parameter(1.0, true);
	axis_psi    = Parameter(0.0, true);
}

/**
 * Function to evaluate 1D scattering function
 * The NIST IGOR library is used for the actual calculation.
 * @param q: q-value
 * @return: function value
 */
double TriaxialEllipsoidModel :: operator()(double q) {
	double dp[6];

	// Fill parameter array for IGOR library
	// Add the background after averaging
	dp[0] = scale();
	dp[1] = semi_axisA();
	dp[2] = semi_axisB();
	dp[3] = semi_axisC();
	dp[4] = contrast();
	dp[5] = 0.0;

	// Get the dispersion points for the semi axis A
	vector<WeightPoint> weights_semi_axisA;
	semi_axisA.get_weights(weights_semi_axisA);

	// Get the dispersion points for the semi axis B
	vector<WeightPoint> weights_semi_axisB;
	semi_axisB.get_weights(weights_semi_axisB);

	// Get the dispersion points for the semi axis C
	vector<WeightPoint> weights_semi_axisC;
	semi_axisC.get_weights(weights_semi_axisC);

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;
	double vol = 0.0;

	// Loop over semi axis A weight points
	for(int i=0; i< (int)weights_semi_axisA.size(); i++) {
		dp[1] = weights_semi_axisA[i].value;

		// Loop over semi axis B weight points
		for(int j=0; j< (int)weights_semi_axisB.size(); j++) {
			dp[2] = weights_semi_axisB[j].value;

			// Loop over semi axis C weight points
			for(int k=0; k< (int)weights_semi_axisC.size(); k++) {
				dp[3] = weights_semi_axisC[k].value;
				//Un-normalize  by volume
				sum += weights_semi_axisA[i].weight
					* weights_semi_axisB[j].weight * weights_semi_axisC[k].weight* TriaxialEllipsoid(dp, q)
					* weights_semi_axisA[i].value*weights_semi_axisB[j].value*weights_semi_axisC[k].value;
				//Find average volume
				vol += weights_semi_axisA[i].weight
					* weights_semi_axisB[j].weight * weights_semi_axisC[k].weight
					* weights_semi_axisA[i].value*weights_semi_axisB[j].value*weights_semi_axisC[k].value;

				norm += weights_semi_axisA[i].weight
					* weights_semi_axisB[j].weight * weights_semi_axisC[k].weight;
			}
		}
	}
	if (vol != 0.0 && norm != 0.0) {
		//Re-normalize by avg volume
		sum = sum/(vol/norm);}

	return sum/norm + background();
}

/**
 * Function to evaluate 2D scattering function
 * @param q_x: value of Q along x
 * @param q_y: value of Q along y
 * @return: function value
 */
double TriaxialEllipsoidModel :: operator()(double qx, double qy) {
	TriaxialEllipsoidParameters dp;
	// Fill parameter array
	dp.scale      = scale();
	dp.semi_axisA   = semi_axisA();
	dp.semi_axisB     = semi_axisB();
	dp.semi_axisC     = semi_axisC();
	dp.contrast   = contrast();
	dp.background = 0.0;
	dp.axis_theta  = axis_theta();
	dp.axis_phi    = axis_phi();
	dp.axis_psi    = axis_psi();

	// Get the dispersion points for the semi_axis A
	vector<WeightPoint> weights_semi_axisA;
	semi_axisA.get_weights(weights_semi_axisA);

	// Get the dispersion points for the semi_axis B
	vector<WeightPoint> weights_semi_axisB;
	semi_axisB.get_weights(weights_semi_axisB);

	// Get the dispersion points for the semi_axis C
	vector<WeightPoint> weights_semi_axisC;
	semi_axisC.get_weights(weights_semi_axisC);

	// Get angular averaging for theta
	vector<WeightPoint> weights_theta;
	axis_theta.get_weights(weights_theta);

	// Get angular averaging for phi
	vector<WeightPoint> weights_phi;
	axis_phi.get_weights(weights_phi);

	// Get angular averaging for psi
	vector<WeightPoint> weights_psi;
	axis_psi.get_weights(weights_psi);

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;
	double norm_vol = 0.0;
	double vol = 0.0;

	// Loop over semi axis A weight points
	for(int i=0; i< (int)weights_semi_axisA.size(); i++) {
		dp.semi_axisA = weights_semi_axisA[i].value;

		// Loop over semi axis B weight points
		for(int j=0; j< (int)weights_semi_axisB.size(); j++) {
			dp.semi_axisB = weights_semi_axisB[j].value;

			// Loop over semi axis C weight points
			for(int k=0; k < (int)weights_semi_axisC.size(); k++) {
			dp.semi_axisC = weights_semi_axisC[k].value;

				// Average over theta distribution
				for(int l=0; l< (int)weights_theta.size(); l++) {
					dp.axis_theta = weights_theta[l].value;

					// Average over phi distribution
					for(int m=0; m <(int)weights_phi.size(); m++) {
						dp.axis_phi = weights_phi[m].value;
						// Average over psi distribution
						for(int n=0; n <(int)weights_psi.size(); n++) {
							dp.axis_psi = weights_psi[n].value;
							//Un-normalize  by volume
							double _ptvalue = weights_semi_axisA[i].weight
								* weights_semi_axisB[j].weight
								* weights_semi_axisC[k].weight
								* weights_theta[l].weight
								* weights_phi[m].weight
								* weights_psi[n].weight
								* triaxial_ellipsoid_analytical_2DXY(&dp, qx, qy)
								* weights_semi_axisA[i].value*weights_semi_axisB[j].value*weights_semi_axisC[k].value;
							if (weights_theta.size()>1) {
								_ptvalue *= sin(weights_theta[k].value);
							}
							sum += _ptvalue;
							//Find average volume
							vol += weights_semi_axisA[i].weight
								* weights_semi_axisB[j].weight
								* weights_semi_axisC[k].weight
								* weights_semi_axisA[i].value*weights_semi_axisB[j].value*weights_semi_axisC[k].value;
							//Find norm for volume
							norm_vol += weights_semi_axisA[i].weight
								* weights_semi_axisB[j].weight
								* weights_semi_axisC[k].weight;

							norm += weights_semi_axisA[i].weight
								* weights_semi_axisB[j].weight
								* weights_semi_axisC[k].weight
								* weights_theta[l].weight
								* weights_phi[m].weight
								* weights_psi[n].weight;
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

	if (vol != 0.0 && norm_vol != 0.0) {
		//Re-normalize by avg volume
		sum = sum/(vol/norm_vol);}

	return sum/norm + background();
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the triaxial ellipsoid
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double TriaxialEllipsoidModel :: evaluate_rphi(double q, double phi) {
	double qx = q*cos(phi);
	double qy = q*sin(phi);
	return (*this).operator()(qx, qy);
}
/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double TriaxialEllipsoidModel :: calculate_ER() {
	TriaxialEllipsoidParameters dp;

	dp.semi_axisA   = semi_axisA();
	dp.semi_axisB     = semi_axisB();
	//polar axis C
	dp.semi_axisC     = semi_axisC();

	double rad_out = 0.0;
	//Surface average radius at the equat. cross section.
	double suf_rad = sqrt(dp.semi_axisA * dp.semi_axisB);

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;

	// Get the dispersion points for the semi_axis A
	vector<WeightPoint> weights_semi_axisA;
	semi_axisA.get_weights(weights_semi_axisA);

	// Get the dispersion points for the semi_axis B
	vector<WeightPoint> weights_semi_axisB;
	semi_axisB.get_weights(weights_semi_axisB);

	// Get the dispersion points for the semi_axis C
	vector<WeightPoint> weights_semi_axisC;
	semi_axisC.get_weights(weights_semi_axisC);

	// Loop over semi axis A weight points
	for(int i=0; i< (int)weights_semi_axisA.size(); i++) {
		dp.semi_axisA = weights_semi_axisA[i].value;

		// Loop over semi axis B weight points
		for(int j=0; j< (int)weights_semi_axisB.size(); j++) {
			dp.semi_axisB = weights_semi_axisB[j].value;

			// Loop over semi axis C weight points
			for(int k=0; k < (int)weights_semi_axisC.size(); k++) {
				dp.semi_axisC = weights_semi_axisC[k].value;

				//Calculate surface averaged radius
				suf_rad = sqrt(dp.semi_axisA * dp.semi_axisB);

				//Sum
				sum += weights_semi_axisA[i].weight
					* weights_semi_axisB[j].weight
					* weights_semi_axisC[k].weight * DiamEllip(dp.semi_axisC, suf_rad)/2.0;
				//Norm
				norm += weights_semi_axisA[i].weight* weights_semi_axisB[j].weight
					* weights_semi_axisC[k].weight;
			}
		}
	}
	if (norm != 0){
		//return the averaged value
		rad_out =  sum/norm;}
	else{
		//return normal value
		rad_out = DiamEllip(dp.semi_axisC, suf_rad)/2.0;}

	return rad_out;
}
