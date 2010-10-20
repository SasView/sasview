/*
 * Scattering model for a BC_ParaCrystal
 */
#include "bcc.h"
#include "libSphere.h"
#include <math.h>


/**
 * Function to evaluate 1D scattering function
 * @param pars: parameters of the BCC_ParaCrystal
 * @param q: q-value
 * @return: function value
 */
double bcc_analytical_1D(BCParameters *pars, double q) {
	double dp[7];
	double result;

	dp[0] = pars->scale;
	dp[1] = pars->dnn;
	dp[2] = pars->d_factor;
	dp[3] = pars->radius;
	dp[4] = pars->sldSph;
	dp[5] = pars->sldSolv;
	dp[6] = pars->background;

	result = BCC_ParaCrystal(dp, q);
	// This FIXES a singualrity the kernel in libigor.
	if ( result == INFINITY || result == NAN){
		result = pars->background;
	}
	return result;
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the BCC_ParaCrystal
 * @param q: q-value
 * @return: function value
 */
double bc_analytical_2DXY(BCParameters *pars, double qx, double qy){
	double q;
	q = sqrt(qx*qx+qy*qy);
	return bc_analytical_2D_scaled(pars, q, qx/q, qy/q);
}

double bc_analytical_2D(BCParameters *pars, double q, double phi) {
	return bc_analytical_2D_scaled(pars, q, cos(phi), sin(phi));
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the BCCCrystalModel
 * @param q: q-value
 * @param q_x: q_x / q
 * @param q_y: q_y / q
 * @return: function value
 */
double bc_analytical_2D_scaled(BCParameters *pars, double q, double q_x, double q_y) {
	double a3_x, a3_y, a3_z, a2_x, a2_y, a1_x, a1_y;
	double b3_x, b3_y, b3_z, b2_x, b2_y, b1_x, b1_y;
	double q_z;
	double alpha, vol, cos_val_b3, cos_val_b2, cos_val_b1;
	double a1_dot_q, a2_dot_q,a3_dot_q;
	double answer;
	double Pi = 4.0*atan(1.0);
	double aa, Da, qDa_2, latticeScale, Zq, Fkq, Fkq_2;

	double dp[5];
	dp[0] = 1.0;
	dp[1] = pars->radius;
	dp[2] = pars->sldSph;
	dp[3] = pars->sldSolv;
	dp[4] = 0.0;

	aa = pars->dnn;
	Da = pars->d_factor*aa;
	qDa_2 = pow(q*Da,2.0);

	//the occupied volume of the lattice
	latticeScale = 2.0*(4.0/3.0)*Pi*(dp[1]*dp[1]*dp[1])/pow(aa/sqrt(3.0/4.0),3.0);
	// q vector
	q_z = 0.0; // for SANS; assuming qz is negligible
	/// Angles here are respect to detector coordinate
	///  instead of against q coordinate(PRB 36(46), 3(6), 1754(3854))
    // b3 axis orientation
    b3_x = sin(pars->theta) * cos(pars->phi);//negative sign here???
    b3_y = sin(pars->theta) * sin(pars->phi);
    b3_z = cos(pars->theta);
    cos_val_b3 =  b3_x*q_x + b3_y*q_y + b3_z*q_z;

    alpha = acos(cos_val_b3);
    // b1 axis orientation
    b1_x = sin(pars->psi);
    b1_y = cos(pars->psi);
	cos_val_b1 = (b1_x*q_x + b1_y*q_y);
    // b2 axis orientation
	cos_val_b2 = sin(acos(cos_val_b1));
	// alpha corrections
	cos_val_b2 *= sin(alpha);
	cos_val_b1 *= sin(alpha);

    // Compute the angle btw vector q and the a3 axis
    a3_dot_q = 0.5*aa*q*(cos_val_b2+cos_val_b1-cos_val_b3);

    // a1 axis
    a1_dot_q = 0.5*aa*q*(cos_val_b3+cos_val_b2-cos_val_b1);

    // a2 axis
    a2_dot_q = 0.5*aa*q*(cos_val_b3+cos_val_b1-cos_val_b2);

    // The following test should always pass
    if (fabs(cos_val_b3)>1.0) {
    	printf("bcc_ana_2D: Unexpected error: cos(alpha)>1\n");
     	return 0;
    }
    // Get Fkq and Fkq_2
    Fkq = exp(-0.5*pow(Da/aa,2.0)*(a1_dot_q*a1_dot_q+a2_dot_q*a2_dot_q+a3_dot_q*a3_dot_q));
    Fkq_2 = Fkq*Fkq;
    // Call Zq=Z1*Z2*Z3
    Zq = (1.0-Fkq_2)/(1.0-2.0*Fkq*cos(a1_dot_q)+Fkq_2);
    Zq *= (1.0-Fkq_2)/(1.0-2.0*Fkq*cos(a2_dot_q)+Fkq_2);
    Zq *= (1.0-Fkq_2)/(1.0-2.0*Fkq*cos(a3_dot_q)+Fkq_2);

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
