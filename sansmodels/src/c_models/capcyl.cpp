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
  #include "GaussWeights.h"
	#include "libCylinder.h"
}
#include "capcyl.h"

// Convenience parameter structure
typedef struct {
    double scale;
    double rad_cyl;
    double len_cyl;
    double rad_cap;
    double sld_capcyl;
    double sld_solv;
    double background;
    double theta;
    double phi;
} CapCylParameters;

CappedCylinderModel :: CappedCylinderModel() {
	scale      = Parameter(1.0);
	rad_cyl		= Parameter(20.0);
	rad_cyl.set_min(0.0);
	len_cyl     = Parameter(400.0, true);
	len_cyl.set_min(0.0);
	rad_cap = Parameter(40.0);
	rad_cap.set_min(0.0);
	sld_capcyl  = Parameter(1.0e-6);
	sld_solv   = Parameter(6.3e-6);
	background = Parameter(0.0);
	theta  = Parameter(0.0, true);
	phi    = Parameter(0.0, true);
}

static double capcyl2d_kernel(double dp[], double q, double alpha) {
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

  hDist = -1.0*sqrt(fabs(endRad*endRad-rad*rad));   //by definition for this model

  contr = sldc-slds;

  Pi = 4.0*atan(1.0);
  vaj = -1.0*hDist/endRad;
  vbj = 1.0;    //endpoints of inner integral

  summj=0.0;

  for(j=0;j<nordj;j++) {
    //20 gauss points for the inner integral
    zij = ( Gauss76Z[j]*(vbj-vaj) + vaj + vbj )/2.0;    //the "t" dummy
    yyy = Gauss76Wt[j] * ConvLens_kernel(dp,q,zij,zi);    //uses the same Kernel as the Dumbbell, here L>0
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
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the BarBell
 * @param q: q-value
 * @param q_x: q_x / q
 * @param q_y: q_y / q
 * @return: function value
 */
static double capcyl_analytical_2D_scaled(CapCylParameters *pars, double q, double q_x, double q_y) {
  double cyl_x, cyl_y;//, cyl_z;
  //double q_z;
  double alpha, cos_val;
  double answer;
  double dp[7];
  //convert angle degree to radian
  double pi = 4.0*atan(1.0);
  double theta = pars->theta * pi/180.0;
  double phi = pars->phi * pi/180.0;

  dp[0] = pars->scale;
  dp[1] = pars->rad_cyl;
  dp[2] = pars->len_cyl;
  dp[3] = pars->rad_cap;
  dp[4] = pars->sld_capcyl;
  dp[5] = pars->sld_solv;
  dp[6] = pars->background;


  //double Pi = 4.0*atan(1.0);
    // Cylinder orientation
    cyl_x = cos(theta) * cos(phi);
    cyl_y = sin(theta);
    //cyl_z = -cos(theta) * sin(phi);

    // q vector
    //q_z = 0;

    // Compute the angle btw vector q and the
    // axis of the cylinder
    cos_val = cyl_x*q_x + cyl_y*q_y;// + cyl_z*q_z;

    // The following test should always pass
    if (fabs(cos_val)>1.0) {
      printf("cyl_ana_2D: Unexpected error: cos(alpha)>1\n");
      return 0;
    }

    // Note: cos(alpha) = 0 and 1 will get an
    // undefined value from CylKernel
  alpha = acos( cos_val );

  // Call the IGOR library function to get the kernel
  answer = capcyl2d_kernel(dp, q, alpha)/sin(alpha);


  return answer;

}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the BarBell
 * @param q: q-value
 * @return: function value
 */
static double capcyl_analytical_2DXY(CapCylParameters *pars, double qx, double qy){
  double q;
  q = sqrt(qx*qx+qy*qy);
  return capcyl_analytical_2D_scaled(pars, q, qx/q, qy/q);
}

/**
 * Function to evaluate 1D scattering function
 * The NIST IGOR library is used for the actual calculation.
 * @param q: q-value
 * @return: function value
 */
double CappedCylinderModel :: operator()(double q) {
	double dp[7];

	// Fill parameter array for IGOR library
	// Add the background after averaging
	dp[0] = scale();
	dp[1] = rad_cyl();
	dp[2] = len_cyl();
	dp[3] = rad_cap();
	dp[4] = sld_capcyl();
	dp[5] = sld_solv();
	dp[6] = 0.0;

	// Get the dispersion points for the rad_cyl
	vector<WeightPoint> weights_rad_cyl;
	rad_cyl.get_weights(weights_rad_cyl);
	// Get the dispersion points for the len_cyl
	vector<WeightPoint> weights_len_cyl;
	len_cyl.get_weights(weights_len_cyl);
	// Get the dispersion points for the rad_cap
	vector<WeightPoint> weights_rad_cap;
	rad_cap.get_weights(weights_rad_cap);

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;
	double vol = 0.0;
	double pi,hDist,result;
	double vol_i = 0.0;
	pi = 4.0*atan(1.0);
	// Loop over radius weight points
	for(size_t i=0; i<weights_rad_cyl.size(); i++) {
		dp[1] = weights_rad_cyl[i].value;
		for(size_t j=0; j<weights_len_cyl.size(); j++) {
			dp[2] = weights_len_cyl[j].value;
			for(size_t k=0; k<weights_rad_cap.size(); k++) {
				dp[3] = weights_rad_cap[k].value;

				//Un-normalize SphereForm by volume
				hDist = -1.0*sqrt(fabs(dp[3]*dp[3]-dp[1]*dp[1]));
				vol_i = pi*dp[1]*dp[1]*dp[2]+2.0*pi/3.0*((dp[3]-hDist)*(dp[3]-hDist)*
								(2.0*(dp[3]+hDist)));
				result =  CappedCylinder(dp, q) * vol_i;
				// This FIXES a singualrity the kernel in libigor.
				if ( result == INFINITY || result == NAN){
					result = 0.0;
				}
				sum += weights_rad_cyl[i].weight*weights_len_cyl[j].weight*weights_rad_cap[k].weight
					* result;
				//Find average volume
				vol += weights_rad_cyl[i].weight*weights_len_cyl[j].weight*weights_rad_cap[k].weight
					* vol_i;

				norm += weights_rad_cyl[i].weight*weights_len_cyl[j].weight*weights_rad_cap[k].weight;
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
double CappedCylinderModel :: operator()(double qx, double qy) {
	CapCylParameters dp;

	dp.scale = scale();
	dp.rad_cyl = rad_cyl();
	dp.len_cyl = len_cyl();
	dp.rad_cap = rad_cap();
	dp.sld_capcyl = sld_capcyl();
	dp.sld_solv = sld_solv();
	dp.background = 0.0;
	dp.theta  = theta();
	dp.phi    = phi();

	// Get the dispersion points for the rad_bar
	vector<WeightPoint> weights_rad_cyl;
	rad_cyl.get_weights(weights_rad_cyl);

	// Get the dispersion points for the len_bar
	vector<WeightPoint> weights_len_cyl;
	len_cyl.get_weights(weights_len_cyl);

	// Get the dispersion points for the rad_bell
	vector<WeightPoint> weights_rad_cap;
	rad_cap.get_weights(weights_rad_cap);

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
	for(size_t i=0; i<weights_rad_cyl.size(); i++) {
		dp.rad_cyl = weights_rad_cyl[i].value;
		for(size_t j=0; j<weights_len_cyl.size(); j++) {
			dp.len_cyl = weights_len_cyl[j].value;
			for(size_t k=0; k<weights_rad_cap.size(); k++) {
				dp.rad_cap = weights_rad_cap[k].value;
				// Average over theta distribution
				for(size_t l=0; l< weights_theta.size(); l++) {
					dp.theta = weights_theta[l].value;
					// Average over phi distribution
					for(size_t m=0; m< weights_phi.size(); m++) {
						dp.phi = weights_phi[m].value;
						//Un-normalize Form by volume
						hDist = -1.0*sqrt(fabs(dp.rad_cap*dp.rad_cap-dp.rad_cyl*dp.rad_cyl));
						vol_i = pi*dp.rad_cyl*dp.rad_cyl*dp.len_cyl+2.0*pi/3.0*((dp.rad_cap-hDist)*(dp.rad_cap-hDist)*
										(2*dp.rad_cap+hDist));

						double _ptvalue = weights_rad_cyl[i].weight
											* weights_len_cyl[j].weight
											* weights_rad_cap[k].weight
											* weights_theta[l].weight
											* weights_phi[m].weight
											* vol_i
											* capcyl_analytical_2DXY(&dp, qx, qy);
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
						vol += weights_rad_cyl[i].weight
								* weights_len_cyl[j].weight
								* weights_rad_cap[k].weight
								* vol_i;
						//Find norm for volume
						norm_vol += weights_rad_cyl[i].weight
								* weights_len_cyl[j].weight
								* weights_rad_cap[k].weight;

						norm += weights_rad_cyl[i].weight
								* weights_len_cyl[j].weight
								* weights_rad_cap[k].weight
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
double CappedCylinderModel :: evaluate_rphi(double q, double phi) {
	return (*this).operator()(q);
}

/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double CappedCylinderModel :: calculate_ER() {
	//NOT implemented yet!!!
	return 0.0;
}
double CappedCylinderModel :: calculate_VR() {
  return 1.0;
}
