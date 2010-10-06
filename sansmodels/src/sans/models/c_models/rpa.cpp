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
#include "models.hh"
#include "parameters.hh"
#include <stdio.h>
using namespace std;

extern "C" {
	#include "rpa.h"
}

RPAModel :: RPAModel() {
	lcase_n = Parameter(0.0);
	ba = Parameter(5.0);
	bb = Parameter(5.0);
	bc = Parameter(5.0);
	bd = Parameter(5.0);

    Kab = Parameter(-0.0004);
    Kac = Parameter(-0.0004);
    Kad = Parameter(-0.0004);
    Kbc = Parameter(-0.0004);
    Kbd = Parameter(-0.0004);
    Kcd = Parameter(-0.0004);

    scale = Parameter(1.0);
    background = Parameter(0.0);

    Na = Parameter(1000.0);
    Phia = Parameter(0.25);
    va = Parameter(100.0);
    La = Parameter(1.0e-012);

    Nb = Parameter(1000.0);
    Phib = Parameter(0.25);
    vb = Parameter(100.0);
    Lb = Parameter(1.0e-012);

    Nc = Parameter(1000.0);
    Phic = Parameter(0.25);
    vc = Parameter(100.0);
    Lc = Parameter(1.0e-012);

    Nd = Parameter(1000.0);
    Phid = Parameter(0.25);
    vd = Parameter(100.0);
    Ld = Parameter(0.0e-012);

}

/**
 * Function to evaluate 1D scattering function
 * The NIST IGOR library is used for the actual calculation.
 * @param q: q-value
 * @return: function value
 */
double RPAModel :: operator()(double q) {
	double dp[29];
	// Fill parameter array for IGOR library
	// Add the background after averaging
	//Fittable parameters
	dp[0] = lcase_n();

	dp[1] = ba();
	dp[2] = bb();
	dp[3] = bc();
	dp[4] = bd();

	dp[5] = Kab();
	dp[6] = Kac();
	dp[7] = Kad();
	dp[8] = Kbc();
	dp[9] = Kbd();
	dp[10] = Kcd();

	dp[11] = scale();
	dp[12] = background();

	//Fixed parameters
	dp[13] = Na();
	dp[14] = Phia();
	dp[15] = va();
	dp[16] = La();

	dp[17] = Nb();
	dp[18] = Phib();
	dp[19] = vb();
	dp[20] = Lb();

	dp[21] = Nc();
	dp[22] = Phic();
	dp[23] = vc();
	dp[24] = Lc();

	dp[25] = Nd();
	dp[26] = Phid();
	dp[27] = vd();
	dp[28] = Ld();

	return rpa_kernel(dp,q);
}

/**
 * Function to evaluate 2D scattering function
 * @param q_x: value of Q along x
 * @param q_y: value of Q along y
 * @return: function value
 */
double RPAModel :: operator()(double qx, double qy) {
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
double RPAModel :: evaluate_rphi(double q, double phi) {
	return (*this).operator()(q);
}

/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double RPAModel :: calculate_ER() {
//NOT implemented!!!
}
