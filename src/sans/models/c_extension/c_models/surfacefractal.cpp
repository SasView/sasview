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
using namespace std;
#include "surfacefractal.h"
extern "C" {
#include "libmultifunc/libfunc.h"
}

static double surface_fractal_kernel(double dp[], double q) {
  //fit parameters
  double scale = dp[0];
  double radius = dp[1];
  double surface_dim = dp[2];
  double co_length = dp[3];
  double background = dp[4];
  //others
  double pq = 0.0;
  double sq = 0.0;
  double mmo = 0.0;
  //result
  double result = 0.0;
  if( (q*radius) == 0.0){
		pq = 1.0;
  }
  else{
	//calculate P(q) for the spherical subunits; not normalized
	pq = pow((3.0*(sin(q*radius) - q*radius*cos(q*radius))/pow((q*radius),3)),2);
  }
  mmo = 5.0 - surface_dim;

  //calculate S(q)
  sq = exp(gamln(mmo))*sin(-(mmo)*atan(q*co_length));
  sq *= pow(co_length, mmo);
  sq /= pow((1.0 + (q*co_length)*(q*co_length)),(mmo/2.0));
  sq /= q;
  //combine and return
  result = pq * sq;
  result *= scale;
  result += background;

  return(result);
}

SurfaceFractalModel :: SurfaceFractalModel() {
  scale      = Parameter(1.0);
  radius = Parameter(10.0);
  surface_dim = Parameter(2.0);
  co_length = Parameter(500.0);
  background = Parameter(0.0);
}

/**
 * Function to evaluate 1D scattering function
 * @param q: q-value
 * @return: function value
 */
double SurfaceFractalModel :: operator()(double q) {
  double dp[5];

  // Add the background after averaging
  dp[0] = scale();
  dp[1] = radius();
  dp[2] = surface_dim();
  dp[3] = co_length();
  dp[4] = 0.0;

  // Perform the computation
  double sum = 0.0;

  sum = surface_fractal_kernel(dp, fabs(q));
  return sum + background();
}

/**
 * Function to evaluate 2D scattering function
 * @param q_x: value of Q along x
 * @param q_y: value of Q along y
 * @return: function value
 */
double SurfaceFractalModel :: operator()(double qx, double qy) {
  double q = sqrt(qx*qx + qy*qy);
  return (*this).operator()(q);
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the SurfaceFractalModel
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double SurfaceFractalModel :: evaluate_rphi(double q, double phi) {
  return (*this).operator()(q);
}

/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double SurfaceFractalModel :: calculate_ER() {
  //NOT implemented yet!!! 'cause None shape Model
  return 0.0;
}
double SurfaceFractalModel :: calculate_VR() {
  return 1.0;
}
