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
	#include "libStructureFactor.h"
	#include "SquareWell.h"
}

SquareWellStructure :: SquareWellStructure() {
	effect_radius      = Parameter(50.0, true);
	effect_radius.set_min(0.0);
	volfraction = Parameter(0.04, true);
	volfraction.set_min(0.0);
	welldepth   = Parameter(1.50);
	wellwidth  = Parameter(1.20);
}

/**
 * Function to evaluate 1D scattering function
 * The NIST IGOR library is used for the actual calculation.
 * @param q: q-value
 * @return: function value
 */
double SquareWellStructure :: operator()(double q) {
	double dp[4];

	// Fill parameter array for IGOR library
	// Add the background after averaging
	dp[0] = effect_radius();
	dp[1] = volfraction();
	dp[2] = welldepth();
	dp[3] = wellwidth();

	// Get the dispersion points for the radius
	vector<WeightPoint> weights_rad;
	effect_radius.get_weights(weights_rad);

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;

	// Loop over radius weight points
	for(int i=0; i<weights_rad.size(); i++) {
		dp[0] = weights_rad[i].value;

		sum += weights_rad[i].weight
				* SquareWellStruct(dp, q);
		norm += weights_rad[i].weight;
	}
	return sum/norm ;
}

/**
 * Function to evaluate 2D scattering function
 * @param q_x: value of Q along x
 * @param q_y: value of Q along y
 * @return: function value
 */
double SquareWellStructure :: operator()(double qx, double qy) {
	double q = sqrt(qx*qx + qy*qy);
	return (*this).operator()(q);
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the cylinder
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double SquareWellStructure :: evaluate_rphi(double q, double phi) {
	double qx = q*cos(phi);
	double qy = q*sin(phi);
	return (*this).operator()(qx, qy);
}
/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double SquareWellStructure :: calculate_ER() {
//NOT implemented yet!!!
}
// Testing code
/*
int main(void)
{
	SquareWellModel c = SquareWellModel();

	printf("I(Qx=%g,Qy=%g) = %g\n", 0.001, 0.001, c(0.001, 0.001));
	printf("I(Q=%g) = %g\n", 0.001, c(0.001));
	c.radius.dispersion = new GaussianDispersion();
	c.radius.dispersion->npts = 100;
	c.radius.dispersion->width = 5;

	//c.length.dispersion = GaussianDispersion();
	//c.length.dispersion.npts = 20;
	//c.length.dispersion.width = 65;

	printf("I(Q=%g) = %g\n", 0.001, c(0.001));
	printf("I(Q=%g) = %g\n", 0.001, c(0.001));
	printf("I(Qx=%g, Qy=%g) = %g\n", 0.001, 0.001, c(0.001, 0.001));
	printf("I(Q=%g,  Phi=%g) = %g\n", 0.00447, .7854, c.evaluate_rphi(sqrt(0.00002), .7854));



	double i_avg = c(0.01, 0.01);
	double i_1d = c(sqrt(0.0002));

	printf("\nI(Qx=%g, Qy=%g) = %g\n", 0.01, 0.01, i_avg);
	printf("I(Q=%g)         = %g\n", sqrt(0.0002), i_1d);
	printf("ratio %g %g\n", i_avg/i_1d, i_1d/i_avg);


	return 0;
}
*/
