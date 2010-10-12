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
	#include "onion.h"
}

OnionModel :: OnionModel() {
	n_shells = Parameter(1.0);
	scale = Parameter(1.0);
	rad_core0 = Parameter(200.0);
	sld_core0 = Parameter(1e-06);
	sld_solv = Parameter(6.4e-06);
    background = Parameter(0.0);


    sld_out_shell1 = Parameter(1.0e-06);
    sld_out_shell2 = Parameter(1.0e-06);
    sld_out_shell3 = Parameter(1.0e-06);
    sld_out_shell4 = Parameter(1.0e-06);
    sld_out_shell5 = Parameter(1.0e-06);
    sld_out_shell6 = Parameter(1.0e-06);
    sld_out_shell7 = Parameter(1.0e-06);
    sld_out_shell8 = Parameter(1.0e-06);
    sld_out_shell9 = Parameter(1.0e-06);
    sld_out_shell10 = Parameter(1.0e-06);


    sld_in_shell1 = Parameter(2.3e-06);
    sld_in_shell2 = Parameter(2.6e-06);
    sld_in_shell3 = Parameter(2.9e-06);
    sld_in_shell4 = Parameter(3.2e-06);
    sld_in_shell5 = Parameter(3.5e-06);
    sld_in_shell6 = Parameter(3.8e-06);
    sld_in_shell7 = Parameter(4.1e-06);
    sld_in_shell8 = Parameter(4.4e-06);
    sld_in_shell9 = Parameter(4.7e-06);
    sld_in_shell10 = Parameter(5.0e-06);


    A_shell1 = Parameter(1.0);
    A_shell2 = Parameter(1.0);
    A_shell3 = Parameter(1.0);
    A_shell4 = Parameter(1.0);
    A_shell5 = Parameter(1.0);
    A_shell6 = Parameter(1.0);
    A_shell7 = Parameter(1.0);
    A_shell8 = Parameter(1.0);
    A_shell9 = Parameter(1.0);
    A_shell10 = Parameter(1.0);


    thick_shell1 = Parameter(50.0);
    thick_shell2 = Parameter(50.0);
    thick_shell3 = Parameter(50.0);
    thick_shell4 = Parameter(50.0);
    thick_shell5 = Parameter(50.0);
    thick_shell6 = Parameter(50.0);
    thick_shell7 = Parameter(50.0);
    thick_shell8 = Parameter(50.0);
    thick_shell9 = Parameter(50.0);
    thick_shell10 = Parameter(50.0);


    func_shell1 = Parameter(2);
    func_shell2 = Parameter(2);
    func_shell3 = Parameter(2);
    func_shell4 = Parameter(2);
    func_shell5 = Parameter(2);
    func_shell6 = Parameter(2);
    func_shell7 = Parameter(2);
    func_shell8 = Parameter(2);
    func_shell9 = Parameter(2);
    func_shell10 = Parameter(2);

}

/**
 * Function to evaluate 1D scattering function
 * The NIST IGOR library is used for the actual calculation.
 * @param q: q-value
 * @return: function value
 */
double OnionModel :: operator()(double q) {
	double dp[56];
	// Fill parameter array for IGOR library
	// Add the background after averaging
	dp[0] = n_shells();
	dp[1] = scale();
	dp[2] = rad_core0();
	dp[3] = sld_core0();
	dp[4] = sld_solv();
	dp[5] = 0.0;

	dp[6] = sld_out_shell1();
	dp[7] = sld_out_shell2();
	dp[8] = sld_out_shell3();
	dp[9] = sld_out_shell4();
	dp[10] = sld_out_shell5();
	dp[11] = sld_out_shell6();
	dp[12] = sld_out_shell7();
	dp[13] = sld_out_shell8();
	dp[14] = sld_out_shell9();
	dp[15] = sld_out_shell10();

	dp[16] = sld_in_shell1();
	dp[17] = sld_in_shell2();
	dp[18] = sld_in_shell3();
	dp[19] = sld_in_shell4();
	dp[20] = sld_in_shell5();
	dp[21] = sld_in_shell6();
	dp[22] = sld_in_shell7();
	dp[23] = sld_in_shell8();
	dp[24] = sld_in_shell9();
	dp[25] = sld_in_shell10();

	dp[26] = A_shell1();
	dp[27] = A_shell2();
	dp[28] = A_shell3();
	dp[29] = A_shell4();
	dp[30] = A_shell5();
	dp[31] = A_shell6();
	dp[32] = A_shell7();
	dp[33] = A_shell8();
	dp[34] = A_shell9();
	dp[35] = A_shell10();

	dp[36] = thick_shell1();
	dp[37] = thick_shell2();
	dp[38] = thick_shell3();
	dp[39] = thick_shell4();
	dp[40] = thick_shell5();
	dp[41] = thick_shell6();
	dp[42] = thick_shell7();
	dp[43] = thick_shell8();
	dp[44] = thick_shell9();
	dp[45] = thick_shell10();

	dp[46] = func_shell1();
	dp[47] = func_shell2();
	dp[48] = func_shell3();
	dp[49] = func_shell4();
	dp[50] = func_shell5();
	dp[51] = func_shell6();
	dp[52] = func_shell7();
	dp[53] = func_shell8();
	dp[54] = func_shell9();
	dp[55] = func_shell10();


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

	// Get the dispersion points for the thick 5
	vector<WeightPoint> weights_s5;
	thick_shell5.get_weights(weights_s5);

	// Get the dispersion points for the thick 6
	vector<WeightPoint> weights_s6;
	thick_shell6.get_weights(weights_s6);

	// Get the dispersion points for the thick 7
	vector<WeightPoint> weights_s7;
	thick_shell7.get_weights(weights_s7);

	// Get the dispersion points for the thick 8
	vector<WeightPoint> weights_s8;
	thick_shell8.get_weights(weights_s8);
	// Get the dispersion points for the thick 9
	vector<WeightPoint> weights_s9;
	thick_shell9.get_weights(weights_s9);

	// Get the dispersion points for the thick 10
	vector<WeightPoint> weights_s10;
	thick_shell10.get_weights(weights_s10);


	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;
	double vol = 0.0;

	// Loop over radius weight points
	for(int i=0; i<weights_rad.size(); i++) {
		dp[2] = weights_rad[i].value;
		// Loop over radius weight points
		for(int j=0; j<weights_s1.size(); j++) {
			dp[36] = weights_s1[j].value;
			// Loop over radius weight points
			for(int k=0; k<weights_s2.size(); k++) {
				dp[37] = weights_s2[k].value;
				// Loop over radius weight points
				for(int l=0; l<weights_s3.size(); l++) {
					dp[38] = weights_s3[l].value;
					// Loop over radius weight points
					for(int m=0; m<weights_s4.size(); m++) {
						dp[39] = weights_s4[m].value;
						for(int n=0; n<weights_s5.size(); n++) {
							dp[40] = weights_s5[n].value;
							for(int o=0; o<weights_s6.size(); o++) {
								dp[41] = weights_s6[o].value;
								for(int p=0; p<weights_s7.size(); p++) {
									dp[42] = weights_s7[p].value;
									for(int t=0; t<weights_s8.size(); t++) {
										dp[43] = weights_s8[t].value;
										for(int r=0; r<weights_s9.size(); r++) {
											dp[44] = weights_s9[r].value;
											for(int s=0; s<weights_s10.size(); s++) {
												dp[45] = weights_s10[s].value;
												//Un-normalize Shells by volume
												sum += weights_rad[i].weight*weights_s1[j].weight*weights_s2[k].weight*weights_s3[l].weight*weights_s4[m].weight
														*weights_s5[n].weight*weights_s6[o].weight*weights_s7[p].weight*weights_s8[t].weight
														*weights_s9[r].weight*weights_s10[s].weight
														* so_kernel(dp,q) * pow((weights_rad[i].value+weights_s1[j].value+weights_s2[k].value+weights_s3[l].value+weights_s4[m].value
																+weights_s5[n].value+weights_s6[o].value+weights_s7[p].value+weights_s8[t].value
																+weights_s9[r].value+weights_s10[s].value),3.0);
												//Find average volume
												vol += weights_rad[i].weight*weights_s1[j].weight*weights_s2[k].weight*weights_s3[l].weight*weights_s4[m].weight
													*weights_s5[n].weight*weights_s6[o].weight*weights_s7[p].weight*weights_s8[t].weight
													*weights_s9[r].weight*weights_s10[s].weight
													* pow((weights_rad[i].value+weights_s1[j].value+weights_s2[k].value+weights_s3[l].value+weights_s4[m].value
															+weights_s5[n].value+weights_s6[o].value+weights_s7[p].value+weights_s8[t].value
															+weights_s9[r].value+weights_s10[s].value),3.0);
												norm += weights_rad[i].weight*weights_s1[j].weight*weights_s2[k].weight*weights_s3[l].weight*weights_s4[m].weight
													*weights_s5[n].weight*weights_s6[o].weight*weights_s7[p].weight*weights_s8[t].weight
													*weights_s9[r].weight*weights_s10[s].weight;
											}
										}
									}
								}
							}
						}
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
double OnionModel :: operator()(double qx, double qy) {
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
double OnionModel :: evaluate_rphi(double q, double phi) {
	return (*this).operator()(q);
}

/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double OnionModel :: calculate_ER() {
	OnionParameters dp;
	dp.rad_core0 = rad_core0();
	dp.thick_shell1 = thick_shell1();
	dp.thick_shell2 = thick_shell2();
	dp.thick_shell3 = thick_shell3();
	dp.thick_shell4 = thick_shell4();
	dp.thick_shell5 = thick_shell5();
	dp.thick_shell6 = thick_shell6();
	dp.thick_shell7 = thick_shell7();
	dp.thick_shell8 = thick_shell8();
	dp.thick_shell9 = thick_shell9();
	dp.thick_shell10 = thick_shell10();


	double rad_out = 0.0;
	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;

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
	// Get the dispersion points for the thick 5
	vector<WeightPoint> weights_s5;
	thick_shell5.get_weights(weights_s5);

	// Get the dispersion points for the thick 6
	vector<WeightPoint> weights_s6;
	thick_shell6.get_weights(weights_s6);

	// Get the dispersion points for the thick 7
	vector<WeightPoint> weights_s7;
	thick_shell7.get_weights(weights_s7);

	// Get the dispersion points for the thick 8
	vector<WeightPoint> weights_s8;
	thick_shell8.get_weights(weights_s8);
	// Get the dispersion points for the thick 9
	vector<WeightPoint> weights_s9;
	thick_shell9.get_weights(weights_s9);

	// Get the dispersion points for the thick 10
	vector<WeightPoint> weights_s10;
	thick_shell10.get_weights(weights_s10);


	// Loop over radius weight points
	for(int i=0; i<weights_rad.size(); i++) {
		dp.rad_core0 = weights_rad[i].value;
		// Loop over radius weight points
		for(int j=0; j<weights_s1.size(); j++) {
			dp.thick_shell1 = weights_s1[j].value;
			// Loop over radius weight points
			for(int k=0; k<weights_s2.size(); k++) {
				dp.thick_shell2 = weights_s2[k].value;
				// Loop over radius weight points
				for(int l=0; l<weights_s3.size(); l++) {
					dp.thick_shell3 = weights_s3[l].value;
					// Loop over radius weight points
					for(int m=0; m<weights_s4.size(); m++) {
						dp.thick_shell4 = weights_s4[m].value;
						// Loop over radius weight points
						for(int n=0; j<weights_s5.size(); n++) {
							dp.thick_shell5 = weights_s5[n].value;
							// Loop over radius weight points
							for(int o=0; k<weights_s6.size(); o++) {
								dp.thick_shell6 = weights_s6[o].value;
								// Loop over radius weight points
								for(int p=0; l<weights_s7.size(); p++) {
									dp.thick_shell7 = weights_s7[p].value;
									// Loop over radius weight points
									for(int t=0; m<weights_s8.size(); t++) {
										dp.thick_shell8 = weights_s8[t].value;
										// Loop over radius weight points
										for(int r=0; l<weights_s9.size(); r++) {
											dp.thick_shell8 = weights_s9[r].value;
											// Loop over radius weight points
											for(int s=0; m<weights_s10.size(); s++) {
												dp.thick_shell10 = weights_s10[s].value;
												//Un-normalize FourShell by volume
												sum += weights_rad[i].weight*weights_s1[j].weight*weights_s2[k].weight*weights_s3[l].weight*weights_s4[m].weight
													*weights_s5[n].weight*weights_s6[o].weight*weights_s7[p].weight*weights_s8[t].weight
													*weights_s9[r].weight*weights_s10[s].weight
													* (dp.rad_core0+dp.thick_shell1+dp.thick_shell2+dp.thick_shell3+dp.thick_shell4+dp.thick_shell5
															+dp.thick_shell6+dp.thick_shell7+dp.thick_shell8+dp.thick_shell9+dp.thick_shell10);
												norm += weights_rad[i].weight*weights_s1[j].weight*weights_s2[k].weight*weights_s3[l].weight
													*weights_s4[m].weight*weights_s5[n].weight*weights_s6[o].weight*weights_s7[p].weight
													*weights_s8[t].weight*weights_s9[r].weight*weights_s10[s].weight;
											}
										}
									}
								}
							}
						}
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
		rad_out = dp.rad_core0+dp.thick_shell1+dp.thick_shell2+dp.thick_shell3+dp.thick_shell4
					+dp.thick_shell5+dp.thick_shell6+dp.thick_shell7+dp.thick_shell8+dp.thick_shell9+dp.thick_shell10;}
	return rad_out;
}
