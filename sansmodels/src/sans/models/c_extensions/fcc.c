/*
 * Scattering model for a SC_ParaCrystal
 */
#include "fcc.h"
#include "libSphere.h"
#include <math.h>


/**
 * Function to evaluate 1D scattering function
 * @param pars: parameters of the FCC_ParaCrystal
 * @param q: q-value
 * @return: function value
 */
double fcc_analytical_1D(FCParameters *pars, double q) {
	double dp[7];
	double result;

	dp[0] = pars->scale;
	dp[1] = pars->dnn;
	dp[2] = pars->d_factor;
	dp[3] = pars->radius;
	dp[4] = pars->sldSph;
	dp[5] = pars->sldSolv;
	dp[6] = pars->background;

	result = FCC_ParaCrystal(dp, q);
	// This FIXES a singualrity the kernel in libigor.
	if ( result == INFINITY || result == NAN){
		result = pars->background;
	}
	return result;
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the FCC_ParaCrystal
 * @param q: q-value
 * @return: function value
 */
double fc_analytical_2DXY(FCParameters *pars, double qx, double qy){
	double q;
	q = sqrt(qx*qx+qy*qy);
	return fc_analytical_2D_scaled(pars, q, qx/q, qy/q);
}

double fc_analytical_2D(FCParameters *pars, double q, double phi) {
	return fc_analytical_2D_scaled(pars, q, cos(phi), sin(phi));
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the FCCCrystalModel
 * @param q: q-value
 * @param q_x: q_x / q
 * @param q_y: q_y / q
 * @return: function value
 */
double fc_analytical_2D_scaled(FCParameters *pars, double q, double q_x, double q_y) {
	double a3_x, a3_y, a3_z, a2_x, a2_y, a1_x, a1_y;
	double b3_x, b3_y, b3_z, b2_x, b2_y, b1_x, b1_y;
	double q_z;
	double alpha, vol, cos_val_a3, cos_val_a2, cos_val_a1;
	double a1_dot_q, a2_dot_q,a3_dot_q;
	double answer;
	double Pi = 4.0*atan(1.0);
	double aa, Da, qDa_2, latticeScale, Zq, Fkq, Fkq_2,contrast;

	double dp[5];
	dp[0] = 1.0;
	dp[1] = pars->radius;
	dp[2] = pars->sldSph;
	dp[3] = pars->sldSolv;
	dp[4] = 0.0;

	aa = pars->dnn;
	Da = pars->d_factor*aa;
	qDa_2 = pow(q*Da,2.0);
	//contrast = pars->sldSph - pars->sldSolv;

	latticeScale = 4.0*(4.0/3.0)*Pi*(dp[1]*dp[1]*dp[1])/pow(aa*sqrt(2.0),3.0);

	/// Angles here are respect to detector coordinate
	///  instead of against q coordinate(PRB 36(46), 3(6), 1754(3854))
    // b3 axis orientation
    b3_x = sin(pars->theta) * cos(pars->phi);//negative sign here???
    b3_y = sin(pars->theta) * sin(pars->phi);
    b3_z = cos(pars->theta);
    // b1 axis orientation
    b1_x = sin(pars->psi);
    b1_y = cos(pars->psi);
    // b2 axis orientation
    b2_x = sqrt(1.0-sin(pars->theta)*cos(pars->phi))*cos(pars->psi);
    b2_y = sqrt(1.0-sin(pars->theta)*cos(pars->phi))*sin(pars->psi);

    // a3 axis orientation
    a3_x = 0.5*(b2_x + b1_x);
    a3_y = 0.5*(b2_y + b1_y);
    a3_z = 0.0;
    // a1 axis orientation
    a1_x = 0.5*(b3_x + b2_x);
    a1_y = 0.5*(b3_y + b2_y);
    // a2 axis orientation
    a2_x = 0.5*(b3_x + b1_x);
    a2_y = 0.5*(b3_y + b1_y);

    // q vector
    q_z = 0.0; // for SANS; assuming qz is negligible

    // Compute the angle btw vector q and the a3 axis
    cos_val_a3 = a3_x*q_x + a3_y*q_y + a3_z*q_z;
    alpha = acos(cos_val_a3);
    a3_dot_q = aa*q*cos_val_a3;

    // a1 axis
    cos_val_a1 = a1_x*q_x + a1_y*q_y;
    a1_dot_q = aa*q*cos_val_a1*sin(alpha);

    // a2 axis
    cos_val_a2 = sin(acos(cos_val_a1));//a2_x*q_x + a2_y*q_y;
    a2_dot_q = aa*q*cos_val_a2*sin(alpha);

    // The following test should always pass
    if (fabs(cos_val_a3)>1.0) {
    	printf("parallel_ana_2D: Unexpected error: cos(alpha)>1\n");
     	return 0;
    }
    // Get Fkq and Fkq_2
    Fkq = exp(-0.5*pow(Da/aa,2.0)*(a1_dot_q*a1_dot_q+a2_dot_q*a2_dot_q+a3_dot_q*a3_dot_q));
    Fkq_2 = Fkq*Fkq;
    // Call Zq=Z1*Z2*Z3
    Zq = (1.0-Fkq_2)/(1.0-2.0*Fkq*cos(a1_dot_q)+Fkq_2);
    Zq = Zq * (1.0-Fkq_2)/(1.0-2.0*Fkq*cos(a2_dot_q)+Fkq_2);
    Zq = Zq * (1.0-Fkq_2)/(1.0-2.0*Fkq*cos(a3_dot_q)+Fkq_2);

	// Use SphereForm directly from libigor
	answer = SphereForm(dp,q)*Zq;

	//consider scales
	answer *= latticeScale * pars->scale;

	// This FIXES a singualrity the kernel in libigor.
	if ( answer == INFINITY || answer == NAN){
		answer = 0.0;
	}

	// add background
	answer += pars->background;

	return answer;
}
