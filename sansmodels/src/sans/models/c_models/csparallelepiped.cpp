/**
	This software was developed by the University of Tennessee as part of the
	Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
	project funded by the US National Science Foundation.

	If you use DANSE applications to do scientific research that leads to
	publication, we ask that you acknowledge the use of the software with the
	following sentence:

	"This work benefited from DANSE software developed under NSF award DMR-0520547."

	copyright 2010, University of Tennessee
 */

/**
 * Scattering model classes
 * The classes use the IGOR library found in
 *   sansmodels/src/libigor
 */

#include <math.h>
#include "models.hh"
#include "parameters.hh"
#include <stdio.h>
using namespace std;

extern "C" {
	#include "libCylinder.h"
	#include "libStructureFactor.h"
	#include "csparallelepiped.h"
}

CSParallelepipedModel :: CSParallelepipedModel() {
	scale      = Parameter(1.0);
	shortA     = Parameter(35.0, true);
	shortA.set_min(1.0);
	midB     = Parameter(75.0, true);
	midB.set_min(1.0);
	longC    = Parameter(400.0, true);
	longC.set_min(1.0);
	rimA     = Parameter(10.0, true);
	rimB     = Parameter(10.0, true);
	rimC     = Parameter(10.0, true);
	sld_rimA     = Parameter(2.0e-6, true);
	sld_rimB     = Parameter(4.0e-6, true);
	sld_rimC    = Parameter(2.0e-6, true);
	sld_pcore   = Parameter(1.0e-6);
	sld_solv   = Parameter(6.0e-6);
	background = Parameter(0.06);
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
double CSParallelepipedModel :: operator()(double q) {
	double dp[13];

	// Fill parameter array for IGOR library
	// Add the background after averaging
	dp[0] = scale();
	dp[1] = shortA();
	dp[2] = midB();
	dp[3] = longC();
	dp[4] = rimA();
	dp[5] = rimB();
	dp[6] = rimC();
	dp[7] = sld_rimA();
	dp[8] = sld_rimB();
	dp[9] = sld_rimC();
	dp[10] = sld_pcore();
	dp[11] = sld_solv();
	dp[12] = 0.0;

	// Get the dispersion points for the short_edgeA
	vector<WeightPoint> weights_shortA;
	shortA.get_weights(weights_shortA);

	// Get the dispersion points for the longer_edgeB
	vector<WeightPoint> weights_midB;
	midB.get_weights(weights_midB);

	// Get the dispersion points for the longuest_edgeC
	vector<WeightPoint> weights_longC;
	longC.get_weights(weights_longC);



	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;
	double vol = 0.0;

	// Loop over short_edgeA weight points
	for(int i=0; i< (int)weights_shortA.size(); i++) {
		dp[1] = weights_shortA[i].value;

		// Loop over longer_edgeB weight points
		for(int j=0; j< (int)weights_midB.size(); j++) {
			dp[2] = weights_midB[j].value;

			// Loop over longuest_edgeC weight points
			for(int k=0; k< (int)weights_longC.size(); k++) {
				dp[3] = weights_longC[k].value;
				//Un-normalize  by volume
				sum += weights_shortA[i].weight * weights_midB[j].weight
					* weights_longC[k].weight * CSParallelepiped(dp, q)
					* weights_shortA[i].value*weights_midB[j].value
					* weights_longC[k].value;
				//Find average volume
				vol += weights_shortA[i].weight * weights_midB[j].weight
					* weights_longC[k].weight
					* weights_shortA[i].value * weights_midB[j].value
					* weights_longC[k].value;

				norm += weights_shortA[i].weight
					 * weights_midB[j].weight * weights_longC[k].weight;
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
double CSParallelepipedModel :: operator()(double qx, double qy) {
	CSParallelepipedParameters dp;
	// Fill parameter array
	dp.scale      = scale();
	dp.shortA   = shortA();
	dp.midB   = midB();
	dp.longC  = longC();
	dp.rimA   = rimA();
	dp.rimB   = rimB();
	dp.rimC  = rimC();
	dp.sld_rimA   = sld_rimA();
	dp.sld_rimB   = sld_rimB();
	dp.sld_rimC  = sld_rimC();
	dp.sld_pcore   = sld_pcore();
	dp.sld_solv   = sld_solv();
	dp.background = 0.0;
	//dp.background = background();
	dp.parallel_theta  = parallel_theta();
	dp.parallel_phi    = parallel_phi();
	dp.parallel_psi    = parallel_psi();



	// Get the dispersion points for the short_edgeA
	vector<WeightPoint> weights_shortA;
	shortA.get_weights(weights_shortA);

	// Get the dispersion points for the longer_edgeB
	vector<WeightPoint> weights_midB;
	midB.get_weights(weights_midB);

	// Get the dispersion points for the longuest_edgeC
	vector<WeightPoint> weights_longC;
	longC.get_weights(weights_longC);

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
	double norm_vol = 0.0;
	double vol = 0.0;

	// Loop over radius weight points
	for(int i=0; i< (int)weights_shortA.size(); i++) {
		dp.shortA = weights_shortA[i].value;

		// Loop over longer_edgeB weight points
		for(int j=0; j< (int)weights_midB.size(); j++) {
			dp.midB = weights_midB[j].value;

			// Average over longuest_edgeC distribution
			for(int k=0; k< (int)weights_longC.size(); k++) {
				dp.longC = weights_longC[k].value;

				// Average over theta distribution
				for(int l=0; l< (int)weights_parallel_theta.size(); l++) {
				dp.parallel_theta = weights_parallel_theta[l].value;

					// Average over phi distribution
					for(int m=0; m< (int)weights_parallel_phi.size(); m++) {
						dp.parallel_phi = weights_parallel_phi[m].value;

						// Average over phi distribution
						for(int n=0; n< (int)weights_parallel_psi.size(); n++) {
							dp.parallel_psi = weights_parallel_psi[n].value;
							//Un-normalize by volume
							double _ptvalue = weights_shortA[i].weight
								* weights_midB[j].weight
								* weights_longC[k].weight
								* weights_parallel_theta[l].weight
								* weights_parallel_phi[m].weight
								* weights_parallel_psi[n].weight
								* csparallelepiped_analytical_2DXY(&dp, qx, qy)
								* weights_shortA[i].value*weights_midB[j].value
								* weights_longC[k].value;

							if (weights_parallel_theta.size()>1) {
								_ptvalue *= fabs(sin(weights_parallel_theta[l].value));
							}
							sum += _ptvalue;
							//Find average volume
							vol += weights_shortA[i].weight
								* weights_midB[j].weight
								* weights_longC[k].weight
								* weights_shortA[i].value*weights_midB[j].value
								* weights_longC[k].value;
							//Find norm for volume
							norm_vol += weights_shortA[i].weight
								* weights_midB[j].weight
								* weights_longC[k].weight;

							norm += weights_shortA[i].weight
								* weights_midB[j].weight
								* weights_longC[k].weight
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

	if (vol != 0.0 && norm_vol != 0.0) {
		//Re-normalize by avg volume
		sum = sum/(vol/norm_vol);}

	return sum/norm + background();
}


/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the cylinder
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double CSParallelepipedModel :: evaluate_rphi(double q, double phi) {
	double qx = q*cos(phi);
	double qy = q*sin(phi);
	return (*this).operator()(qx, qy);
}
/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double CSParallelepipedModel :: calculate_ER() {
	CSParallelepipedParameters dp;
	dp.shortA   = shortA();
	dp.midB   = midB();
	dp.longC  = longC();
	dp.rimA   = rimA();
	dp.rimB   = rimB();
	dp.rimC  = rimC();

	double rad_out = 0.0;
	double pi = 4.0*atan(1.0);
	double suf_rad = sqrt((dp.shortA*dp.midB+2.0*dp.rimA*dp.midB+2.0*dp.rimA*dp.shortA)/pi);
	double height =(dp.longC + 2.0*dp.rimC);
	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;

	// Get the dispersion points for the short_edgeA
	vector<WeightPoint> weights_shortA;
	shortA.get_weights(weights_shortA);

	// Get the dispersion points for the longer_edgeB
	vector<WeightPoint> weights_midB;
	midB.get_weights(weights_midB);

	// Get angular averaging for the longuest_edgeC
	vector<WeightPoint> weights_longC;
	longC.get_weights(weights_longC);

	// Loop over radius weight points
	for(int i=0; i< (int)weights_shortA.size(); i++) {
		dp.shortA = weights_shortA[i].value;

		// Loop over longer_edgeB weight points
		for(int j=0; j< (int)weights_midB.size(); j++) {
			dp.midB = weights_midB[j].value;

			// Average over longuest_edgeC distribution
			for(int k=0; k< (int)weights_longC.size(); k++) {
				dp.longC = weights_longC[k].value;
				//Calculate surface averaged radius
				//This is rough approximation.
				suf_rad = sqrt((dp.shortA*dp.midB+2.0*dp.rimA*dp.midB+2.0*dp.rimA*dp.shortA)/pi);
				height =(dp.longC + 2.0*dp.rimC);
				//Note: output of "DiamCyl(dp.length,dp.radius)" is a DIAMETER.
				sum +=weights_shortA[i].weight* weights_midB[j].weight
					* weights_longC[k].weight*DiamCyl(height, suf_rad)/2.0;
				norm += weights_shortA[i].weight* weights_midB[j].weight*weights_longC[k].weight;
			}
		}
	}

	if (norm != 0){
		//return the averaged value
		rad_out =  sum/norm;}
	else{
		//return normal value
		//Note: output of "DiamCyl(length,radius)" is DIAMETER.
		rad_out = DiamCyl(dp.longC, suf_rad)/2.0;}
	return rad_out;

}
