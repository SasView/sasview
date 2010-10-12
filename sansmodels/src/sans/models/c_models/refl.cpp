
#include <math.h>
#include "models.hh"
#include "parameters.hh"
#include <stdio.h>
using namespace std;

extern "C" {
	#include "refl.h"
}

ReflModel :: ReflModel() {
	n_layers = Parameter(1.0);
	scale = Parameter(1.0);
	thick_inter0 = Parameter(1.0);
	func_inter0 = Parameter(0);
	sld_sub0 = Parameter(2.07e-06);
	sld_medium = Parameter(1.0e-06);
    background = Parameter(0.0);


    sld_flat1 = Parameter(3.0e-06);
    sld_flat2 = Parameter(3.5e-06);
    sld_flat3 = Parameter(4.0e-06);
    sld_flat4 = Parameter(3.5e-06);
    sld_flat5 = Parameter(4.0e-06);
    sld_flat6 = Parameter(3.5e-06);
    sld_flat7 = Parameter(4.0e-06);
    sld_flat8 = Parameter(3.5e-06);
    sld_flat9 = Parameter(4.0e-06);
    sld_flat10 = Parameter(3.5e-06);


    thick_inter1 = Parameter(1);
    thick_inter2 = Parameter(1);
    thick_inter3 = Parameter(1);
    thick_inter4 = Parameter(1);
    thick_inter5 = Parameter(1);
    thick_inter6 = Parameter(1);
    thick_inter7 = Parameter(1);
    thick_inter8 = Parameter(1);
    thick_inter9 = Parameter(1);
    thick_inter10 = Parameter(1);


    thick_flat1 = Parameter(15);
    thick_flat2 = Parameter(100);
    thick_flat3 = Parameter(100);
    thick_flat4 = Parameter(100);
    thick_flat5 = Parameter(100);
    thick_flat6 = Parameter(100);
    thick_flat7 = Parameter(100);
    thick_flat8 = Parameter(100);
    thick_flat9 = Parameter(100);
    thick_flat10 = Parameter(100);


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

    sldIM_flat1 = Parameter(0);
    sldIM_flat2 = Parameter(0);
    sldIM_flat3 = Parameter(0);
    sldIM_flat4 = Parameter(0);
    sldIM_flat5 = Parameter(0);
    sldIM_flat6 = Parameter(0);
    sldIM_flat7 = Parameter(0);
    sldIM_flat8 = Parameter(0);
    sldIM_flat9 = Parameter(0);
    sldIM_flat10 = Parameter(0);

    sldIM_sub0 = Parameter(0);
    sldIM_medium = Parameter(0);
}

/**
 * Function to evaluate 1D NR function
 * @param q: q-value
 * @return: function value
 */
double ReflModel :: operator()(double q) {
	double dp[59];
	// Fill parameter array for IGOR library
	// Add the background after averaging
	dp[0] = n_layers();
	dp[1] = scale();
	dp[2] = thick_inter0();
	dp[3] = func_inter0();
	dp[4] = sld_sub0();
	dp[5] = sld_medium();
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

	dp[47] = sldIM_flat1();
	dp[48] = sldIM_flat2();
	dp[49] = sldIM_flat3();
	dp[50] = sldIM_flat4();
	dp[51] = sldIM_flat5();
	dp[52] = sldIM_flat6();
	dp[53] = sldIM_flat7();
	dp[54] = sldIM_flat8();
	dp[55] = sldIM_flat9();
	dp[56] = sldIM_flat10();

	dp[57] = sldIM_sub0();
	dp[58] = sldIM_medium();

	// Get the dispersion points for the radius
	//vector<WeightPoint> weights_thick;
	//thick_inter0.get_weights(weights_thick_inter0);


	return re_kernel(dp,q);
}

/**
 * Function to evaluate 2D NR function
 * @param q_x: value of Q along x
 * @param q_y: value of Q along y
 * @return: function value
 */
double ReflModel :: operator()(double qx, double qy) {
	double q = sqrt(qx*qx + qy*qy);
	return (*this).operator()(q);
}

/**
 * Function to evaluate 2D NR function
 * @param pars: parameters of the sphere
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double ReflModel :: evaluate_rphi(double q, double phi) {
	return (*this).operator()(q);
}

/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double ReflModel :: calculate_ER() {
	//NOT implemented yet!!!
}
