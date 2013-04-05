/**
 * PringlesModel
 *
 * (c) 2013 / Andrew J Jackson / andrew.jackson@esss.se
 *
 * Model for "pringles" particle from K. Edler @ Bath University
 *
 */
#include <math.h>
#include "parameters.hh"
#include "pringles.h"
#include "cephes.h"
using namespace std;

extern "C"
{
#include "GaussWeights.h"
#include "libStructureFactor.h"
}

// Convenience parameter structure
typedef struct {
    double scale;
    double radius;
    double thickness;
    double alpha;
    double beta;
    double sldCyl;
    double sldSolv;
    double background;
    double cyl_theta;
    double cyl_phi;
} PringleParameters;


PringlesModel::PringlesModel() {
	scale = Parameter(1.0);
	radius = Parameter(60.0,true);
	radius.set_min(0.0);
	thickness = Parameter(10.0,true);
	thickness.set_min(0.0);
	alpha = Parameter(0.001,true);
	beta = Parameter(0.02,true);
	sld_pringle = Parameter(1.0e-6);
	sld_solvent = Parameter(6.35e-6);
	background = Parameter(0.0);
}

/**
 * Function to evaluate 1D scattering function
 * @param q: q-value
 * @return: function value
 */
double PringlesModel::operator()(double q) {
	double dp[8];
	// Fill parameter array
	// Add the background after averaging
	dp[0] = scale();
	dp[1] = radius();
	dp[2] = thickness();
	dp[3] = alpha();
	dp[4] = beta();
	dp[5] = sld_pringle();
	dp[6] = sld_solvent();
	dp[7] = 0.0;

	// Get the dispersion points for the radius
	vector<WeightPoint> weights_rad;
	radius.get_weights(weights_rad);

	// Get the dispersion points for the thickness
	vector<WeightPoint> weights_thick;
	thickness.get_weights(weights_thick);

	// Get the dispersion points for alpha
	vector<WeightPoint> weights_alpha;
	alpha.get_weights(weights_alpha);

	// Get the dispersion points for beta
	vector<WeightPoint> weights_beta;
	beta.get_weights(weights_beta);

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;
	double volnorm = 0.0;
	double vol = 0.0;
	double Pi;

	Pi = 4.0 * atan(1.0);

	// Loop over alpha weight points
	for (size_t i = 0; i < weights_alpha.size(); i++) {
		dp[3] = weights_alpha[i].value;

		//Loop over beta weight points
		for (size_t j = 0; j < weights_beta.size(); j++) {
			dp[4] = weights_beta[j].value;

			// Loop over thickness weight points
			for (size_t k = 0; k < weights_thick.size(); k++) {
				dp[2] = weights_thick[k].value;

				// Loop over radius weight points
				for (size_t l = 0; l < weights_rad.size(); l++) {
					dp[1] = weights_rad[l].value;
					sum += weights_rad[l].weight * weights_thick[k].weight
							* weights_alpha[i].weight * weights_beta[j].weight
							* pringle_form(dp, q);
					//Find average volume
					vol += weights_rad[l].weight * weights_thick[k].weight * Pi * pow(weights_rad[l].value, 2) * weights_thick[k].value;
					volnorm += weights_rad[l].weight * weights_thick[k].weight;
					norm +=  weights_rad[l].weight * weights_thick[k].weight * weights_alpha[i].weight * weights_beta[j].weight;

				}
			}
		}
	}

	if (vol > 0.0 && norm > 0.0) {
		//normalize by avg volume
		sum = sum * (vol/volnorm);
		return sum/norm + background();
	} else {
		return 0.0;
	}
}

/**
 * Function to evaluate 2D scattering function
 * @param q_x: value of Q along x
 * @param q_y: value of Q along y
 * @return: function value
 */
double PringlesModel::operator()(double qx, double qy) {
	double q = sqrt(qx * qx + qy * qy);
	return (*this).operator()(q);
}
/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the model
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double PringlesModel::evaluate_rphi(double q, double phi) {
	return (*this).operator()(q);
}

/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double PringlesModel::calculate_ER() {
	PringleParameters dp;

	dp.radius     = radius();
	dp.thickness  = thickness();
	double rad_out = 0.0;

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;

	// Get the dispersion points for the major shell
	vector<WeightPoint> weights_thick;
	thickness.get_weights(weights_thick);

	// Get the dispersion points for the minor shell
	vector<WeightPoint> weights_radius ;
	radius.get_weights(weights_radius);

	// Loop over major shell weight points
	for(int i=0; i< (int)weights_thick.size(); i++) {
		dp.thickness = weights_thick[i].value;
		for(int k=0; k< (int)weights_radius.size(); k++) {
			dp.radius = weights_radius[k].value;
			//Note: output of "DiamCyl(dp.thick,dp.radius)" is DIAMETER.
			sum +=weights_thick[i].weight
				* weights_radius[k].weight*DiamCyl(dp.thickness,dp.radius)/2.0;
			norm += weights_thick[i].weight* weights_radius[k].weight;
		}
	}
	if (norm != 0){
		//return the averaged value
		rad_out =  sum/norm;}
	else{
		//return normal value
		//Note: output of "DiamCyl(dp.length,dp.radius)" is DIAMETER.
		rad_out = DiamCyl(dp.thickness,dp.radius)/2.0;}

	return rad_out;
}
/**
 * Function to calculate particle volume/total volume for shape models:
 *    Most case returns 1 but for example for the vesicle model it is
 *    (total volume - core volume)/total volume
 *    (< 1 depending on the thickness).
 * @return: effective radius value
 */
double PringlesModel::calculate_VR() {
	return 1.0;
}

/*
 * Useful work functions start here!
 *
 */

static double pringle_form(double dp[], double q) {

	double Pi;
	int nord = 76, i=0;			//order of integration
	double uplim, lolim;		//upper and lower integration limits
	double summ, phi, yyy, answer, vcyl;			//running tally of integration
	double delrho;

	Pi = 4.0 * atan(1.0);
	lolim = 0.0;
	uplim = Pi / 2.0;

	summ = 0.0;			//initialize integral

	delrho = dp[5] - dp[6] ; //make contrast term

	for (i = 0; i < nord; i++) {
		phi = (Gauss76Z[i] * (uplim - lolim) + uplim + lolim) / 2.0;
		yyy = Gauss76Wt[i] * pringle_kernel(dp, q, phi);
		summ += yyy;
	}

	answer = (uplim - lolim) / 2.0 * summ;

	answer *= delrho*delrho;

    //normalize by cylinder volume
	//vcyl=Pi*dp[1]*dp[1]*dp[2];
	//answer *= vcyl;

    //convert to [cm-1]
	answer *= 1.0e8;

    //Scale by volume fraction
	answer *= dp[0];

	return answer;
}

static double pringle_kernel(double dp[], double q, double phi) {

	double sumterm, sincarg, sincterm, nn, retval;

	sincarg = q * dp[2] * cos(phi) / 2.0; //dp[2] = thickness
	sincterm = pow(sin(sincarg) / sincarg, 2.0);

	//calculate sum term from n = -3 to 3
	sumterm = 0;
	for (nn = -3; nn <= 3; nn = nn + 1) {
		sumterm = sumterm
				+ (pow(pringleC(dp, q, phi, nn), 2.0)
						+ pow(pringleS(dp, q, phi, nn), 2.0));
	}

	retval = 4.0 * sin(phi) * sumterm * sincterm;

	return retval;

}

static double pringleC(double dp[], double q, double phi, double n) {

	double nord, va, vb, summ;
	double bessargs, cosarg, bessargcb;
	double r, retval, yyy;
	int ii;
	// set up the integration
	// end points and weights
	nord = 76;
	va = 0;
	vb = dp[1]; //radius

	// evaluate at Gauss points
	// remember to index from 0,size-1

	summ = 0.0;		// initialize integral
	ii = 0;
	do {
		// Using 76 Gauss points
		r = (Gauss76Z[ii] * (vb - va) + vb + va) / 2.0;

		bessargs = q * r * sin(phi);
		cosarg = q * r * r * dp[3] * cos(phi);
		bessargcb = q * r * r * dp[4] * cos(phi);

		yyy = Gauss76Wt[ii] * r * cos(cosarg) * jn(n, bessargcb)
				* jn(2 * n, bessargs);
		summ += yyy;

		ii += 1;
	} while (ii < nord);			// end of loop over quadrature points
	//
	// calculate value of integral to return

	retval = (vb - va) / 2.0 * summ;

	retval = retval / pow(r, 2.0);

	return retval;
}

static double pringleS(double dp[], double q, double phi, double n) {

	double nord, va, vb, summ;
	double bessargs, sinarg, bessargcb;
	double r, retval, yyy;
	int ii;
	// set up the integration
	// end points and weights
	nord = 76;
	va = 0;
	vb = dp[1]; //radius

	// evaluate at Gauss points
	// remember to index from 0,size-1

	summ = 0.0;		// initialize integral
	ii = 0;
	do {
		// Using 76 Gauss points
		r = (Gauss76Z[ii] * (vb - va) + vb + va) / 2.0;

		bessargs = q * r * sin(phi);
		sinarg = q * r * r * dp[3] * cos(phi);
		bessargcb = q * r * r * dp[4] * cos(phi);

		yyy = Gauss76Wt[ii] * r * sin(sinarg) * jn(n, bessargcb)
				* jn(2 * n, bessargs);

		summ += yyy;

		ii += 1;
	} while (ii < nord);			// end of loop over quadrature points
	//
	// calculate value of integral to return

	retval = (vb - va) / 2.0 * summ;

	retval = retval / pow(r, 2.0);

	return retval;
}
