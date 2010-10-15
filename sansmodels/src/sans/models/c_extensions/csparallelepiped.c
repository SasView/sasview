/**
 * Scattering model for a csparallelepiped
 */

#include "csparallelepiped.h"
#include <math.h>
#include "libCylinder.h"
#include <stdio.h>
#include <stdlib.h>


/**
 * Function to evaluate 1D scattering function
 * @param pars: parameters of the CSparallelepiped
 * @param q: q-value
 * @return: function value
 */
double csparallelepiped_analytical_1D(CSParallelepipedParameters *pars, double q) {
	double dp[13];

	// Fill paramater array
	dp[0] = pars->scale;
	dp[1] = pars->shortA;
	dp[2] = pars->midB;
	dp[3] = pars->longC;
	dp[4] = pars->rimA;
	dp[5] = pars->rimB;
	dp[6] = pars->rimC;
	dp[7] = pars->sld_rimA;
	dp[8] = pars->sld_rimB;
	dp[9] = pars->sld_rimC;
	dp[10] = pars->sld_pcore;
	dp[11] = pars->sld_solv;
	dp[12] = pars->background;

	// Call library function to evaluate model
	//ToDo: Correct this 1d model, CSParallelepiped in libigor (2D corrected).
	return CSParallelepiped(dp, q);
}


double cspkernel(double dp[],double q, double ala, double alb, double alc){
    // mu passed in is really mu*sqrt(1-sig^2)
    double argA,argB,argC,argtA,argtB,argtC,tmp1,tmp2,tmp3,tmpt1,tmpt2,tmpt3;			//local variables

	double aa,bb,cc, ta,tb,tc;
	double Vin,Vot,V1,V2,V3;
	double rhoA,rhoB,rhoC, rhoP, rhosolv;
	double dr0, drA,drB, drC;
	double Pi,retVal;

	aa = dp[1];
	bb = dp[2];
	cc = dp[3];
	ta = dp[4];
	tb = dp[5];
	tc = dp[6];
	rhoA=dp[7];
	rhoB=dp[8];
	rhoC=dp[9];
	rhoP=dp[10];
	rhosolv=dp[11];
	dr0=rhoP-rhosolv;
	drA=rhoA-rhosolv;
	drB=rhoB-rhosolv;
	drC=rhoC-rhosolv;
	Vin=(aa*bb*cc);
	Vot=(aa*bb*cc+2.0*ta*bb*cc+2.0*aa*tb*cc+2.0*aa*bb*tc);
	V1=(2.0*ta*bb*cc);   //  incorrect V1 (aa*bb*cc+2*ta*bb*cc)
	V2=(2.0*aa*tb*cc);  // incorrect V2(aa*bb*cc+2*aa*tb*cc)
	V3=(2.0*aa*bb*tc);
	//aa = aa/bb;
	ta=(aa+2.0*ta);///bb;
	tb=(aa+2.0*tb);///bb;
	tc=(aa+2.0*tc);
    //handle arg=0 separately, as sin(t)/t -> 1 as t->0
    argA = q*aa*ala/2.0;
    argB = q*bb*alb/2.0;
    argC = q*cc*alc/2.0;
    argtA = q*ta*ala/2.0;
	argtB = q*tb*alb/2.0;
	argtC = q*tc*alc/2.0;

    if(argA==0.0) {
		tmp1 = 1.0;
	} else {
		tmp1 = sin(argA)/argA;
    }
    if (argB==0.0) {
		tmp2 = 1.0;
	} else {
		tmp2 = sin(argB)/argB;
    }

    if (argC==0.0) {
		tmp3 = 1.0;
	} else {
		tmp3 = sin(argC)/argC;
    }
    if(argtA==0.0) {
		tmpt1 = 1.0;
	} else {
		tmpt1 = sin(argtA)/argtA;
    }
    if (argtB==0.0) {
		tmpt2 = 1.0;
	} else {
		tmpt2 = sin(argtB)/argtB;
    }
    if (argtC==0.0) {
		tmpt3 = 1.0;
	} else {
		tmpt3 = sin(argtC)*sin(argtC)/argtC/argtC;
    }
    // This expression is different from NIST/IGOR package (I strongly believe the IGOR is wrong!!!). 10/15/2010.
    retVal =( dr0*tmp1*tmp2*tmp3*Vin + drA*(tmpt1-tmp1)*tmp2*tmp3*V1+ drB*tmp1*(tmpt2-tmp2)*tmp3*V2 + drC*tmp1*tmp2*(tmpt3-tmp3)*V3)*
				( dr0*tmp1*tmp2*tmp3*Vin + drA*(tmpt1-tmp1)*tmp2*tmp3*V1+ drB*tmp1*(tmpt2-tmp2)*tmp3*V2 + drC*tmp1*tmp2*(tmpt3-tmp3)*V3);   //  correct FF : square of sum of phase factors
    //retVal *= (tmp3*tmp3);
    retVal /= Vot;

    return (retVal);

}//Function cspkernel()




/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the CSparallelepiped
 * @param q: q-value
 * @return: function value
 */
double csparallelepiped_analytical_2DXY(CSParallelepipedParameters *pars, double qx, double qy) {
	double q;
	q = sqrt(qx*qx+qy*qy);
    return csparallelepiped_analytical_2D_scaled(pars, q, qx/q, qy/q);
}


/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the CSParallelepiped
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double csparallelepiped_analytical_2D(CSParallelepipedParameters *pars, double q, double phi) {
    return csparallelepiped_analytical_2D_scaled(pars, q, cos(phi), sin(phi));
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the CSparallelepiped
 * @param q: q-value
 * @param q_x: q_x / q
 * @param q_y: q_y / q
 * @return: function value
 */
double csparallelepiped_analytical_2D_scaled(CSParallelepipedParameters *pars, double q, double q_x, double q_y) {
	double dp[13];

	// Fill paramater array
	dp[0] = 1.0;
	dp[1] = pars->shortA;
	dp[2] = pars->midB;
	dp[3] = pars->longC;
	dp[4] = pars->rimA;
	dp[5] = pars->rimB;
	dp[6] = pars->rimC;
	dp[7] = pars->sld_rimA;
	dp[8] = pars->sld_rimB;
	dp[9] = pars->sld_rimC;
	dp[10] = pars->sld_pcore;
	dp[11] = pars->sld_solv;
	dp[12] = 0.0;

	double cparallel_x, cparallel_y, cparallel_z, bparallel_x, bparallel_y, parallel_x, parallel_y, parallel_z;
	double q_z;
	double alpha, vol, cos_val_c, cos_val_b, cos_val_a, edgeA, edgeB, edgeC;

	double answer;
	double pi = 4.0*atan(1.0);

	edgeA = pars->shortA;
	edgeB = pars->midB;
	edgeC = pars->longC;


    // parallelepiped c axis orientation
    cparallel_x = sin(pars->parallel_theta) * cos(pars->parallel_phi);
    cparallel_y = sin(pars->parallel_theta) * sin(pars->parallel_phi);
    cparallel_z = cos(pars->parallel_theta);

    // q vector
    q_z = 0.0;

    // Compute the angle btw vector q and the
    // axis of the parallelepiped
    cos_val_c = cparallel_x*q_x + cparallel_y*q_y + cparallel_z*q_z;
    alpha = acos(cos_val_c);

    // parallelepiped a axis orientation
    parallel_x = sin(pars->parallel_psi);//cos(pars->parallel_theta) * sin(pars->parallel_phi)*sin(pars->parallel_psi);
    parallel_y = cos(pars->parallel_psi);//cos(pars->parallel_theta) * cos(pars->parallel_phi)*cos(pars->parallel_psi);

    cos_val_a = parallel_x*q_x + parallel_y*q_y;



    // parallelepiped b axis orientation
    bparallel_x = sqrt(1.0-sin(pars->parallel_theta)*cos(pars->parallel_phi))*cos(pars->parallel_psi);//cos(pars->parallel_theta) * cos(pars->parallel_phi)* cos(pars->parallel_psi);
    bparallel_y = sqrt(1.0-sin(pars->parallel_theta)*cos(pars->parallel_phi))*sin(pars->parallel_psi);//cos(pars->parallel_theta) * sin(pars->parallel_phi)* sin(pars->parallel_psi);
    // axis of the parallelepiped
    cos_val_b = sin(acos(cos_val_a)) ;



    // The following test should always pass
    if (fabs(cos_val_c)>1.0) {
    	printf("parallel_ana_2D: Unexpected error: cos(alpha)>1\n");
     	return 0;
    }

	// Call the IGOR library function to get the kernel
	answer = cspkernel( dp,q, sin(alpha)*cos_val_a,sin(alpha)*cos_val_b,cos_val_c);

	//convert to [cm-1]
	answer *= 1.0e8;

	//Scale
	answer *= pars->scale;

	// add in the background
	answer += pars->background;

	return answer;
}

