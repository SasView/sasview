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
	#include "cylinder.h"
}

CylinderModel :: CylinderModel() {
	scale      = Parameter(1.0);
	radius     = Parameter(20.0, true);
	radius.set_min(0.0);
	length     = Parameter(400.0, true);
	length.set_min(0.0);
	contrast   = Parameter(3.e-6);
	background = Parameter(0.0);
	cyl_theta  = Parameter(0.0, true);
	cyl_phi    = Parameter(0.0, true);
}

/**
 * Function to evaluate 1D scattering function
 * The NIST IGOR library is used for the actual calculation.
 * @param q: q-value
 * @return: function value
 */
double CylinderModel :: operator()(double q) {
	double dp[5];

	// Fill parameter array for IGOR library
	// Add the background after averaging
	dp[0] = scale();
	dp[1] = radius();
	dp[2] = length();
	dp[3] = contrast();
	dp[4] = 0.0;

	// Get the dispersion points for the radius
	vector<WeightPoint> weights_rad;
	radius.get_weights(weights_rad);

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
			dp[2] = weights_len[j].value;

			sum += weights_rad[i].weight
				* weights_len[j].weight * CylinderForm(dp, q);
			norm += weights_rad[i].weight
				* weights_len[j].weight;
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
double CylinderModel :: operator()(double qx, double qy) {
	CylinderParameters dp;
	// Fill parameter array
	dp.scale      = scale();
	dp.radius     = radius();
	dp.length     = length();
	dp.contrast   = contrast();
	dp.background = 0.0;
	dp.cyl_theta  = cyl_theta();
	dp.cyl_phi    = cyl_phi();

	// Get the dispersion points for the radius
	vector<WeightPoint> weights_rad;
	radius.get_weights(weights_rad);

	// Get the dispersion points for the length
	vector<WeightPoint> weights_len;
	length.get_weights(weights_len);

	// Get angular averaging for theta
	vector<WeightPoint> weights_theta;
	cyl_theta.get_weights(weights_theta);

	// Get angular averaging for phi
	vector<WeightPoint> weights_phi;
	cyl_phi.get_weights(weights_phi);

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;

	// Loop over radius weight points
	for(int i=0; i<weights_rad.size(); i++) {
		dp.radius = weights_rad[i].value;


		// Loop over length weight points
		for(int j=0; j<weights_len.size(); j++) {
			dp.length = weights_len[j].value;

			// Average over theta distribution
			for(int k=0; k<weights_theta.size(); k++) {
				dp.cyl_theta = weights_theta[k].value;

				// Average over phi distribution
				for(int l=0; l<weights_phi.size(); l++) {
					dp.cyl_phi = weights_phi[l].value;

					double _ptvalue = weights_rad[i].weight
						* weights_len[j].weight
						* weights_theta[k].weight
						* weights_phi[l].weight
						* cylinder_analytical_2DXY(&dp, qx, qy);
					if (weights_theta.size()>1) {
						_ptvalue *= sin(weights_theta[k].value);
					}
					sum += _ptvalue;

					norm += weights_rad[i].weight
						* weights_len[j].weight
						* weights_theta[k].weight
						* weights_phi[l].weight;

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
double CylinderModel :: evaluate_rphi(double q, double phi) {
	double qx = q*cos(phi);
	double qy = q*sin(phi);
	return (*this).operator()(qx, qy);
}
/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double CylinderModel :: calculate_ER() {
	CylinderParameters dp;

	dp.radius     = radius();
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
// Testing code
int main(void)
{
	CylinderModel c = CylinderModel();

	printf("Length = %g\n", c.length());
	printf("I(Qx=%g,Qy=%g) = %g\n", 0.001, 0.001, c(0.001, 0.001));
	printf("I(Q=%g) = %g\n", 0.001, c(0.001));
	c.radius.dispersion = new GaussianDispersion();
	c.radius.dispersion->npts = 100;
	c.radius.dispersion->width = 5;

	//c.length.dispersion = GaussianDispersion();
	//c.length.dispersion.npts = 20;
	//c.length.dispersion.width = 65;

	printf("I(Q=%g) = %g\n", 0.001, c(0.001));
	c.scale = 10.0;
	printf("I(Q=%g) = %g\n", 0.001, c(0.001));
	printf("I(Qx=%g, Qy=%g) = %g\n", 0.001, 0.001, c(0.001, 0.001));
	printf("I(Q=%g,  Phi=%g) = %g\n", 0.00447, .7854, c.evaluate_rphi(sqrt(0.00002), .7854));

	// Average over phi at theta=90 deg
	c.cyl_theta = 1.57;
	double values_th[100];
	double values[100];
	double weights[100];
	double pi = acos(-1.0);
	printf("pi=%g\n", pi);
	for(int i=0; i<100; i++){
		values[i] = (float)i*2.0*pi/99.0;
		values_th[i] = (float)i*pi/99.0;
		weights[i] = 1.0;
	}
	//c.radius.dispersion->width = 0;
	c.cyl_phi.dispersion = new ArrayDispersion();
	c.cyl_theta.dispersion = new ArrayDispersion();
	(*c.cyl_phi.dispersion).set_weights(100, values, weights);
	(*c.cyl_theta.dispersion).set_weights(100, values_th, weights);

	double i_avg = c(0.01, 0.01);
	double i_1d = c(sqrt(0.0002));

	printf("\nI(Qx=%g, Qy=%g) = %g\n", 0.01, 0.01, i_avg);
	printf("I(Q=%g)         = %g\n", sqrt(0.0002), i_1d);
	printf("ratio %g %g\n", i_avg/i_1d, i_1d/i_avg);


	return 0;
}

