
#include <math.h>
#include "models.hh"
#include "parameters.hh"
#include <stdio.h>
using namespace std;

extern "C" {
	#include "pearlnecklace.h"
}

PearlNecklaceModel :: PearlNecklaceModel() {
	scale = Parameter(1.0);
	radius = Parameter(80.0, true);
	radius.set_min(0.0);
	edge_separation = Parameter(350.0, true);
	edge_separation.set_min(0.0);
	thick_string = Parameter(2.5, true);
	thick_string.set_min(0.0);
	num_pearls = Parameter(3);
	num_pearls.set_min(0.0);
	sld_pearl = Parameter(1.0e-06);
	sld_string = Parameter(5.0e-06);
	sld_solv = Parameter(0.5e-06);
    background = Parameter(0.0);

}

/**
 * Function to evaluate 1D PearlNecklaceModel function
 * @param q: q-value
 * @return: function value
 */
double PearlNecklaceModel :: operator()(double q) {
	double dp[9];
	// Fill parameter array for IGOR library
	// Add the background after averaging
	dp[0] = scale();
	dp[1] = radius();
	dp[2] = edge_separation();
	dp[3] = thick_string();
	dp[4] = num_pearls();
	dp[5] = sld_pearl();
	dp[6] = sld_string();
	dp[7] = sld_solv();
	dp[8] = 0.0;
	double pi = 4.0*atan(1.0);
	// No polydispersion supported in this model.
	// Get the dispersion points for the radius
	vector<WeightPoint> weights_radius;
	radius.get_weights(weights_radius);
	vector<WeightPoint> weights_edge_separation;
	edge_separation.get_weights(weights_edge_separation);
	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;
	double vol = 0.0;
	double string_vol = 0.0;
	double pearl_vol = 0.0;
	double tot_vol = 0.0;
	// Loop over core weight points
	for(int i=0; i<weights_radius.size(); i++) {
		dp[1] = weights_radius[i].value;
		// Loop over thick_inter0 weight points
		for(int j=0; j<weights_edge_separation.size(); j++) {
			dp[2] = weights_edge_separation[j].value;
			pearl_vol = 4.0 /3.0 * pi * pow(dp[1], 3);
			string_vol =dp[2] * pi * pow((dp[3] / 2.0), 2);
			tot_vol = (dp[4] - 1.0) * string_vol;
			tot_vol += dp[4] * pearl_vol;
			//Un-normalize Sphere by volume
			sum += weights_radius[i].weight * weights_edge_separation[j].weight
				* pearl_necklace_kernel(dp,q) * tot_vol;
			//Find average volume
			vol += weights_radius[i].weight * weights_edge_separation[j].weight
				* tot_vol;
			norm += weights_radius[i].weight * weights_edge_separation[j].weight;
		}
	}

	if (vol != 0.0 && norm != 0.0) {
		//Re-normalize by avg volume
		sum = sum/(vol/norm);}

	return sum/norm + background();
}

/**
 * Function to evaluate 2D PearlNecklaceModel function
 * @param q_x: value of Q along x
 * @param q_y: value of Q along y
 * @return: function value
 */
double PearlNecklaceModel :: operator()(double qx, double qy) {
	double q = sqrt(qx*qx + qy*qy);
	return (*this).operator()(q);
}

/**
 * Function to evaluate PearlNecklaceModel function
 * @param pars: parameters of the PearlNecklaceModel
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double PearlNecklaceModel :: evaluate_rphi(double q, double phi) {
	return (*this).operator()(q);
}

/**
 * Function to calculate TOTAL radius
 * Todo: decide whether or not we keep this calculation
 * @return: effective radius value
 */
// No polydispersion supported in this model.
// Calculate max radius assumming max_radius = effective radius
// Note that this max radius is not affected by sld of layer, sld of interface, or
// sld of solvent.
double PearlNecklaceModel :: calculate_ER() {
	PeralNecklaceParameters dp;

	dp.scale = scale();
	dp.radius = radius();
	dp.edge_separation = edge_separation();
	dp.thick_string = thick_string();
	dp.num_pearls = num_pearls();

	double rad_out = 0.0;
	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;
	double pi = 4.0*atan(1.0);
	// No polydispersion supported in this model.
	// Get the dispersion points for the radius
	vector<WeightPoint> weights_radius;
	radius.get_weights(weights_radius);
	vector<WeightPoint> weights_edge_separation;
	edge_separation.get_weights(weights_edge_separation);
	// Perform the computation, with all weight points
	double string_vol = 0.0;
	double pearl_vol = 0.0;
	double tot_vol = 0.0;
	// Loop over core weight points
	for(int i=0; i<weights_radius.size(); i++) {
		dp.radius = weights_radius[i].value;
		// Loop over thick_inter0 weight points
		for(int j=0; j<weights_edge_separation.size(); j++) {
			dp.edge_separation = weights_edge_separation[j].value;
			pearl_vol = 4.0 /3.0 * pi * pow(dp.radius , 3);
			string_vol =dp.edge_separation * pi * pow((dp.thick_string / 2.0), 2);
			tot_vol = (dp.num_pearls - 1.0) * string_vol;
			tot_vol += dp.num_pearls * pearl_vol;
			//Find  volume
			// This may be a too much approximation
			//Todo: decided whether or not we keep this calculation
			sum += weights_radius[i].weight * weights_edge_separation[j].weight
				* pow(3.0*tot_vol/4.0/pi,0.333333);
			norm += weights_radius[i].weight * weights_edge_separation[j].weight;
		}
	}

	if (norm != 0){
		//return the averaged value
		rad_out =  sum/norm;}
	else{
		//return normal value
		pearl_vol = 4.0 /3.0 * pi * pow(dp.radius , 3);
		string_vol =dp.edge_separation * pi * pow((dp.thick_string / 2.0), 2);
		tot_vol = (dp.num_pearls - 1.0) * string_vol;
		tot_vol += dp.num_pearls * pearl_vol;

		rad_out =  pow((3.0*tot_vol/4.0/pi), 0.33333);
		}

	return rad_out;

}
