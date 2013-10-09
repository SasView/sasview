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

extern "C" {
	#include "libCylinder.h"
  #include "GaussWeights.h"
	#include "barbell.h"
}

BarBellModel :: BarBellModel() {
	scale      = Parameter(1.0);
	rad_bar		= Parameter(20.0);
	rad_bar.set_min(0.0);
	len_bar     = Parameter(400.0, true);
	len_bar.set_min(0.0);
	rad_bell = Parameter(40.0);
	rad_bell.set_min(0.0);
	sld_barbell   = Parameter(1.0e-6);
	sld_solv   = Parameter(6.3e-6);
	background = Parameter(0.0);
	theta  = Parameter(0.0, true);
	phi    = Parameter(0.0, true);
}

double bar2d_kernel(double dp[], double q, double alpha) {
  int j;
  double Pi;
  double scale,contr,bkg,sldc,slds;
  double len,rad,hDist,endRad;
  int nordj=76;
  double zi=alpha,yyy,answer;     //running tally of integration
  double summj,vaj,vbj,zij;     //for the inner integration
  double arg1,arg2,inner,be;


  scale = dp[0];
  rad = dp[1];
  len = dp[2];
  endRad = dp[3];
  sldc = dp[4];
  slds = dp[5];
  bkg = dp[6];

  hDist = sqrt(fabs(endRad*endRad-rad*rad));    //by definition for this model

  contr = sldc-slds;

  Pi = 4.0*atan(1.0);
  vaj = -1.0*hDist/endRad;
  vbj = 1.0;    //endpoints of inner integral

  summj=0.0;

  for(j=0;j<nordj;j++) {
    //20 gauss points for the inner integral
    zij = ( Gauss76Z[j]*(vbj-vaj) + vaj + vbj )/2.0;    //the "t" dummy
    yyy = Gauss76Wt[j] * Dumb_kernel(dp,q,zij,zi);    //uses the same Kernel as the Dumbbell, here L>0
    summj += yyy;
  }
  //now calculate the value of the inner integral
  inner = (vbj-vaj)/2.0*summj;
  inner *= 4.0*Pi*endRad*endRad*endRad;

  //now calculate outer integrand
  arg1 = q*len/2.0*cos(zi);
  arg2 = q*rad*sin(zi);
  yyy = inner;

  if(arg2 == 0) {
    be = 0.5;
  } else {
    be = NR_BessJ1(arg2)/arg2;
  }

  if(arg1 == 0.0) {   //limiting value of sinc(0) is 1; sinc is not defined in math.h
    yyy += Pi*rad*rad*len*2.0*be;
  } else {
    yyy += Pi*rad*rad*len*sin(arg1)/arg1*2.0*be;
  }
  yyy *= yyy;   //sin(zi);
  answer = yyy;


  answer /= Pi*rad*rad*len + 2.0*Pi*(2.0*endRad*endRad*endRad/3.0+endRad*endRad*hDist-hDist*hDist*hDist/3.0);   //divide by volume
  answer *= 1.0e8;    //convert to cm^-1
  answer *= contr*contr;
  answer *= scale;
  answer += bkg;

  return answer;
}
/**
 * Function to evaluate 1D scattering function
 * The NIST IGOR library is used for the actual calculation.
 * @param q: q-value
 * @return: function value
 */
double BarBellModel :: operator()(double q) {
	double dp[7];

	// Fill parameter array for IGOR library
	// Add the background after averaging
	dp[0] = scale();
	dp[1] = rad_bar();
	dp[2] = len_bar();
	dp[3] = rad_bell();
	dp[4] = sld_barbell();
	dp[5] = sld_solv();
	dp[6] = 0.0;

	// Get the dispersion points for the rad_bar
	vector<WeightPoint> weights_rad_bar;
	rad_bar.get_weights(weights_rad_bar);
	// Get the dispersion points for the len_bar
	vector<WeightPoint> weights_len_bar;
	len_bar.get_weights(weights_len_bar);
	// Get the dispersion points for the rad_bell
	vector<WeightPoint> weights_rad_bell;
	rad_bell.get_weights(weights_rad_bell);

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;
	double vol = 0.0;
	double pi,hDist,result;
	double vol_i = 0.0;
	pi = 4.0*atan(1.0);
	// Loop over radius weight points
	for(size_t i=0; i<weights_rad_bar.size(); i++) {
		dp[1] = weights_rad_bar[i].value;
		for(size_t j=0; j<weights_len_bar.size(); j++) {
			dp[2] = weights_len_bar[j].value;
			for(size_t k=0; k<weights_rad_bell.size(); k++) {
				dp[3] = weights_rad_bell[k].value;

				//Un-normalize SphereForm by volume
				hDist = sqrt(fabs(dp[3]*dp[3]-dp[1]*dp[1]));
				vol_i = pi*dp[1]*dp[1]*dp[2]+2.0*pi*(2.0*dp[3]*dp[3]*dp[3]/3.0
								+dp[3]*dp[3]*hDist-hDist*hDist*hDist/3.0);
				result =  Barbell(dp, q) * vol_i;
				// This FIXES a singualrity the kernel in libigor.
				if ( result == INFINITY || result == NAN){
					result = 0.0;
				}
				sum += weights_rad_bar[i].weight*weights_len_bar[j].weight*weights_rad_bell[k].weight
					* result;
				//Find average volume
				vol += weights_rad_bar[i].weight*weights_len_bar[j].weight*weights_rad_bell[k].weight
					* vol_i;

				norm += weights_rad_bar[i].weight*weights_len_bar[j].weight*weights_rad_bell[k].weight;
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
double BarBellModel :: operator()(double qx, double qy) {
  double dp[7];

  // Fill parameter array for IGOR library
  // Add the background after averaging
  dp[0] = scale();
  dp[1] = rad_bar();
  dp[2] = len_bar();
  dp[3] = rad_bell();
  dp[4] = sld_barbell();
  dp[5] = sld_solv();
  dp[6] = 0.0;

  double _theta = theta();
  double _phi = phi();

	// Get the dispersion points for the rad_bar
	vector<WeightPoint> weights_rad_bar;
	rad_bar.get_weights(weights_rad_bar);

	// Get the dispersion points for the len_bar
	vector<WeightPoint> weights_len_bar;
	len_bar.get_weights(weights_len_bar);

	// Get the dispersion points for the rad_bell
	vector<WeightPoint> weights_rad_bell;
	rad_bell.get_weights(weights_rad_bell);

	// Get angular averaging for theta
	vector<WeightPoint> weights_theta;
	theta.get_weights(weights_theta);

	// Get angular averaging for phi
	vector<WeightPoint> weights_phi;
	phi.get_weights(weights_phi);


	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;
	double norm_vol = 0.0;
	double vol = 0.0;
	double pi,hDist;
	double vol_i = 0.0;
	pi = 4.0*atan(1.0);

	// Loop over radius weight points
	for(size_t i=0; i<weights_rad_bar.size(); i++) {
		dp[1] = weights_rad_bar[i].value;
		for(size_t j=0; j<weights_len_bar.size(); j++) {
			dp[2] = weights_len_bar[j].value;
			for(size_t k=0; k<weights_rad_bell.size(); k++) {
				dp[3] = weights_rad_bell[k].value;
				// Average over theta distribution
				for(size_t l=0; l< weights_theta.size(); l++) {
					_theta = weights_theta[l].value;
					// Average over phi distribution
					for(size_t m=0; m< weights_phi.size(); m++) {
						_phi = weights_phi[m].value;
						//Un-normalize Form by volume
						hDist = sqrt(fabs(dp[3]*dp[3]-dp[1]*dp[1]));
						vol_i = pi*dp[1]*dp[1]*dp[2]+2.0*pi*(2.0*dp[3]*dp[3]*dp[3]/3.0
										+dp[3]*dp[3]*hDist-hDist*hDist*hDist/3.0);

					  const double q = sqrt(qx*qx+qy*qy);
					  //convert angle degree to radian
					  const double pi = 4.0*atan(1.0);

					  // Cylinder orientation
				    const double cyl_x = cos(_theta * pi/180.0) * cos(_phi * pi/180.0);
				    const double cyl_y = sin(_theta * pi/180.0);

				    // Compute the angle btw vector q and the
				    // axis of the cylinder (assume qz = 0)
				    const double cos_val = cyl_x*qx + cyl_y*qy;

				    // The following test should always pass
				    if (fabs(cos_val)>1.0) {
				      return 0;
				    }

				    // Note: cos(alpha) = 0 and 1 will get an
				    // undefined value from CylKernel
				    const double alpha = acos( cos_val );

            // Call the IGOR library function to get the kernel
            const double output = bar2d_kernel(dp, q, alpha)/sin(alpha);

						double _ptvalue = weights_rad_bar[i].weight
											* weights_len_bar[j].weight
											* weights_rad_bell[k].weight
											* weights_theta[l].weight
											* weights_phi[m].weight
											* vol_i
											* output;
											//* pow(weights_rad[i].value,3.0);

						// Consider when there is infinte or nan.
						if ( _ptvalue == INFINITY || _ptvalue == NAN){
							_ptvalue = 0.0;
						}
						if (weights_theta.size()>1) {
							_ptvalue *= fabs(cos(weights_theta[l].value*pi/180.0));
						}
						sum += _ptvalue;
						// This model dose not need the volume of spheres correction!!!
						//Find average volume
						vol += weights_rad_bar[i].weight
								* weights_len_bar[j].weight
								* weights_rad_bell[k].weight
								* vol_i;
						//Find norm for volume
						norm_vol += weights_rad_bar[i].weight
								* weights_len_bar[j].weight
								* weights_rad_bell[k].weight;

						norm += weights_rad_bar[i].weight
								* weights_len_bar[j].weight
								* weights_rad_bell[k].weight
								* weights_theta[l].weight
								* weights_phi[m].weight;
					}
				}
			}
		}
	}
	// Averaging in theta needs an extra normalization
	// factor to account for the sin(theta) term in the
	// integration (see documentation).
	if (weights_theta.size()>1) norm = norm / asin(1.0);

	if (vol != 0.0 && norm_vol != 0.0) {
		//Re-normalize by avg volume
		sum = sum/(vol/norm_vol);}

	return sum/norm + background();
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the SCCrystal
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double BarBellModel :: evaluate_rphi(double q, double phi) {
	return (*this).operator()(q);
}

/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double BarBellModel :: calculate_ER() {
	//NOT implemented yet!!!
	return 0.0;
}
/**
 * Function to calculate volf_ratio for shell/tot
 * @return: volf_ratio value
 */
double BarBellModel :: calculate_VR() {
  return 1.0;
}
