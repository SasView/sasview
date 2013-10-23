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
#include "parameters.hh"
#include <stdio.h>
//#include <iostream>
using namespace std;
#include "TwoYukawa.h"

extern "C" {
#include "2Y_TwoYukawa.h"
}

TwoYukawaModel :: TwoYukawaModel() {
	// Model parameters
	volfraction = Parameter(0.2, true);
	effect_radius = Parameter(50.0, true);
	effect_radius.set_min(0.0);
	scale_K1 = Parameter(6.0);
	decayConst_Z1 = Parameter(10.0);
	scale_K2 = Parameter(-1.0);
	decayConst_Z2 = Parameter(2.0); 
}

/**
 * Function to evaluate 1D scattering function
 * The NIST IGOR library is used for the actual calculation.
 * @param q: q-value
 * @return: function value
 */
double TwoYukawaModel :: operator()(double q) 
{
  double dp[6];
  // Fill parameter array for IGOR library
  // Add the background after averaging
  dp[0] = volfraction();
  dp[1] = effect_radius();
  dp[2] = scale_K1();
  dp[3] = decayConst_Z1();
  dp[4] = scale_K2();
  dp[5] = decayConst_Z2();
  
  double ZERO = 1.0e-24;
  if (fabs(dp[2]) < 0.001){
  	return ZERO;
  	}
  if (fabs(dp[3]) < 0.001){
  	return ZERO;
  	}
  if (fabs(dp[4]) < 0.001){
  	return ZERO;
  	}
  if (fabs(dp[5]) < 0.001){
  	return ZERO;
  	}
  	
  double a, b, c1, c2, d1, d2;
  int check = 1;
  double x_in = q * dp[1] *2.0;
  int ok = 0;
  
  ok = TY_SolveEquations(dp[3], dp[5], dp[2], dp[4], dp[0], &a, &b, &c1, &c2, &d1, &d2, 0);
  if (ok > 0 ){
	//check = TY_CheckSolution(dp[3], dp[5], dp[2], dp[4], dp[0], &a, &b, &c1, &c2, &d1, &d2);
    if (check > 0){
    	return SqTwoYukawa(x_in, dp[3], dp[5], dp[2], dp[4], dp[0], a, b, c1, c2, d1, d2);
    }
    else{
    	return ZERO;
    }
  }
  else{
     return ZERO;
  }
}

/**
 * Function to evaluate 2D scattering function
 * @param q_x: value of Q along x
 * @param q_y: value of Q along y
 * @return: function value
 */
double TwoYukawaModel :: operator()(double qx, double qy)
{
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
double TwoYukawaModel :: evaluate_rphi(double q, double phi)
{
  double qx = q*cos(phi);
  double qy = q*sin(phi);
  return (*this).operator()(qx, qy);
}
/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double TwoYukawaModel :: calculate_ER()
{
  return effect_radius();
}
double TwoYukawaModel :: calculate_VR()
{
  return 1.0;
}

