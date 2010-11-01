/**
 * Scattering model classes
 * The classes use the IGOR library found in
 *   sansmodels/c_extensions/libmultifunc/librefl.h
 */

#include <math.h>
#include "models.hh"
#include "parameters.hh"
#include <stdio.h>
using namespace std;

extern "C" {
	#include "sld_cal.h"
}

SLDCalFunc :: SLDCalFunc() {
	fun_type     = Parameter(0);
	npts_inter   = Parameter(21);
	shell_num	 = Parameter(1);
	nu_inter	 = Parameter(2.5);
	sld_left 	 = Parameter(1.0e-06);
	sld_right	 = Parameter(2.0e-06);
}

/**
 * Function to evaluate 1D scattering function
 * @param q: q-value
 * @return: function value
 */
double SLDCalFunc :: operator()(double q) {
	SLDCalParameters dp;

	dp.fun_type = fun_type();
	dp.npts_inter = npts_inter();
	dp.shell_num = shell_num();
	dp.nu_inter = nu_inter();
	dp.sld_left = sld_left();
	dp.sld_right = sld_right();

	return sld_cal_analytical_1D(&dp, q);
}

/**
 * Function to evaluate 2D scattering function
 * @param q_x: value of Q along x
 * @param q_y: value of Q along y
 * @return: function value
 */
double SLDCalFunc :: operator()(double qx, double qy) {
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
double SLDCalFunc :: evaluate_rphi(double q, double phi) {
	return (*this).operator()(q);
}
/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double SLDCalFunc :: calculate_ER() {
//NOT implemented yet!!!
}
