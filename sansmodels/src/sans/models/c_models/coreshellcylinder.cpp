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
	#include "core_shell_cylinder.h"
}

CoreShellCylinderModel :: CoreShellCylinderModel() {
	scale      = Parameter(1.0);
	radius     = Parameter(20.0, true);
	radius.set_min(0.0);
	thickness  = Parameter(10.0, true);
	thickness.set_min(0.0);
	length     = Parameter(400.0, true);
	length.set_min(0.0);
	core_sld   = Parameter(1.e-6);
	shell_sld  = Parameter(4.e-6);
	solvent_sld= Parameter(1.e-6);
	background = Parameter(0.0);
	axis_theta = Parameter(0.0, true);
	axis_phi   = Parameter(0.0, true);
}

/**
 * Function to evaluate 1D scattering function
 * The NIST IGOR library is used for the actual calculation.
 * @param q: q-value
 * @return: function value
 */
double CoreShellCylinderModel :: operator()(double q) {
	double dp[8];

	dp[0] = scale();
	dp[1] = radius();
	dp[2] = thickness();
	dp[3] = length();
	dp[4] = core_sld();
	dp[5] = shell_sld();
	dp[6] = solvent_sld();
	dp[7] = 0.0;

	// Get the dispersion points for the radius
	vector<WeightPoint> weights_rad;
	radius.get_weights(weights_rad);

	// Get the dispersion points for the thickness
	vector<WeightPoint> weights_thick;
	thickness.get_weights(weights_thick);

	// Get the dispersion points for the length
	vector<WeightPoint> weights_len;
	length.get_weights(weights_len);

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;

	// Loop over radius weight points
	for(int i=0; i<weights_rad.size(); i++) {
		dp[1] = weights_rad[i].value;

		// Loop over length weight points
		for(int j=0; j<weights_len.size(); j++) {
			dp[3] = weights_len[j].value;

			// Loop over thickness weight points
			for(int k=0; k<weights_thick.size(); k++) {
				dp[2] = weights_thick[k].value;

				sum += weights_rad[i].weight
					* weights_len[j].weight
					* weights_thick[k].weight
					* CoreShellCylinder(dp, q);
				norm += weights_rad[i].weight
				* weights_len[j].weight
				* weights_thick[k].weight;
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
double CoreShellCylinderModel :: operator()(double qx, double qy) {
	CoreShellCylinderParameters dp;
	// Fill parameter array
	dp.scale      = scale();
	dp.radius     = radius();
	dp.thickness  = thickness();
	dp.length     = length();
	dp.core_sld   = core_sld();
	dp.shell_sld  = shell_sld();
	dp.solvent_sld= solvent_sld();
	dp.background = 0.0;
	dp.axis_theta = axis_theta();
	dp.axis_phi   = axis_phi();

	// Get the dispersion points for the radius
	vector<WeightPoint> weights_rad;
	radius.get_weights(weights_rad);

	// Get the dispersion points for the thickness
	vector<WeightPoint> weights_thick;
	thickness.get_weights(weights_thick);

	// Get the dispersion points for the length
	vector<WeightPoint> weights_len;
	length.get_weights(weights_len);

	// Get angular averaging for theta
	vector<WeightPoint> weights_theta;
	axis_theta.get_weights(weights_theta);

	// Get angular averaging for phi
	vector<WeightPoint> weights_phi;
	axis_phi.get_weights(weights_phi);

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;

	// Loop over radius weight points
	for(int i=0; i<weights_rad.size(); i++) {
		dp.radius = weights_rad[i].value;


		// Loop over length weight points
		for(int j=0; j<weights_len.size(); j++) {
			dp.length = weights_len[j].value;

			// Loop over thickness weight points
			for(int m=0; m<weights_thick.size(); m++) {
				dp.thickness = weights_thick[m].value;

			// Average over theta distribution
			for(int k=0; k<weights_theta.size(); k++) {
				dp.axis_theta = weights_theta[k].value;

				// Average over phi distribution
				for(int l=0; l<weights_phi.size(); l++) {
					dp.axis_phi = weights_phi[l].value;

					double _ptvalue = weights_rad[i].weight
						* weights_len[j].weight
						* weights_thick[m].weight
						* weights_theta[k].weight
						* weights_phi[l].weight
						* core_shell_cylinder_analytical_2DXY(&dp, qx, qy);
					if (weights_theta.size()>1) {
						_ptvalue *= sin(weights_theta[k].value);
					}
					sum += _ptvalue;

					norm += weights_rad[i].weight
						* weights_len[j].weight
						* weights_thick[m].weight
						* weights_theta[k].weight
						* weights_phi[l].weight;

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
 * @param pars: parameters of the cylinder
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double CoreShellCylinderModel :: evaluate_rphi(double q, double phi) {
	double qx = q*cos(phi);
	double qy = q*sin(phi);
	return (*this).operator()(qx, qy);
}
/**
 * Function to calculate effective radius
 * @param pars: parameters of the sphere
 * @return: effective radius value
 */
double CoreShellCylinderModel :: calculate_ER() {
	CoreShellCylinderParameters dp;

	dp.radius     = radius();
	dp.thickness  = thickness();
	dp.length     = length();
	double rad_out = 0.0;

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;

	// Get the dispersion points for the major shell
	vector<WeightPoint> weights_length;
	length.get_weights(weights_length);

	// Get the dispersion points for the major shell
	vector<WeightPoint> weights_thickness;
	thickness.get_weights(weights_thickness);

	// Get the dispersion points for the minor shell
	vector<WeightPoint> weights_radius ;
	radius.get_weights(weights_radius);

	// Loop over major shell weight points
	for(int i=0; i< (int)weights_length.size(); i++) {
		dp.length = weights_length[i].value;
		for(int j=0; j< (int)weights_thickness.size(); j++) {
			dp.thickness = weights_thickness[j].value;
			for(int k=0; k< (int)weights_radius.size(); k++) {
				dp.radius = weights_radius[k].value;
				//Note: output of "DiamCyl(dp.length,dp.radius)" is DIAMETER.
				sum +=weights_length[i].weight * weights_thickness[j].weight
					* weights_radius[k].weight*DiamCyl(dp.length,dp.radius+dp.thickness)/2.0;
				norm += weights_length[i].weight* weights_thickness[j].weight* weights_radius[k].weight;
			}
		}
	}
	if (norm != 0){
		//return the averaged value
		rad_out =  sum/norm;}
	else{
		//return normal value
		//Note: output of "DiamCyl(dp.length,dp.radius)" is DIAMETER.
		rad_out = DiamCyl(dp.length,dp.radius+dp.thickness)/2.0;}

	return rad_out;
}
