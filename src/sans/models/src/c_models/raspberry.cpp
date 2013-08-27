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
#include "raspberry.h"

// scattering
// Modified from igor model: JHC - May 04, 2012
//
// you should write your function to calculate the intensity
// for a single q-value (that's the input parameter x)
// based on the wave (array) of parameters that you send it (w)
// Ref: J. coll. inter. sci. (2010) vol. 343 (1) pp. 36-41.
//  model calculation
//
static double raspberry_func(double dp[], double q){
	// variables are:							
	//[0] volume fraction large spheres
	//[1] radius large sphere (A)
	//[2] sld large sphere (A-2)
	//[3] volume fraction small spheres
	//[4] radius small sphere (A)
	//[5] fraction of small spheres at surface
	//[6] sld small sphere
	//[7] small sphere penetration (A) 
	//[8] sld solvent
	//[9] background (cm-1)
	double vfL, rL, sldL, vfS, rS, sldS, deltaS, delrhoL, delrhoS, bkg, sldSolv, aSs;
	vfL = dp[0];
	rL = dp[1];
	sldL = dp[2];
	vfS = dp[3];
	rS = dp[4];
	aSs = dp[5];
	sldS = dp[6];
	deltaS = dp[7];
	sldSolv = dp[8];
	bkg = dp[9];
	
	delrhoL = fabs(sldL - sldSolv);
	delrhoS = fabs(sldS - sldSolv);	
	
	double VL, VS, Np, f2, fSs;
	double pi = 4.0*atan(1.0);
	  
	VL = 4*pi/3*pow(rL,3.0);
	VS = 4*pi/3*pow(rS,3.0);
	Np = aSs*4.0*pow(((rL+deltaS)/rS), 2.0);
	fSs = Np*vfL*VS/vfS/VL;
	
	double rasp_temp[8];
	rasp_temp[0] = dp[0];
	rasp_temp[1] = dp[1];
	rasp_temp[2] = delrhoL;
	rasp_temp[3] = dp[3];
	rasp_temp[4] = dp[4];
	rasp_temp[5] = dp[5];
	rasp_temp[6] = delrhoS;
	rasp_temp[7] = dp[7];

	f2 = raspberry_kernel(rasp_temp,q);
	f2+= vfS*(1.0-fSs)*pow(delrhoS, 2)*VS*rasp_bes(q,rS)*rasp_bes(q,rS);
	
	// normalize to single particle volume and convert to 1/cm
	f2 *= 1.0e8;		// [=] 1/cm
	
	return (f2+bkg);	// Scale, then add in the background
}

double raspberry_kernel(double dp[], double q){
	// variables are:							
	//[0] volume fraction large spheres
	//[1] radius large sphere (A)
	//[2] sld large sphere (A-2)
	//[3] volume fraction small spheres
	//[4] radius small sphere (A)
	//[5] fraction of small spheres at surface
	//[6] sld small sphere
	//[7] small sphere penetration (A) 

	double vfL, rL, vfS, rS, deltaS;
	double delrhoL, delrhoS, qval, aSs;
	vfL = dp[0];
	rL = dp[1];
	delrhoL = dp[2];
	vfS = dp[3];
	rS = dp[4];
	aSs = dp[5];
	delrhoS = dp[6];
	deltaS = dp[7];
			
	qval = q;		//rename the input q-value, purely for readability
	double pi = 4.0*atan(1.0);
		
	double psiL,psiS,f2;
	double sfLS,sfSS;
	double VL,VS,slT,Np,fSs;

	VL = 4.0*pi/3.0*pow(rL,3.0);
	VS = 4.0*pi/3.0*pow(rS,3.0);

	Np = aSs*4.0*(rS/(rL+deltaS))*VL/VS; 

	fSs = Np*vfL*VS/vfS/VL;

	slT = delrhoL*VL + Np*delrhoS*VS;

	psiL = rasp_bes(qval,rL);
	psiS = rasp_bes(qval,rS);

	sfLS = psiL*psiS*(sin(qval*(rL+deltaS*rS))/qval/(rL+deltaS*rS));
	sfSS = psiS*psiS*pow((sin(qval*(rL+deltaS*rS))/qval/(rL+deltaS*rS)),2);
		
	f2 = delrhoL*delrhoL*VL*VL*psiL*psiL; 
	f2 += Np*delrhoS*delrhoS*VS*VS*psiS*psiS; 
	f2 += Np*(Np-1)*delrhoS*delrhoS*VS*VS*sfSS; 
	f2 += 2*Np*delrhoL*delrhoS*VL*VS*sfLS;
	if (f2 != 0.0){
		f2 = f2/slT/slT;
	}

	f2 = f2*(vfL*delrhoL*delrhoL*VL + vfS*fSs*Np*delrhoS*delrhoS*VS);

	return f2;
}

double rasp_bes(double qval, double rad){
	double retval;
	retval = 3.0*(sin(qval*rad)-qval*rad*cos(qval*rad))/(qval*qval*qval)/(rad*rad*rad);
	return retval;
}

RaspBerryModel :: RaspBerryModel() {
	volf_Lsph = Parameter(0.05);
	radius_Lsph = Parameter(5000.0, true);
	radius_Lsph.set_min(0.0);
	sld_Lsph = Parameter(-4.0e-7);
	volf_Ssph = Parameter(0.005);
	radius_Ssph = Parameter(100.0, true);
	radius_Ssph.set_min(0.0);
	surfrac_Ssph = Parameter(0.4);
	sld_Ssph = Parameter(3.5e-6);
	delta_Ssph = Parameter(0.0);
	sld_solv   = Parameter(6.3e-6);
	background = Parameter(0.0);
}

/**
 * Function to evaluate 1D scattering function
 * The NIST IGOR is used for the actual calculation.
 * @param q: q-value
 * @return: function value
 */
double RaspBerryModel :: operator()(double q) {
	double dp[10];
	// Add the background after averaging
	dp[0] = volf_Lsph();
	dp[1] = radius_Lsph();
	dp[2] = sld_Lsph();
	dp[3] = volf_Ssph();
	dp[4] = radius_Ssph();
	dp[5] = surfrac_Ssph();
	dp[6] = sld_Ssph();
	dp[7] = delta_Ssph();
	dp[8] = sld_solv();
	dp[9] = 0.0;

	// Get the dispersion points for the radius_Lsph
	vector<WeightPoint> weights_radius_Lsph;
	radius_Lsph.get_weights(weights_radius_Lsph);

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;
	//double norm_vol = 0.0;
	//double vol = 0.0;

	// Loop over radius_Lsph weight points
	for(size_t i=0; i<weights_radius_Lsph.size(); i++) {
		dp[1] = weights_radius_Lsph[i].value;
			//Un-normalize by volume
			sum += weights_radius_Lsph[i].weight
				* raspberry_func(dp, q);// * pow(weights_radius_Lsph[i].value,3.0);
			//Find average volume 
			//vol += weights_radius_Lsph[i].weight
			//	* pow(weights_radius_Lsph[i].value,3.0);
			norm += weights_radius_Lsph[i].weight;
			//norm_vol += weights_radius_Lsph[i].weight;
		}
	
	//if (vol != 0.0 && norm_vol != 0.0) {
		//Re-normalize by avg volume
		//sum = sum/(vol/norm_vol);}
	return sum/norm + background();
}

/**
 * Function to evaluate 2D scattering function
 * @param q_x: value of Q along x
 * @param q_y: value of Q along y
 * @return: function value
 */
double RaspBerryModel :: operator()(double qx, double qy) {
	double q = sqrt(qx*qx + qy*qy);
	return (*this).operator()(q);
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters 
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double RaspBerryModel :: evaluate_rphi(double q, double phi) {
	return (*this).operator()(q);
}

/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double RaspBerryModel :: calculate_ER() {
  //NOT implemented yet!!!
  return 0.0;
}
double RaspBerryModel :: calculate_VR() {
  return 1.0;
}
