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

extern "C" {
	#include "libSphere.h"
}

class BinaryHSPSF11Model{
public:
  // Model parameters
  Parameter l_radius;
  Parameter s_radius;
  Parameter vol_frac_ls;
  Parameter vol_frac_ss;
  Parameter ls_sld;
  Parameter ss_sld;
  Parameter solvent_sld;
  Parameter background;

  //Constructor
  BinaryHSPSF11Model();

  //Operators to get I(Q)
  double operator()(double q);
  double operator()(double qx , double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);
};

BinaryHSPSF11Model :: BinaryHSPSF11Model() {

	l_radius     = Parameter(160.0, true);
	l_radius.set_min(0.0);
	s_radius    = Parameter(25.0, true);
	s_radius.set_min(0.0);
	vol_frac_ls  = Parameter(0.2);
	vol_frac_ss  = Parameter(0.1);
	ls_sld      = Parameter(3.5e-6);
	ss_sld     = Parameter(5e-7);
	solvent_sld   = Parameter(6.36e-6);
	background = Parameter(0.0);
}

/**
 * Function to evaluate 1D scattering function
 * The NIST IGOR library is used for the actual calculation.
 * @param q: q-value
 * @return: function value
 */
double BinaryHSPSF11Model :: operator()(double q) {
	double dp[8];

	// Fill parameter array for IGOR library
	// Add the background after averaging
	dp[0] = l_radius();
	dp[1] = s_radius();
	dp[2] = vol_frac_ls();
	dp[3] = vol_frac_ss();
	dp[4] = ls_sld();
	dp[5] = ss_sld();
	dp[6] = solvent_sld();
	dp[7] = 0.0;


	// Get the dispersion points for the large radius
	vector<WeightPoint> weights_l_radius;
	l_radius.get_weights(weights_l_radius);

	// Get the dispersion points for the small radius
	vector<WeightPoint> weights_s_radius;
	s_radius.get_weights(weights_s_radius);

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;

	// Loop over larger radius weight points
	for(int i=0; i< (int)weights_l_radius.size(); i++) {
		dp[0] = weights_l_radius[i].value;

		// Loop over small radius weight points
		for(int j=0; j< (int)weights_s_radius.size(); j++) {
			dp[1] = weights_s_radius[j].value;


			sum += weights_l_radius[i].weight *weights_s_radius[j].weight * BinaryHS_PSF11(dp, q);
			norm += weights_l_radius[i].weight *weights_s_radius[j].weight;
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
double BinaryHSPSF11Model :: operator()(double qx, double qy) {
	double q = sqrt(qx*qx + qy*qy);
	return (*this).operator()(q);
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the vesicle
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double BinaryHSPSF11Model :: evaluate_rphi(double q, double phi) {
	return (*this).operator()(q);
}
/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double BinaryHSPSF11Model :: calculate_ER() {
//NOT implemented yet!!!
	return 0.0;
}
double BinaryHSPSF11Model :: calculate_VR() {
  return 1.0;
}
