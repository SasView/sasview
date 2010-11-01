
#include <math.h>
#include "models.hh"
#include "parameters.hh"
#include <stdio.h>
using namespace std;

extern "C" {
	#include "spheresld.h"
}

SphereSLDModel :: SphereSLDModel() {
	n_shells = Parameter(1.0);
	scale = Parameter(1.0);
	thick_inter0 = Parameter(1.0);
	func_inter0 = Parameter(0);
	sld_core0 = Parameter(2.07e-06);
	sld_solv = Parameter(1.0e-06);
    background = Parameter(0.0);


    sld_flat1 = Parameter(2.7e-06);
    sld_flat2 = Parameter(3.5e-06);
    sld_flat3 = Parameter(4.0e-06);
    sld_flat4 = Parameter(3.5e-06);
    sld_flat5 = Parameter(4.0e-06);
    sld_flat6 = Parameter(3.5e-06);
    sld_flat7 = Parameter(4.0e-06);
    sld_flat8 = Parameter(3.5e-06);
    sld_flat9 = Parameter(4.0e-06);
    sld_flat10 = Parameter(3.5e-06);


    thick_inter1 = Parameter(1.0);
    thick_inter2 = Parameter(1.0);
    thick_inter3 = Parameter(1.0);
    thick_inter4 = Parameter(1.0);
    thick_inter5 = Parameter(1.0);
    thick_inter6 = Parameter(1.0);
    thick_inter7 = Parameter(1.0);
    thick_inter8 = Parameter(1.0);
    thick_inter9 = Parameter(1.0);
    thick_inter10 = Parameter(1.0);


    thick_flat1 = Parameter(100.0);
    thick_flat2 = Parameter(100.0);
    thick_flat3 = Parameter(100.0);
    thick_flat4 = Parameter(100.0);
    thick_flat5 = Parameter(100.0);
    thick_flat6 = Parameter(100.0);
    thick_flat7 = Parameter(100.0);
    thick_flat8 = Parameter(100.0);
    thick_flat9 = Parameter(100.0);
    thick_flat10 = Parameter(100.0);


    func_inter1 = Parameter(0);
    func_inter2 = Parameter(0);
    func_inter3 = Parameter(0);
    func_inter4 = Parameter(0);
    func_inter5 = Parameter(0);
    func_inter6 = Parameter(0);
    func_inter7 = Parameter(0);
    func_inter8 = Parameter(0);
    func_inter9 = Parameter(0);
    func_inter10 = Parameter(0);

    nu_inter1 = Parameter(2.5);
    nu_inter2 = Parameter(2.5);
    nu_inter3 = Parameter(2.5);
    nu_inter4 = Parameter(2.5);
    nu_inter5 = Parameter(2.5);
    nu_inter6 = Parameter(2.5);
    nu_inter7 = Parameter(2.5);
    nu_inter8 = Parameter(2.5);
    nu_inter9 = Parameter(2.5);
    nu_inter10 = Parameter(2.5);

    npts_inter = Parameter(35.0);
    nu_inter0 = Parameter(2.5);
    rad_core0 = Parameter(60.0);
}

/**
 * Function to evaluate 1D SphereSLD function
 * @param q: q-value
 * @return: function value
 */
double SphereSLDModel :: operator()(double q) {
	double dp[60];
	// Fill parameter array for IGOR library
	// Add the background after averaging
	dp[0] = n_shells();
	dp[1] = scale();
	dp[2] = thick_inter0();
	dp[3] = func_inter0();
	dp[4] = sld_core0();
	dp[5] = sld_solv();
	dp[6] = background();

	dp[7] = sld_flat1();
	dp[8] = sld_flat2();
	dp[9] = sld_flat3();
	dp[10] = sld_flat4();
	dp[11] = sld_flat5();
	dp[12] = sld_flat6();
	dp[13] = sld_flat7();
	dp[14] = sld_flat8();
	dp[15] = sld_flat9();
	dp[16] = sld_flat10();

	dp[17] = thick_inter1();
	dp[18] = thick_inter2();
	dp[19] = thick_inter3();
	dp[20] = thick_inter4();
	dp[21] = thick_inter5();
	dp[22] = thick_inter6();
	dp[23] = thick_inter7();
	dp[24] = thick_inter8();
	dp[25] = thick_inter9();
	dp[26] = thick_inter10();

	dp[27] = thick_flat1();
	dp[28] = thick_flat2();
	dp[29] = thick_flat3();
	dp[30] = thick_flat4();
	dp[31] = thick_flat5();
	dp[32] = thick_flat6();
	dp[33] = thick_flat7();
	dp[34] = thick_flat8();
	dp[35] = thick_flat9();
	dp[36] = thick_flat10();

	dp[37] = func_inter1();
	dp[38] = func_inter2();
	dp[39] = func_inter3();
	dp[40] = func_inter4();
	dp[41] = func_inter5();
	dp[42] = func_inter6();
	dp[43] = func_inter7();
	dp[44] = func_inter8();
	dp[45] = func_inter9();
	dp[46] = func_inter10();

	dp[47] = nu_inter1();
	dp[48] = nu_inter2();
	dp[49] = nu_inter3();
	dp[50] = nu_inter4();
	dp[51] = nu_inter5();
	dp[52] = nu_inter6();
	dp[53] = nu_inter7();
	dp[54] = nu_inter8();
	dp[55] = nu_inter9();
	dp[56] = nu_inter10();


	dp[57] = npts_inter();
	dp[58] = nu_inter0();
	dp[59] = rad_core0();

	// No polydispersion supported in this model.

	return sphere_sld_kernel(dp,q);
}

/**
 * Function to evaluate 2D SphereSLD function
 * @param q_x: value of Q along x
 * @param q_y: value of Q along y
 * @return: function value
 */
double SphereSLDModel :: operator()(double qx, double qy) {
	double q = sqrt(qx*qx + qy*qy);
	return (*this).operator()(q);
}

/**
 * Function to evaluate SphereSLD function
 * @param pars: parameters of the SphereSLD
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double SphereSLDModel :: evaluate_rphi(double q, double phi) {
	return (*this).operator()(q);
}

/**
 * Function to calculate TOTAL radius
 * ToDo: Find What is the effective radius for this model.
 * @return: effective radius value
 */
// No polydispersion supported in this model.
// Calculate max radius assumming max_radius = effective radius
// Note that this max radius is not affected by sld of layer, sld of interface, or
// sld of solvent.
double SphereSLDModel :: calculate_ER() {
	SphereSLDParameters dp;

	dp.n_shells = n_shells();

	dp.rad_core0 = rad_core0();
	dp.thick_flat1 = thick_flat1();
	dp.thick_flat2 = thick_flat2();
	dp.thick_flat3 = thick_flat3();
	dp.thick_flat4 = thick_flat4();
	dp.thick_flat5 = thick_flat5();
	dp.thick_flat6 = thick_flat6();
	dp.thick_flat7 = thick_flat7();
	dp.thick_flat8 = thick_flat8();
	dp.thick_flat9 = thick_flat9();
	dp.thick_flat10 = thick_flat10();

	dp.thick_inter0 = thick_inter0();
	dp.thick_inter1 = thick_inter1();
	dp.thick_inter2 = thick_inter2();
	dp.thick_inter3 = thick_inter3();
	dp.thick_inter4 = thick_inter4();
	dp.thick_inter5 = thick_inter5();
	dp.thick_inter6 = thick_inter6();
	dp.thick_inter7 = thick_inter7();
	dp.thick_inter8 = thick_inter8();
	dp.thick_inter9 = thick_inter9();
	dp.thick_inter10 = thick_inter10();

	double rad_out = dp.rad_core0 + dp.thick_inter0;
	if (dp.n_shells > 0)
		rad_out += dp.thick_flat1 + dp.thick_inter1;
	if (dp.n_shells > 1)
		rad_out += dp.thick_flat2 + dp.thick_inter2;
	if (dp.n_shells > 2)
		rad_out += dp.thick_flat3 + dp.thick_inter3;
	if (dp.n_shells > 3)
		rad_out += dp.thick_flat4 + dp.thick_inter4;
	if (dp.n_shells > 4)
		rad_out += dp.thick_flat5 + dp.thick_inter5;
	if (dp.n_shells > 5)
		rad_out += dp.thick_flat6 + dp.thick_inter6;
	if (dp.n_shells > 6)
		rad_out += dp.thick_flat7 + dp.thick_inter7;
	if (dp.n_shells > 7)
		rad_out += dp.thick_flat8 + dp.thick_inter8;
	if (dp.n_shells > 8)
		rad_out += dp.thick_flat9 + dp.thick_inter9;
	if (dp.n_shells > 9)
		rad_out += dp.thick_flat10 + dp.thick_inter10;

	return rad_out;

}
