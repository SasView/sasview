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
#include "corefourshell.h"

extern "C" {
	#include "libSphere.h"
}

typedef struct {
  double scale;
  double rad_core0;
  double sld_core0;
  double thick_shell1;
  double sld_shell1;
  double thick_shell2;
  double sld_shell2;
  double thick_shell3;
  double sld_shell3;
  double thick_shell4;
  double sld_shell4;
  double sld_solv;
  double background;
} CoreFourShellParameters;

CoreFourShellModel :: CoreFourShellModel() {
	scale      = Parameter(1.0);
	rad_core0     = Parameter(60.0, true);
	rad_core0.set_min(0.0);
	sld_core0   = Parameter(6.4e-6);
	thick_shell1     = Parameter(10.0, true);
	thick_shell1.set_min(0.0);
	sld_shell1   = Parameter(1.0e-6);
	thick_shell2     = Parameter(10.0, true);
	thick_shell2.set_min(0.0);
	sld_shell2   = Parameter(2.0e-6);
	thick_shell3     = Parameter(10.0, true);
	thick_shell3.set_min(0.0);
	sld_shell3   = Parameter(3.0e-6);
	thick_shell4     = Parameter(10.0, true);
	thick_shell4.set_min(0.0);
	sld_shell4   = Parameter(4.0e-6);
	sld_solv   = Parameter(6.4e-6);
	background = Parameter(0.001);
}

/**
 * Function to evaluate 1D scattering function
 * The NIST IGOR library is used for the actual calculation.
 * @param q: q-value
 * @return: function value
 */
double CoreFourShellModel :: operator()(double q) {
	double dp[13];

	// Fill parameter array for IGOR library
	// Add the background after averaging
	dp[0] = scale();
	dp[1] = rad_core0();
	dp[2] = sld_core0();
	dp[3] = thick_shell1();
	dp[4] = sld_shell1();
	dp[5] = thick_shell2();
	dp[6] = sld_shell2();
	dp[7] = thick_shell3();
	dp[8] = sld_shell3();
	dp[9] = thick_shell4();
	dp[10] = sld_shell4();
	dp[11] = sld_solv();
	dp[12] = 0.0;

	// Get the dispersion points for the radius
	vector<WeightPoint> weights_rad;
	rad_core0.get_weights(weights_rad);

	// Get the dispersion points for the thick 1
	vector<WeightPoint> weights_s1;
	thick_shell1.get_weights(weights_s1);

	// Get the dispersion points for the thick 2
	vector<WeightPoint> weights_s2;
	thick_shell2.get_weights(weights_s2);

	// Get the dispersion points for the thick 3
	vector<WeightPoint> weights_s3;
	thick_shell3.get_weights(weights_s3);

	// Get the dispersion points for the thick 4
	vector<WeightPoint> weights_s4;
	thick_shell4.get_weights(weights_s4);

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;
	double vol = 0.0;

	// Loop over radius weight points
	for(size_t i=0; i<weights_rad.size(); i++) {
		dp[1] = weights_rad[i].value;
		// Loop over radius weight points
		for(size_t j=0; j<weights_s1.size(); j++) {
			dp[3] = weights_s1[j].value;
			// Loop over radius weight points
			for(size_t k=0; k<weights_s2.size(); k++) {
				dp[5] = weights_s2[k].value;
				// Loop over radius weight points
				for(size_t l=0; l<weights_s3.size(); l++) {
					dp[7] = weights_s3[l].value;
					// Loop over radius weight points
					for(size_t m=0; m<weights_s4.size(); m++) {
						dp[9] = weights_s4[m].value;
						//Un-normalize FourShell by volume
						sum += weights_rad[i].weight*weights_s1[j].weight*weights_s2[k].weight*weights_s3[l].weight*weights_s4[m].weight
							* FourShell(dp, q) * pow((weights_rad[i].value+weights_s1[j].value+weights_s2[k].value+weights_s3[l].value+weights_s4[m].value),3);
						//Find average volume
						vol += weights_rad[i].weight*weights_s1[j].weight*weights_s2[k].weight*weights_s3[l].weight*weights_s4[m].weight
							* pow((weights_rad[i].value+weights_s1[j].value+weights_s2[k].value+weights_s3[l].value+weights_s4[m].value),3);

						norm += weights_rad[i].weight*weights_s1[j].weight*weights_s2[k].weight*weights_s3[l].weight*weights_s4[m].weight;
					}
				}
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
double CoreFourShellModel :: operator()(double qx, double qy) {
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
double CoreFourShellModel :: evaluate_rphi(double q, double phi) {
	return (*this).operator()(q);
}

/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double CoreFourShellModel :: calculate_ER() {
	CoreFourShellParameters dp;

	dp.scale = scale();
	dp.rad_core0 = rad_core0();
	dp.sld_core0 = sld_core0();
	dp.thick_shell1 = thick_shell1();
	dp.sld_shell1 = sld_shell1();
	dp.thick_shell2 = thick_shell2();
	dp.sld_shell2 = sld_shell2();
	dp.thick_shell3 = thick_shell3();
	dp.sld_shell3 = sld_shell3();
	dp.thick_shell4 = thick_shell4();
	dp.sld_shell4 = sld_shell4();
	dp.sld_solv = sld_solv();
	dp.background = 0.0;

	// Get the dispersion points for the radius
	vector<WeightPoint> weights_rad;
	rad_core0.get_weights(weights_rad);

	// Get the dispersion points for the thick 1
	vector<WeightPoint> weights_s1;
	thick_shell1.get_weights(weights_s1);

	// Get the dispersion points for the thick 2
	vector<WeightPoint> weights_s2;
	thick_shell2.get_weights(weights_s2);

	// Get the dispersion points for the thick 3
	vector<WeightPoint> weights_s3;
	thick_shell3.get_weights(weights_s3);

	// Get the dispersion points for the thick 4
	vector<WeightPoint> weights_s4;
	thick_shell4.get_weights(weights_s4);

	double rad_out = 0.0;
	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;

	// Loop over radius weight points
	for(size_t i=0; i<weights_rad.size(); i++) {
		dp.rad_core0 = weights_rad[i].value;
		// Loop over radius weight points
		for(size_t j=0; j<weights_s1.size(); j++) {
			dp.thick_shell1 = weights_s1[j].value;
			// Loop over radius weight points
			for(size_t k=0; k<weights_s2.size(); k++) {
				dp.thick_shell2 = weights_s2[k].value;
				// Loop over radius weight points
				for(size_t l=0; l<weights_s3.size(); l++) {
					dp.thick_shell3 = weights_s3[l].value;
					// Loop over radius weight points
					for(size_t m=0; m<weights_s4.size(); m++) {
						dp.thick_shell4 = weights_s4[m].value;
						//Un-normalize FourShell by volume
						sum += weights_rad[i].weight*weights_s1[j].weight*weights_s2[k].weight*weights_s3[l].weight*weights_s4[m].weight
							* (dp.rad_core0+dp.thick_shell1+dp.thick_shell2+dp.thick_shell3+dp.thick_shell4);
						norm += weights_rad[i].weight*weights_s1[j].weight*weights_s2[k].weight*weights_s3[l].weight*weights_s4[m].weight;
					}
				}
			}
		}
	}
	if (norm != 0){
		//return the averaged value
		rad_out =  sum/norm;}
	else{
		//return normal value
		rad_out = dp.rad_core0+dp.thick_shell1+dp.thick_shell2+dp.thick_shell3+dp.thick_shell4;}

	return rad_out;
}
double CoreFourShellModel :: calculate_VR() {
  return 1.0;
}
