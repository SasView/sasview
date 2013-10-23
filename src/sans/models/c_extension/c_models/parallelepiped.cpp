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
 *	TODO: add 2D function
 */

#include <math.h>
#include "parameters.hh"
#include <stdio.h>
using namespace std;

extern "C" {
	#include "libCylinder.h"
	#include "libStructureFactor.h"
	#include "libmultifunc/libfunc.h"
}
#include "parallelepiped.h"

// Convenience parameter structure
typedef struct {
    double scale;
    double short_a;
    double short_b;
    double long_c;
    double sldPipe;
    double sldSolv;
    double background;
    double parallel_theta;
    double parallel_phi;
    double parallel_psi;
    double M0_sld_pipe;
    double M_theta_pipe;
    double M_phi_pipe;
    double M0_sld_solv;
    double M_theta_solv;
    double M_phi_solv;
    double Up_frac_i;
	double Up_frac_f;
	double Up_theta;
} ParallelepipedParameters;


static double pkernel(double a, double b,double c, double ala, double alb, double alc){
    // mu passed in is really mu*sqrt(1-sig^2)
    double argA,argB,argC,tmp1,tmp2,tmp3;     //local variables

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

}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the parallelepiped
 * @param q: q-value
 * @param q_x: q_x / q
 * @param q_y: q_y / q
 * @return: function value
 */
static double parallelepiped_analytical_2D_scaled(ParallelepipedParameters *pars, double q, double q_x, double q_y) {
  double cparallel_x, cparallel_y, bparallel_x, bparallel_y, parallel_x, parallel_y;
  //double q_z;
  double vol, cos_val_c, cos_val_b, cos_val_a, edgeA, edgeB, edgeC;

  double answer = 0.0;
  double form = 0.0;
  double pi = 4.0*atan(1.0);
  
  //convert angle degree to radian
  double theta = pars->parallel_theta * pi/180.0;
  double phi = pars->parallel_phi * pi/180.0;
  double psi = pars->parallel_psi * pi/180.0;
  double sld_solv = pars->sldSolv;
  double sld_pipe = pars->sldPipe;
  double m_max = pars->M0_sld_pipe;
  double m_max_solv = pars->M0_sld_solv;
  double contrast = 0.0;
    
  edgeA = pars->short_a;
  edgeB = pars->short_b;
  edgeC = pars->long_c;


    // parallelepiped c axis orientation
    cparallel_x = cos(theta) * cos(phi);
    cparallel_y = sin(theta);
    //cparallel_z = -cos(theta) * sin(phi);

    // q vector
    //q_z = 0.0;

    // Compute the angle btw vector q and the
    // axis of the parallelepiped
    cos_val_c = cparallel_x*q_x + cparallel_y*q_y;// + cparallel_z*q_z;
    //alpha = acos(cos_val_c);

    // parallelepiped a axis orientation
    parallel_x = -cos(phi)*sin(psi) * sin(theta)+sin(phi)*cos(psi);
    parallel_y = sin(psi)*cos(theta);
	//parallel_z = sin(theta)*sin(phi)*sin(psi)+cos(phi)*cos(psi);
	
    cos_val_a = parallel_x*q_x + parallel_y*q_y;

    // parallelepiped b axis orientation
    bparallel_x = -sin(theta)*cos(psi)*cos(phi)-sin(psi)*sin(phi);
    bparallel_y = cos(theta)*cos(psi);
    //bparallel_z = sin(theta)*sin(phi)*cos(psi)-sin(psi)*cos(phi);
    
    // axis of the parallelepiped
    cos_val_b = bparallel_x*q_x + bparallel_y*q_y;

    // The following test should always pass
    if (fabs(cos_val_c)>1.0) {
      //printf("parallel_ana_2D: Unexpected error: cos(alpha)>1\n");
      cos_val_c = 1.0;
    }
    if (fabs(cos_val_a)>1.0) {
      //printf("parallel_ana_2D: Unexpected error: cos(alpha)>1\n");
      cos_val_a = 1.0;
    }
    if (fabs(cos_val_b)>1.0) {
      //printf("parallel_ana_2D: Unexpected error: cos(alpha)>1\n");
      cos_val_b = 1.0;
    }
  // Call the IGOR library function to get the kernel
  form = pkernel( q*edgeA, q*edgeB, q*edgeC, cos_val_a, cos_val_b, cos_val_c);
  
  if (m_max < 1.0e-32 && m_max_solv < 1.0e-32){
      // Multiply by contrast^2
      contrast = (pars->sldPipe - pars->sldSolv);
 	  answer = contrast * contrast * form;
  }
  else{
	  double qx = q_x;
	  double qy = q_y;
	  double s_theta = pars->Up_theta;
	  double m_phi = pars->M_phi_pipe;
	  double m_theta = pars->M_theta_pipe;
	  double m_phi_solv = pars->M_phi_solv;
	  double m_theta_solv = pars->M_theta_solv;
	  double in_spin = pars->Up_frac_i;
	  double out_spin = pars->Up_frac_f;
	  polar_sld p_sld;
	  polar_sld p_sld_solv;
	  p_sld = cal_msld(1, qx, qy, sld_pipe, m_max, m_theta, m_phi, 
	  	 			in_spin, out_spin, s_theta);
	  p_sld_solv = cal_msld(1, qx, qy, sld_solv, m_max_solv, m_theta_solv, m_phi_solv, 
			 			in_spin, out_spin, s_theta);
	  //up_up	
	  if (in_spin > 0.0 && out_spin > 0.0){			 
		  answer += ((p_sld.uu- p_sld_solv.uu) * (p_sld.uu- p_sld_solv.uu) * form);
		  }
	  //down_down
	  if (in_spin < 1.0 && out_spin < 1.0){
		  answer += ((p_sld.dd - p_sld_solv.dd) * (p_sld.dd - p_sld_solv.dd) * form);
		  }
	  //up_down
	  if (in_spin > 0.0 && out_spin < 1.0){
		  answer += ((p_sld.re_ud - p_sld_solv.re_ud) * (p_sld.re_ud - p_sld_solv.re_ud) * form);
		  answer += ((p_sld.im_ud - p_sld_solv.im_ud) * (p_sld.im_ud - p_sld_solv.im_ud) * form);
		  }
	  //down_up	
	  if (in_spin < 1.0 && out_spin > 0.0){
		  answer += ((p_sld.re_du - p_sld_solv.re_du) * (p_sld.re_du - p_sld_solv.re_du) * form);
		  answer += ((p_sld.im_du - p_sld_solv.im_du) * (p_sld.im_du - p_sld_solv.im_du) * form);
		  }
  }
  

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

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the parallelepiped
 * @param q: q-value
 * @return: function value
 */
static double parallelepiped_analytical_2DXY(ParallelepipedParameters *pars, double qx, double qy) {
  double q;
  q = sqrt(qx*qx+qy*qy);
    return parallelepiped_analytical_2D_scaled(pars, q, qx/q, qy/q);
}

ParallelepipedModel :: ParallelepipedModel() {
	scale      = Parameter(1.0);
	short_a     = Parameter(35.0, true);
	short_a.set_min(1.0);
	short_b     = Parameter(75.0, true);
	short_b.set_min(1.0);
	long_c     = Parameter(400.0, true);
	long_c.set_min(1.0);
	sldPipe   = Parameter(6.3e-6);
	sldSolv   = Parameter(1.0e-6);
	background = Parameter(0.0);
	parallel_theta  = Parameter(0.0, true);
	parallel_phi    = Parameter(0.0, true);
	parallel_psi    = Parameter(0.0, true);
	M0_sld_pipe = Parameter(0.0e-6);
	M_theta_pipe = Parameter(0.0);
	M_phi_pipe = Parameter(0.0); 
	M0_sld_solv = Parameter(0.0e-6);
	M_theta_solv = Parameter(0.0);
	M_phi_solv = Parameter(0.0); 
	Up_frac_i = Parameter(0.5); 
	Up_frac_f = Parameter(0.5);
	Up_theta = Parameter(0.0);
}

/**
 * Function to evaluate 1D scattering function
 * The NIST IGOR library is used for the actual calculation.
 * @param q: q-value
 * @return: function value
 */
double ParallelepipedModel :: operator()(double q) {
	double dp[7];

	// Fill parameter array for IGOR library
	// Add the background after averaging
	dp[0] = scale();
	dp[1] = short_a();
	dp[2] = short_b();
	dp[3] = long_c();
	dp[4] = sldPipe();
	dp[5] = sldSolv();
	dp[6] = 0.0;

	// Get the dispersion points for the short_edgeA
	vector<WeightPoint> weights_short_a;
	short_a.get_weights(weights_short_a);

	// Get the dispersion points for the longer_edgeB
	vector<WeightPoint> weights_short_b;
	short_b.get_weights(weights_short_b);

	// Get the dispersion points for the longuest_edgeC
	vector<WeightPoint> weights_long_c;
	long_c.get_weights(weights_long_c);



	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;
	double vol = 0.0;

	// Loop over short_edgeA weight points
	for(int i=0; i< (int)weights_short_a.size(); i++) {
		dp[1] = weights_short_a[i].value;

		// Loop over longer_edgeB weight points
		for(int j=0; j< (int)weights_short_b.size(); j++) {
			dp[2] = weights_short_b[j].value;

			// Loop over longuest_edgeC weight points
			for(int k=0; k< (int)weights_long_c.size(); k++) {
				dp[3] = weights_long_c[k].value;
				//Un-normalize  by volume
				sum += weights_short_a[i].weight * weights_short_b[j].weight
					* weights_long_c[k].weight * Parallelepiped(dp, q)
					* weights_short_a[i].value*weights_short_b[j].value
					* weights_long_c[k].value;
				//Find average volume
				vol += weights_short_a[i].weight * weights_short_b[j].weight
					* weights_long_c[k].weight
					* weights_short_a[i].value * weights_short_b[j].value
					* weights_long_c[k].value;

				norm += weights_short_a[i].weight
					 * weights_short_b[j].weight * weights_long_c[k].weight;
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
double ParallelepipedModel :: operator()(double qx, double qy) {
	ParallelepipedParameters dp;
	// Fill parameter array
	dp.scale      = scale();
	dp.short_a   = short_a();
	dp.short_b   = short_b();
	dp.long_c  = long_c();
	dp.sldPipe   = sldPipe();
	dp.sldSolv   = sldSolv();
	dp.background = 0.0;
	//dp.background = background();
	dp.parallel_theta  = parallel_theta();
	dp.parallel_phi    = parallel_phi();
	dp.parallel_psi    = parallel_psi();
	dp.Up_theta =  Up_theta();
	dp.M_phi_pipe =  M_phi_pipe();
	dp.M_theta_pipe =  M_theta_pipe();
	dp.M0_sld_pipe =  M0_sld_pipe();
	dp.M_phi_solv =  M_phi_solv();
	dp.M_theta_solv =  M_theta_solv();
	dp.M0_sld_solv =  M0_sld_solv();
	dp.Up_frac_i =  Up_frac_i();
	dp.Up_frac_f =  Up_frac_f();


	// Get the dispersion points for the short_edgeA
	vector<WeightPoint> weights_short_a;
	short_a.get_weights(weights_short_a);

	// Get the dispersion points for the longer_edgeB
	vector<WeightPoint> weights_short_b;
	short_b.get_weights(weights_short_b);

	// Get angular averaging for the longuest_edgeC
	vector<WeightPoint> weights_long_c;
	long_c.get_weights(weights_long_c);

	// Get angular averaging for theta
	vector<WeightPoint> weights_parallel_theta;
	parallel_theta.get_weights(weights_parallel_theta);

	// Get angular averaging for phi
	vector<WeightPoint> weights_parallel_phi;
	parallel_phi.get_weights(weights_parallel_phi);

	// Get angular averaging for psi
	vector<WeightPoint> weights_parallel_psi;
	parallel_psi.get_weights(weights_parallel_psi);

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;
	double norm_vol = 0.0;
	double vol = 0.0;
	double pi = 4.0*atan(1.0);
	// Loop over radius weight points
	for(int i=0; i< (int)weights_short_a.size(); i++) {
		dp.short_a = weights_short_a[i].value;

		// Loop over longer_edgeB weight points
		for(int j=0; j< (int)weights_short_b.size(); j++) {
			dp.short_b = weights_short_b[j].value;

			// Average over longuest_edgeC distribution
			for(int k=0; k< (int)weights_long_c.size(); k++) {
				dp.long_c = weights_long_c[k].value;

				// Average over theta distribution
				for(int l=0; l< (int)weights_parallel_theta.size(); l++) {
				dp.parallel_theta = weights_parallel_theta[l].value;

					// Average over phi distribution
					for(int m=0; m< (int)weights_parallel_phi.size(); m++) {
						dp.parallel_phi = weights_parallel_phi[m].value;

						// Average over phi distribution
						for(int n=0; n< (int)weights_parallel_psi.size(); n++) {
							dp.parallel_psi = weights_parallel_psi[n].value;
							//Un-normalize by volume
							double _ptvalue = weights_short_a[i].weight
								* weights_short_b[j].weight
								* weights_long_c[k].weight
								* weights_parallel_theta[l].weight
								* weights_parallel_phi[m].weight
								* weights_parallel_psi[n].weight
								* parallelepiped_analytical_2DXY(&dp, qx, qy)
								* weights_short_a[i].value*weights_short_b[j].value
								* weights_long_c[k].value;

							if (weights_parallel_theta.size()>1) {
								_ptvalue *= fabs(cos(weights_parallel_theta[l].value*pi/180.0));
							}
							sum += _ptvalue;
							//Find average volume
							vol += weights_short_a[i].weight
								* weights_short_b[j].weight
								* weights_long_c[k].weight
								* weights_short_a[i].value*weights_short_b[j].value
								* weights_long_c[k].value;
							//Find norm for volume
							norm_vol += weights_short_a[i].weight
								* weights_short_b[j].weight
								* weights_long_c[k].weight;

							norm += weights_short_a[i].weight
								* weights_short_b[j].weight
								* weights_long_c[k].weight
								* weights_parallel_theta[l].weight
								* weights_parallel_phi[m].weight
								* weights_parallel_psi[n].weight;
						}
					}

				}
			}
		}
	}
	// Averaging in theta needs an extra normalization
	// factor to account for the sin(theta) term in the
	// integration (see documentation).
	if (weights_parallel_theta.size()>1) norm = norm / asin(1.0);

	if (vol != 0.0 && norm_vol != 0.0) {
		//Re-normalize by avg volume
		sum = sum/(vol/norm_vol);}

	return sum/norm + background();
}


/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the cylinder
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double ParallelepipedModel :: evaluate_rphi(double q, double phi) {
	double qx = q*cos(phi);
	double qy = q*sin(phi);
	return (*this).operator()(qx, qy);
}
/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double ParallelepipedModel :: calculate_ER() {
	ParallelepipedParameters dp;
	dp.short_a   = short_a();
	dp.short_b   = short_b();
	dp.long_c  = long_c();
	double rad_out = 0.0;
	double pi = 4.0*atan(1.0);
	double suf_rad = sqrt(dp.short_a*dp.short_b/pi);

	// Perform the computation, with all weight points
	double sum = 0.0;
	double norm = 0.0;

	// Get the dispersion points for the short_edgeA
	vector<WeightPoint> weights_short_a;
	short_a.get_weights(weights_short_a);

	// Get the dispersion points for the longer_edgeB
	vector<WeightPoint> weights_short_b;
	short_b.get_weights(weights_short_b);

	// Get angular averaging for the longuest_edgeC
	vector<WeightPoint> weights_long_c;
	long_c.get_weights(weights_long_c);

	// Loop over radius weight points
	for(int i=0; i< (int)weights_short_a.size(); i++) {
		dp.short_a = weights_short_a[i].value;

		// Loop over longer_edgeB weight points
		for(int j=0; j< (int)weights_short_b.size(); j++) {
			dp.short_b = weights_short_b[j].value;

			// Average over longuest_edgeC distribution
			for(int k=0; k< (int)weights_long_c.size(); k++) {
				dp.long_c = weights_long_c[k].value;
				//Calculate surface averaged radius
				//This is rough approximation.
				suf_rad = sqrt(dp.short_a*dp.short_b/pi);

				//Note: output of "DiamCyl(dp.length,dp.radius)" is DIAMETER.
				sum +=weights_short_a[i].weight* weights_short_b[j].weight
					* weights_long_c[k].weight*DiamCyl(dp.long_c, suf_rad)/2.0;
				norm += weights_short_a[i].weight* weights_short_b[j].weight*weights_long_c[k].weight;
			}
		}
	}

	if (norm != 0){
		//return the averaged value
		rad_out =  sum/norm;}
	else{
		//return normal value
		//Note: output of "DiamCyl(length,radius)" is DIAMETER.
		rad_out = DiamCyl(dp.long_c, suf_rad)/2.0;}
	return rad_out;

}
double ParallelepipedModel :: calculate_VR() {
  return 1.0;
}
