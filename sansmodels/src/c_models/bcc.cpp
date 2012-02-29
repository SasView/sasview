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
#include "bcc.h"

extern "C" {
	#include "libSphere.h"
}

// Convenience structure
typedef struct {
  double scale;
  double dnn;
  double d_factor;
  double radius;
  double sldSph;
  double sldSolv;
  double background;
  double theta;
  double phi;
  double psi;

} BCParameters;

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the BCCCrystalModel
 * @param q: q-value
 * @param q_x: q_x / q
 * @param q_y: q_y / q
 * @return: function value
 */
static double bc_analytical_2D_scaled(BCParameters *pars, double q, double q_x, double q_y) {
  double b3_x, b3_y, b3_z, b1_x, b1_y;
  double q_z;
  double alpha, cos_val_b3, cos_val_b2, cos_val_b1;
  double a1_dot_q, a2_dot_q,a3_dot_q;
  double answer;
  double Pi = 4.0*atan(1.0);
  double aa, Da, qDa_2, latticeScale, Zq, Fkq, Fkq_2;

  //convert angle degree to radian
  double pi = 4.0*atan(1.0);
  double theta = pars->theta * pi/180.0;
  double phi = pars->phi * pi/180.0;
  double psi = pars->psi * pi/180.0;

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
    b3_x = sin(theta) * cos(phi);//negative sign here???
    b3_y = sin(theta) * sin(phi);
    b3_z = cos(theta);
    cos_val_b3 =  b3_x*q_x + b3_y*q_y + b3_z*q_z;

    alpha = acos(cos_val_b3);
    // b1 axis orientation
    b1_x = sin(psi);
    b1_y = cos(psi);
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

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the BCC_ParaCrystal
 * @param q: q-value
 * @return: function value
 */
static double bc_analytical_2DXY(BCParameters *pars, double qx, double qy){
  double q;
  q = sqrt(qx*qx+qy*qy);
  return bc_analytical_2D_scaled(pars, q, qx/q, qy/q);
}

BCCrystalModel :: BCCrystalModel() {
	scale      = Parameter(1.0);
	dnn		= Parameter(220.0);
	d_factor = Parameter(0.06);
	radius     = Parameter(40.0, true);
	radius.set_min(0.0);
	sldSph   = Parameter(3.0e-6);
	sldSolv   = Parameter(6.3e-6);
	background = Parameter(0.0);
	theta  = Parameter(0.0, true);
	phi    = Parameter(0.0, true);
	psi    = Parameter(0.0, true);
}

/**
 * Function to evaluate 1D scattering function
 * The NIST IGOR library is used for the actual calculation.
 * @param q: q-value
 * @return: function value
 */
double BCCrystalModel :: operator()(double q) {
	double dp[7];

	// Fill parameter array for IGOR library
	// Add the background after averaging
	dp[0] = scale();
	dp[1] = dnn();
	dp[2] = d_factor();
	dp[3] = radius();
	dp[4] = sldSph();
	dp[5] = sldSolv();
	dp[6] = 0.0;

	// Get the dispersion points for the radius
	vector<WeightPoint> weights_rad;
	radius.get_weights(weights_rad);

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;
	double vol = 0.0;
	double result;

	// Loop over radius weight points
	for(size_t i=0; i<weights_rad.size(); i++) {
		dp[3] = weights_rad[i].value;

		//Un-normalize SphereForm by volume
		result = BCC_ParaCrystal(dp, q) * pow(weights_rad[i].value,3);
		// This FIXES a singualrity in the kernel in libigor.
		if ( result == INFINITY || result == NAN){
			result = 0.0;
		}
		sum += weights_rad[i].weight
			* result;
		//Find average volume
		vol += weights_rad[i].weight
			* pow(weights_rad[i].value,3);

		norm += weights_rad[i].weight;
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
double BCCrystalModel :: operator()(double qx, double qy) {
	BCParameters dp;
	dp.scale      = scale();
	dp.dnn   = dnn();
	dp.d_factor   = d_factor();
	dp.radius  = radius();
	dp.sldSph   = sldSph();
	dp.sldSolv   = sldSolv();
	dp.background = 0.0;
	dp.theta  = theta();
	dp.phi    = phi();
	dp.psi    = psi();
	double pi = 4.0*atan(1.0);
	// Get the dispersion points for the radius
	vector<WeightPoint> weights_rad;
	radius.get_weights(weights_rad);

	// Get angular averaging for theta
	vector<WeightPoint> weights_theta;
	theta.get_weights(weights_theta);

	// Get angular averaging for phi
	vector<WeightPoint> weights_phi;
	phi.get_weights(weights_phi);

	// Get angular averaging for psi
	vector<WeightPoint> weights_psi;
	psi.get_weights(weights_psi);

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;
	double norm_vol = 0.0;
	double vol = 0.0;

	// Loop over radius weight points
	for(size_t i=0; i<weights_rad.size(); i++) {
		dp.radius = weights_rad[i].value;
		// Average over theta distribution
		for(size_t j=0; j< weights_theta.size(); j++) {
			dp.theta = weights_theta[j].value;
			// Average over phi distribution
			for(size_t k=0; k< weights_phi.size(); k++) {
				dp.phi = weights_phi[k].value;
				// Average over phi distribution
				for(size_t l=0; l< weights_psi.size(); l++) {
					dp.psi = weights_psi[l].value;
					//Un-normalize SphereForm by volume
					double _ptvalue = weights_rad[i].weight
										* weights_theta[j].weight
										* weights_phi[k].weight
										* weights_psi[l].weight
										* bc_analytical_2DXY(&dp, qx, qy);
										//* pow(weights_rad[i].value,3.0);
					// Consider when there is infinity or nan.
					// Actual value for this singular point are typically zero.
					if ( _ptvalue == INFINITY || _ptvalue == NAN){
						_ptvalue = 0.0;
					}
					if (weights_theta.size()>1) {
						_ptvalue *= fabs(sin(weights_theta[j].value*pi/180.0));
					}
					sum += _ptvalue;
					// This model dose not need the volume of spheres correction!!!
					norm += weights_rad[i].weight
							* weights_theta[j].weight
							* weights_phi[k].weight
							* weights_psi[l].weight;
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
 * @param pars: parameters of the BCCCrystal
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double BCCrystalModel :: evaluate_rphi(double q, double phi) {
	return (*this).operator()(q);
}

/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double BCCrystalModel :: calculate_ER() {
	//NOT implemented yet!!!
	return 0.0;
}
double BCCrystalModel :: calculate_VR() {
  return 1.0;
}
