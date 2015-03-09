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
 *	TODO: refactor so that we pull in the old sansmodels.c_extensions
 *	TODO: add 2D function
 */

#include <math.h>
#include "parameters.hh"
#include <stdio.h>
#include <stdlib.h>
using namespace std;
#include "lamellarPS.h"

extern "C" {
#include "libCylinder.h"
}

/*LamellarPS_kernel() was moved from libigor to get rid of polydipersity in del(thickness) that we provide from control panel.
  LamellarPSX  :  calculates the form factor of a lamellar structure - with S(q) effects included
-------
------- resolution effects ARE NOT included, but only a CONSTANT default value, not the real q-dependent resolution!!

 */
static double LamellarPS_kernel(double dp[], double q)
{
  double scale,dd,del,sld_bi,sld_sol,contr,NN,Cp,bkg;   //local variables of coefficient wave
  double inten, qval,Pq,Sq,alpha,temp,t1,t2,t3,dQ;
  double Pi,Euler,dQDefault,fii;
  int ii,NNint;
  Euler = 0.5772156649;   // Euler's constant
  dQDefault = 0.0;    //[=] 1/A, q-resolution, default value
  dQ = dQDefault;

  Pi = 4.0*atan(1.0);
  qval = q;

  scale = dp[0];
  dd = dp[1];
  del = dp[2];
  sld_bi = dp[3];
  sld_sol = dp[4];
  NN = trunc(dp[5]);    //be sure that NN is an integer
  Cp = dp[6];
  bkg = dp[7];

  contr = sld_bi - sld_sol;

  Pq = 2.0*contr*contr/qval/qval*(1.0-cos(qval*del));

  NNint = (int)NN;    //cast to an integer for the loop
  ii=0;
  Sq = 0.0;
  for(ii=1;ii<(NNint-1);ii+=1) {

    fii = (double)ii;   //do I really need to do this?

    temp = 0.0;
    alpha = Cp/4.0/Pi/Pi*(log(Pi*ii) + Euler);
    t1 = 2.0*dQ*dQ*dd*dd*alpha;
    t2 = 2.0*qval*qval*dd*dd*alpha;
    t3 = dQ*dQ*dd*dd*ii*ii;

    temp = 1.0-ii/NN;
    temp *= cos(dd*qval*ii/(1.0+t1));
    temp *= exp(-1.0*(t2 + t3)/(2.0*(1.0+t1)) );
    temp /= sqrt(1.0+t1);

    Sq += temp;
  }

  Sq *= 2.0;
  Sq += 1.0;

  inten = 2.0*Pi*scale*Pq*Sq/(dd*qval*qval);

  inten *= 1.0e8;   // 1/A to 1/cm

  return(inten+bkg);
}

LamellarPSModel :: LamellarPSModel() {
  scale      = Parameter(1.0);
  spacing    = Parameter(400.0, true);
  spacing.set_min(0.0);
  delta     = Parameter(30.0);
  delta.set_min(0.0);
  sld_bi   = Parameter(6.3e-6);
  sld_sol   = Parameter(1.0e-6);
  n_plates     = Parameter(20.0);
  caille = Parameter(0.1);
  background = Parameter(0.0);

}

/**
 * Function to evaluate 1D scattering function
 * The NIST IGOR library is used for the actual calculation.
 * @param q: q-value
 * @return: function value
 */
double LamellarPSModel :: operator()(double q) {
  double dp[8];

  // Fill parameter array for IGOR library
  // Add the background after averaging
  dp[0] = scale();
  dp[1] = spacing();
  dp[2] = delta();
  dp[3] = sld_bi();
  dp[4] = sld_sol();
  dp[5] = n_plates();
  dp[6] = caille();
  dp[7] = 0.0;


  // Get the dispersion points for spacing and delta (thickness)
  vector<WeightPoint> weights_spacing;
  spacing.get_weights(weights_spacing);
  vector<WeightPoint> weights_delta;
  delta.get_weights(weights_delta);

  // Perform the computation, with all weight points
  double sum = 0.0;
  double norm = 0.0;

  // Loop over short_edgeA weight points
  for(int i=0; i< (int)weights_spacing.size(); i++) {
    dp[1] = weights_spacing[i].value;
    //for(int j=0; j< (int)weights_spacing.size(); j++) {    BUGS fixed March 2015
    for(int j=0; j< (int)weights_delta.size(); j++) {
      //dp[2] = weights_delta[i].value;        BUG
      dp[2] = weights_delta[j].value;

      sum += weights_spacing[i].weight * weights_delta[j].weight * LamellarPS_kernel(dp, q);
      norm += weights_spacing[i].weight * weights_delta[j].weight;
    }
  }
  return sum/norm + background();
}
/**
 * Function to evaluate 2D scattering function
 * @param q_x: value of Q along x
 * @param q_y: value of Q along y
 * @return: function value
 */
double LamellarPSModel :: operator()(double qx, double qy) {
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
double LamellarPSModel :: evaluate_rphi(double q, double phi) {
  return (*this).operator()(q);
}
/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double LamellarPSModel :: calculate_ER() {
  //NOT implemented yet!!!
  return 0.0;
}
double LamellarPSModel :: calculate_VR() {
  return 1.0;
}
