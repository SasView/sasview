/**
 * Scattering model for a parallelepiped
 * TODO: Add 2D analysis
 */

#include "parallelepiped.h"
#include <math.h>
#include "libCylinder.h"
#include <stdio.h>
#include <stdlib.h>


/**
 * Function to evaluate 1D scattering function
 * @param pars: parameters of the parallelepiped
 * @param q: q-value
 * @return: function value
 */
double parallelepiped_analytical_1D(ParallelepipedParameters *pars, double q) {
	double dp[7];

	// Fill paramater array
	dp[0] = pars->scale;
	dp[1] = pars->short_a;
	dp[2] = pars->short_b;
	dp[3] = pars->long_c;
	dp[4] = pars->sldPipe;
	dp[5] = pars->sldSolv;
	dp[6] = pars->background;

	// Call library function to evaluate model
	return Parallelepiped(dp, q);
}


double pkernel(double a, double b,double c, double ala, double alb, double alc){
    // mu passed in is really mu*sqrt(1-sig^2)
    double argA,argB,argC,tmp1,tmp2,tmp3;			//local variables

    //handle arg=0 separately, as sin(t)/t -> 1 as t->0
    argA = a*ala/2.0;
    argB = b*alb/2.0;
    argC = c*alc/2.0;
    if(argA==0.0) {
		tmp1 = 1.0;
	} else {
		tmp1 = sin(argA)*sin(argA)/argA/argA;
    }
    if (argB==0.0) {
		tmp2 = 1.0;
	} else {
		tmp2 = sin(argB)*sin(argB)/argB/argB;
    }

    if (argC==0.0) {
		tmp3 = 1.0;
	} else {
		tmp3 = sin(argC)*sin(argC)/argC/argC;
    }

    return (tmp1*tmp2*tmp3);

}//Function pkernel()




/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the parallelepiped
 * @param q: q-value
 * @return: function value
 */
double parallelepiped_analytical_2DXY(ParallelepipedParameters *pars, double qx, double qy) {
	double q;
	q = sqrt(qx*qx+qy*qy);
    return parallelepiped_analytical_2D_scaled(pars, q, qx/q, qy/q);
}


/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the Parallelepiped
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double parallelepiped_analytical_2D(ParallelepipedParameters *pars, double q, double phi) {
    return parallelepiped_analytical_2D_scaled(pars, q, cos(phi), sin(phi));
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the parallelepiped
 * @param q: q-value
 * @param q_x: q_x / q
 * @param q_y: q_y / q
 * @return: function value
 */
double parallelepiped_analytical_2D_scaled(ParallelepipedParameters *pars, double q, double q_x, double q_y) {
	double cparallel_x, cparallel_y, cparallel_z, bparallel_x, bparallel_y, parallel_x, parallel_y, parallel_z;
	double q_z;
	double alpha, vol, cos_val_c, cos_val_b, cos_val_a, edgeA, edgeB, edgeC;

	double answer;
	double pi = 4.0*atan(1.0);

	edgeA = pars->short_a;
	edgeB = pars->short_b;
	edgeC = pars->long_c;


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
	answer = pkernel( q*edgeA, q*edgeB, q*edgeC, sin(alpha)*cos_val_a,sin(alpha)*cos_val_b,cos_val_c);

	// Multiply by contrast^2
	answer *= (pars->sldPipe - pars->sldSolv) * (pars->sldPipe - pars->sldSolv);

	//normalize by cylinder volume
	//NOTE that for this (Fournet) definition of the integral, one must MULTIPLY by Vparallel
    vol = edgeA* edgeB * edgeC;
	answer *= vol;

	//convert to [cm-1]
	answer *= 1.0e8;

	//Scale
	answer *= pars->scale;

	// add in the background
	answer += pars->background;

	return answer;
}

