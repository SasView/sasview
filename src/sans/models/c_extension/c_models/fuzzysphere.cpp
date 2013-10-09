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


#include <math.h>
#include "parameters.hh"
#include <stdio.h>
#include <stdlib.h>
using namespace std;
#include "fuzzysphere.h"

extern "C" {
#include "libSphere.h"
}

// scattering from a uniform sphere w/ fuzzy surface
// Modified from FuzzySpheres in libigor/libSphere.c without polydispersion: JHC
static double fuzzysphere_kernel(double dp[], double q){
  double pi,x,xr;
  double radius,sldSph,sldSolv,scale,bkg,delrho,fuzziness,f2,bes,vol,f;   //my local names

  pi = 4.0*atan(1.0);
  x= q;
  scale = dp[0];
  radius = dp[1];
  fuzziness = dp[2];
  sldSph = dp[3];
  sldSolv = dp[4];
  bkg = dp[5];
  delrho=sldSph-sldSolv;

  xr = x*radius;
  //handle xr==0 separately
  if(xr == 0.0){
    bes = 1.0;
  }else{
    bes = 3.0*(sin(xr)-xr*cos(xr))/(xr*xr*xr);
  }
  vol = 4.0*pi/3.0*radius*radius*radius;
  f = vol*bes*delrho;   // [=] A
  f *= exp(-0.5*fuzziness*fuzziness*x*x);
  // normalize to single particle volume, convert to 1/cm
  f2 = f * f / vol * 1.0e8;   // [=] 1/cm

  f2 *= scale;
  f2 += bkg;

    return(f2); //scale, and add in the background
}

FuzzySphereModel :: FuzzySphereModel() {
	scale      = Parameter(0.01);
	radius     = Parameter(60.0, true);
	radius.set_min(0.0);
	fuzziness  = Parameter(10.0);
	fuzziness.set_min(0.0);
	sldSph   = Parameter(1.0e-6);
	sldSolv   = Parameter(3.0e-6);
	background = Parameter(0.001);
}

/**
 * Function to evaluate 1D scattering function
 * The NIST IGOR library is used for the actual calculation.
 * @param q: q-value
 * @return: function value
 */
double FuzzySphereModel :: operator()(double q) {
	double dp[6];

	// Fill parameter array for IGOR library
	// Add the background after averaging
	dp[0] = scale();
	dp[1] = radius();
	dp[2] = fuzziness();
	dp[3] = sldSph();
	dp[4] = sldSolv();
	dp[5] = 0.0;

	// Get the dispersion points for the radius
	vector<WeightPoint> weights_radius;
	radius.get_weights(weights_radius);

	// Get the dispersion points for the fuzziness
	vector<WeightPoint> weights_fuzziness;
	fuzziness.get_weights(weights_fuzziness);

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;
	double norm_vol = 0.0;
	double vol = 0.0;

	// Loop over radius weight points
	for(size_t i=0; i<weights_radius.size(); i++) {
		dp[1] = weights_radius[i].value;
		// Loop over fuzziness weight points
		for(size_t j=0; j<weights_fuzziness.size(); j++) {
			dp[2] = weights_fuzziness[j].value;

			//Un-normalize SphereForm by volume
			sum += weights_radius[i].weight * weights_fuzziness[j].weight
				* fuzzysphere_kernel(dp, q) * pow(weights_radius[i].value,3);
			//Find average volume : Note the fuzziness has no contribution to the volume
			vol += weights_radius[i].weight
				* pow(weights_radius[i].value,3);

			norm += weights_radius[i].weight * weights_fuzziness[j].weight;
			norm_vol += weights_radius[i].weight;
		}
	}

	if (vol != 0.0 && norm_vol != 0.0) {
		//Re-normalize by avg volume
		sum = sum/(vol/norm_vol);}
	return sum/norm + background();
}

/**
 * Function to evaluate 2D scattering function
 * @param q_x: value of Q along x
 * @param q_y: value of Q along y
 * @return: function value
 */
double FuzzySphereModel :: operator()(double qx, double qy) {
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
double FuzzySphereModel :: evaluate_rphi(double q, double phi) {
	return (*this).operator()(q);
}

/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double FuzzySphereModel :: calculate_ER() {
	double rad_out = 0.0;

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;

	// Get the dispersion points for the radius
	// No need to consider the fuzziness.
	vector<WeightPoint> weights_radius;
	radius.get_weights(weights_radius);
	// Loop over radius weight points to average the radius value
	for(size_t i=0; i<weights_radius.size(); i++) {
		sum += weights_radius[i].weight
			* weights_radius[i].value;
		norm += weights_radius[i].weight;
	}
	if (norm != 0){
		//return the averaged value
		rad_out =  sum/norm;}
	else{
		//return normal value
		rad_out = radius();}

	return rad_out;
}
double FuzzySphereModel :: calculate_VR() {
  return 1.0;
}
