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
 *	TODO: add 2d
 */

#include <math.h>
#include "parameters.hh"
#include <stdio.h>
using namespace std;
#include "flexible_cylinder.h"

extern "C" {
	#include "libCylinder.h"
	#include "libStructureFactor.h"
}

typedef struct {
  double scale;
  double length;
  double kuhn_length;
  double radius;
  double sldCyl;
  double sldSolv;
  double background;
} FlexibleCylinderParameters;

FlexibleCylinderModel :: FlexibleCylinderModel() {
	scale      = Parameter(1.0);
	length     = Parameter(1000.0, true);
	length.set_min(0.0);
	kuhn_length = Parameter(100.0, true);
	kuhn_length.set_min(0.0);
	radius  = Parameter(20.0, true);
	radius.set_min(0.0);
	sldCyl   = Parameter(1.0e-6);
	sldSolv   = Parameter(6.3e-6);
	background = Parameter(0.0001);
}

/**
 * Function to evaluate 1D scattering function
 * The NIST IGOR library is used for the actual calculation.
 * @param q: q-value
 * @return: function value
 */
double FlexibleCylinderModel :: operator()(double q) {
	double dp[7];

	// Fill parameter array for IGOR library
	// Add the background after averaging
	dp[0] = scale();
	dp[1] = length();
	dp[2] = kuhn_length();
	dp[3] = radius();
	dp[4] = sldCyl();
	dp[5] = sldSolv();
	dp[6] = 0.0;

	// Get the dispersion points for the length
	vector<WeightPoint> weights_len;
	length.get_weights(weights_len);

	// Get the dispersion points for the kuhn_length
	vector<WeightPoint> weights_kuhn;
	kuhn_length.get_weights(weights_kuhn);

	// Get the dispersion points for the radius
	vector<WeightPoint> weights_rad;
	radius.get_weights(weights_rad);

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;
	double vol = 0.0;

	// Loop over semi axis A weight points
	for(int i=0; i< (int)weights_len.size(); i++) {
		dp[1] = weights_len[i].value;

		// Loop over semi axis B weight points
		for(int j=0; j< (int)weights_kuhn.size(); j++) {
			dp[2] = weights_kuhn[j].value;

			// Loop over semi axis C weight points
			for(int k=0; k< (int)weights_rad.size(); k++) {
				dp[3] = weights_rad[k].value;
				//Un-normalize by volume
				sum += weights_len[i].weight
					* weights_kuhn[j].weight*weights_rad[k].weight * FlexExclVolCyl(dp, q)
					* pow(weights_rad[k].value,2.0)*weights_len[i].value;
				//Find average volume
				vol += weights_rad[k].weight
					* weights_len[i].weight
					* weights_kuhn[j].weight
					*pow(weights_rad[k].value,2.0)*weights_len[i].value;
				norm += weights_len[i].weight
					* weights_kuhn[j].weight*weights_rad[k].weight;
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
double FlexibleCylinderModel :: operator()(double qx, double qy) {
	double q = sqrt(qx*qx + qy*qy);
	return (*this).operator()(q);
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the triaxial ellipsoid
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double FlexibleCylinderModel :: evaluate_rphi(double q, double phi) {
	//double qx = q*cos(phi);
	//double qy = q*sin(phi);
	return (*this).operator()(q);
}
/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double FlexibleCylinderModel :: calculate_ER() {
	FlexibleCylinderParameters dp;

	dp.radius  = radius();
	dp.length     = length();

	double rad_out = 0.0;

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;

	// Get the dispersion points for the major shell
	vector<WeightPoint> weights_length;
	length.get_weights(weights_length);

	// Get the dispersion points for the minor shell
	vector<WeightPoint> weights_radius ;
	radius.get_weights(weights_radius);

	// Loop over major shell weight points
	for(int i=0; i< (int)weights_length.size(); i++) {
		dp.length = weights_length[i].value;
		for(int k=0; k< (int)weights_radius.size(); k++) {
			dp.radius = weights_radius[k].value;
			//Note: output of "DiamCyl(dp.length,dp.radius)" is DIAMETER.
			sum +=weights_length[i].weight
				* weights_radius[k].weight*DiamCyl(dp.length,dp.radius)/2.0;
			norm += weights_length[i].weight* weights_radius[k].weight;
		}
	}
	if (norm != 0){
		//return the averaged value
		rad_out =  sum/norm;}
	else{
		//return normal value
		//Note: output of "DiamCyl(dp.length,dp.radius)" is DIAMETER.
		rad_out = DiamCyl(dp.length,dp.radius)/2.0;}

	return rad_out;
}
double FlexibleCylinderModel :: calculate_VR() {
  return 1.0;
}
