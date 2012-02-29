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
#include "parameters.hh"
#include <stdio.h>
using namespace std;
#include "polygausscoil.h"

extern "C" {
	#include "libTwoPhase.h"
}

Poly_GaussCoil :: Poly_GaussCoil() {
	scale      = Parameter(1.0);
	rg     = Parameter(60.0, true);
	rg.set_min(0.0);
	poly_m   = Parameter(2.0);
	background = Parameter(0.001);
}

/**
 * Function to evaluate 1D scattering function
 * The NIST IGOR library is used for the actual calculation.
 * @param q: q-value
 * @return: function value
 */
double Poly_GaussCoil :: operator()(double q) {
	double dp[4];

	// Fill parameter array for IGOR library
	// Add the background after averaging
	dp[0] = scale();
	dp[1] = rg();
	dp[2] = poly_m();
	dp[3] = 0.0;

	// Get the dispersion points for the radius
	vector<WeightPoint> weights_rad;
	rg.get_weights(weights_rad);

	// Perform the computation, with all weight points
	double sum = 0.0;


	double norm = 0.0;
	double vol = 0.0;

	// Loop over radius weight points
	for(size_t i=0; i<weights_rad.size(); i++) {
		dp[1] = weights_rad[i].value;

		//Un-normalize SphereForm by volume
		sum += weights_rad[i].weight
			* PolyGaussCoil(dp, q) * pow(weights_rad[i].value,3);
		//Find average volume
		vol += weights_rad[i].weight
			* pow(weights_rad[i].value,3);

		norm += weights_rad[i].weight;
	}

	if (vol != 0.0 && norm != 0.0) {
		//Re-normalize by avg volume
		sum = sum/(vol/norm);}
	return sum/norm + background();


	sum = PolyGaussCoil(dp, q);
	return sum + background();
}

/**
 * Function to evaluate 2D scattering function
 * @param q_x: value of Q along x
 * @param q_y: value of Q along y
 * @return: function value
 */
double Poly_GaussCoil :: operator()(double qx, double qy) {
	double q = sqrt(qx*qx + qy*qy);
	return (*this).operator()(q);
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the sphere
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double Poly_GaussCoil :: evaluate_rphi(double q, double phi) {
	return (*this).operator()(q);
}

/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double Poly_GaussCoil :: calculate_ER() {
	double rad_out = 0.0;

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;

	// Get the dispersion points for the radius
	vector<WeightPoint> weights_rad;
	rg.get_weights(weights_rad);
	// Loop over radius weight points to average the radius value
	for(size_t i=0; i<weights_rad.size(); i++) {
		sum += weights_rad[i].weight
			* weights_rad[i].value;
		norm += weights_rad[i].weight;
	}
	if (norm != 0){
		//return the averaged value
		rad_out =  sum/norm;}
	else{
		//return normal value
		rad_out = rg();}

	return rad_out;
}
double Poly_GaussCoil :: calculate_VR() {
  return 1.0;
}
