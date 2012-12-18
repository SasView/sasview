/**
	This software was developed by the University of Tennessee as part of the
	Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
	project funded by the US National Science Foundation.

	If you use DANSE applications to do scientific research that leads to
	publication, we ask that you acknowledge the use of the software with the
	following sentence:

	"This work benefited from DANSE software developed under NSF award DMR-0520547."

	copyright 2010, University of Tennessee
 */

/**
 * Scattering model classes
 * The classes use the IGOR library found in
 *   sansmodels/src/libigor
 */

#include <math.h>
#include "parameters.hh"
#include <stdio.h>
using namespace std;

extern "C" {
#include "libCylinder.h"
#include "libStructureFactor.h"
}
#include "csparallelepiped.h"

// Convenience parameter structure
typedef struct {
  double scale;
  double shortA;
  double midB;
  double longC;
  double rimA;
  double rimB;
  double rimC;
  double sld_rimA;
  double sld_rimB;
  double sld_rimC;
  double sld_pcore;
  double sld_solv;
  double background;
  double parallel_theta;
  double parallel_phi;
  double parallel_psi;
} CSParallelepipedParameters;

static double cspkernel(double dp[],double q, double ala, double alb, double alc){
  // mu passed in is really mu*sqrt(1-sig^2)
  double argA,argB,argC,argtA,argtB,argtC,tmp1,tmp2,tmp3,tmpt1,tmpt2,tmpt3;     //local variables

  double aa,bb,cc, ta,tb,tc;
  double Vin,Vot,V1,V2,V3;
  double rhoA,rhoB,rhoC, rhoP, rhosolv;
  double dr0, drA,drB, drC;
  double retVal;

  aa = dp[1];
  bb = dp[2];
  cc = dp[3];
  ta = dp[4];
  tb = dp[5];
  tc = dp[6];
  rhoA=dp[7];
  rhoB=dp[8];
  rhoC=dp[9];
  rhoP=dp[10];
  rhosolv=dp[11];
  dr0=rhoP-rhosolv;
  drA=rhoA-rhosolv;
  drB=rhoB-rhosolv;
  drC=rhoC-rhosolv;
  Vin=(aa*bb*cc);
  Vot=(aa*bb*cc+2.0*ta*bb*cc+2.0*aa*tb*cc+2.0*aa*bb*tc);
  V1=(2.0*ta*bb*cc);   //  incorrect V1 (aa*bb*cc+2*ta*bb*cc)
  V2=(2.0*aa*tb*cc);  // incorrect V2(aa*bb*cc+2*aa*tb*cc)
  V3=(2.0*aa*bb*tc);
  //aa = aa/bb;
  ta=(aa+2.0*ta);///bb;
  tb=(aa+2.0*tb);///bb;
  tc=(aa+2.0*tc);
  //handle arg=0 separately, as sin(t)/t -> 1 as t->0
  argA = q*aa*ala/2.0;
  argB = q*bb*alb/2.0;
  argC = q*cc*alc/2.0;
  argtA = q*ta*ala/2.0;
  argtB = q*tb*alb/2.0;
  argtC = q*tc*alc/2.0;

  if(argA==0.0) {
    tmp1 = 1.0;
  } else {
    tmp1 = sin(argA)/argA;
  }
  if (argB==0.0) {
    tmp2 = 1.0;
  } else {
    tmp2 = sin(argB)/argB;
  }

  if (argC==0.0) {
    tmp3 = 1.0;
  } else {
    tmp3 = sin(argC)/argC;
  }
  if(argtA==0.0) {
    tmpt1 = 1.0;
  } else {
    tmpt1 = sin(argtA)/argtA;
  }
  if (argtB==0.0) {
    tmpt2 = 1.0;
  } else {
    tmpt2 = sin(argtB)/argtB;
  }
  if (argtC==0.0) {
    tmpt3 = 1.0;
  } else {
    tmpt3 = sin(argtC)*sin(argtC)/argtC/argtC;
  }
  // This expression is different from NIST/IGOR package (I strongly believe the IGOR is wrong!!!). 10/15/2010.
  retVal =( dr0*tmp1*tmp2*tmp3*Vin + drA*(tmpt1-tmp1)*tmp2*tmp3*V1+ drB*tmp1*(tmpt2-tmp2)*tmp3*V2 + drC*tmp1*tmp2*(tmpt3-tmp3)*V3)*
      ( dr0*tmp1*tmp2*tmp3*Vin + drA*(tmpt1-tmp1)*tmp2*tmp3*V1+ drB*tmp1*(tmpt2-tmp2)*tmp3*V2 + drC*tmp1*tmp2*(tmpt3-tmp3)*V3);   //  correct FF : square of sum of phase factors
  //retVal *= (tmp3*tmp3);
  retVal /= Vot;

  return (retVal);

}//Function cspkernel()

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the CSparallelepiped
 * @param q: q-value
 * @param q_x: q_x / q
 * @param q_y: q_y / q
 * @return: function value
 */
static double csparallelepiped_analytical_2D_scaled(CSParallelepipedParameters *pars, double q, double q_x, double q_y) {
  double dp[13];
  double cparallel_x, cparallel_y, bparallel_x, bparallel_y, parallel_x, parallel_y;
  //double q_z;
  double cos_val_c, cos_val_b, cos_val_a, edgeA, edgeB, edgeC;

  double answer;
  //convert angle degree to radian
  double pi = 4.0*atan(1.0);
  double theta = pars->parallel_theta * pi/180.0;
  double phi = pars->parallel_phi * pi/180.0;
  double psi = pars->parallel_psi* pi/180.0;

  // Fill paramater array
  dp[0] = 1.0;
  dp[1] = pars->shortA;
  dp[2] = pars->midB;
  dp[3] = pars->longC;
  dp[4] = pars->rimA;
  dp[5] = pars->rimB;
  dp[6] = pars->rimC;
  dp[7] = pars->sld_rimA;
  dp[8] = pars->sld_rimB;
  dp[9] = pars->sld_rimC;
  dp[10] = pars->sld_pcore;
  dp[11] = pars->sld_solv;
  dp[12] = 0.0;


  edgeA = pars->shortA;
  edgeB = pars->midB;
  edgeC = pars->longC;


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

  cos_val_a = parallel_x*q_x + parallel_y*q_y;



  // parallelepiped b axis orientation
  bparallel_x = -sin(theta)*cos(psi)*cos(phi)-sin(psi)*sin(phi);
  bparallel_y = cos(theta)*cos(psi);
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
  answer = cspkernel( dp, q, cos_val_a, cos_val_b, cos_val_c);

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
 * @param pars: parameters of the CSparallelepiped
 * @param q: q-value
 * @return: function value
 */
static double csparallelepiped_analytical_2DXY(CSParallelepipedParameters *pars, double qx, double qy) {
  double q;
  q = sqrt(qx*qx+qy*qy);
  return csparallelepiped_analytical_2D_scaled(pars, q, qx/q, qy/q);
}




CSParallelepipedModel :: CSParallelepipedModel() {
  scale      = Parameter(1.0);
  shortA     = Parameter(35.0, true);
  shortA.set_min(1.0);
  midB     = Parameter(75.0, true);
  midB.set_min(1.0);
  longC    = Parameter(400.0, true);
  longC.set_min(1.0);
  rimA     = Parameter(10.0, true);
  rimB     = Parameter(10.0, true);
  rimC     = Parameter(10.0, true);
  sld_rimA     = Parameter(2.0e-6, true);
  sld_rimB     = Parameter(4.0e-6, true);
  sld_rimC    = Parameter(2.0e-6, true);
  sld_pcore   = Parameter(1.0e-6);
  sld_solv   = Parameter(6.0e-6);
  background = Parameter(0.06);
  parallel_theta  = Parameter(0.0, true);
  parallel_phi    = Parameter(0.0, true);
  parallel_psi    = Parameter(0.0, true);
}

/**
 * Function to evaluate 1D scattering function
 * The NIST IGOR library is used for the actual calculation.
 * @param q: q-value
 * @return: function value
 */
double CSParallelepipedModel :: operator()(double q) {
  double dp[13];

  // Fill parameter array for IGOR library
  // Add the background after averaging
  dp[0] = scale();
  dp[1] = shortA();
  dp[2] = midB();
  dp[3] = longC();
  dp[4] = rimA();
  dp[5] = rimB();
  dp[6] = rimC();
  dp[7] = sld_rimA();
  dp[8] = sld_rimB();
  dp[9] = sld_rimC();
  dp[10] = sld_pcore();
  dp[11] = sld_solv();
  dp[12] = 0.0;

  // Get the dispersion points for the short_edgeA
  vector<WeightPoint> weights_shortA;
  shortA.get_weights(weights_shortA);

  // Get the dispersion points for the longer_edgeB
  vector<WeightPoint> weights_midB;
  midB.get_weights(weights_midB);

  // Get the dispersion points for the longuest_edgeC
  vector<WeightPoint> weights_longC;
  longC.get_weights(weights_longC);



  // Perform the computation, with all weight points
  double sum = 0.0;
  double norm = 0.0;
  double vol = 0.0;

  // Loop over short_edgeA weight points
  for(int i=0; i< (int)weights_shortA.size(); i++) {
    dp[1] = weights_shortA[i].value;

    // Loop over longer_edgeB weight points
    for(int j=0; j< (int)weights_midB.size(); j++) {
      dp[2] = weights_midB[j].value;

      // Loop over longuest_edgeC weight points
      for(int k=0; k< (int)weights_longC.size(); k++) {
        dp[3] = weights_longC[k].value;
        //Un-normalize  by volume
        sum += weights_shortA[i].weight * weights_midB[j].weight
            * weights_longC[k].weight * CSParallelepiped(dp, q)
        * weights_shortA[i].value*weights_midB[j].value
        * weights_longC[k].value;
        //Find average volume
        vol += weights_shortA[i].weight * weights_midB[j].weight
            * weights_longC[k].weight
            * weights_shortA[i].value * weights_midB[j].value
            * weights_longC[k].value;

        norm += weights_shortA[i].weight
            * weights_midB[j].weight * weights_longC[k].weight;
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
double CSParallelepipedModel :: operator()(double qx, double qy) {
  CSParallelepipedParameters dp;
  // Fill parameter array
  dp.scale      = scale();
  dp.shortA   = shortA();
  dp.midB   = midB();
  dp.longC  = longC();
  dp.rimA   = rimA();
  dp.rimB   = rimB();
  dp.rimC  = rimC();
  dp.sld_rimA   = sld_rimA();
  dp.sld_rimB   = sld_rimB();
  dp.sld_rimC  = sld_rimC();
  dp.sld_pcore   = sld_pcore();
  dp.sld_solv   = sld_solv();
  dp.background = 0.0;
  //dp.background = background();
  dp.parallel_theta  = parallel_theta();
  dp.parallel_phi    = parallel_phi();
  dp.parallel_psi    = parallel_psi();



  // Get the dispersion points for the short_edgeA
  vector<WeightPoint> weights_shortA;
  shortA.get_weights(weights_shortA);

  // Get the dispersion points for the longer_edgeB
  vector<WeightPoint> weights_midB;
  midB.get_weights(weights_midB);

  // Get the dispersion points for the longuest_edgeC
  vector<WeightPoint> weights_longC;
  longC.get_weights(weights_longC);

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
  for(int i=0; i< (int)weights_shortA.size(); i++) {
    dp.shortA = weights_shortA[i].value;

    // Loop over longer_edgeB weight points
    for(int j=0; j< (int)weights_midB.size(); j++) {
      dp.midB = weights_midB[j].value;

      // Average over longuest_edgeC distribution
      for(int k=0; k< (int)weights_longC.size(); k++) {
        dp.longC = weights_longC[k].value;

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
              double _ptvalue = weights_shortA[i].weight
                  * weights_midB[j].weight
                  * weights_longC[k].weight
                  * weights_parallel_theta[l].weight
                  * weights_parallel_phi[m].weight
                  * weights_parallel_psi[n].weight
                  * csparallelepiped_analytical_2DXY(&dp, qx, qy)
              * weights_shortA[i].value*weights_midB[j].value
              * weights_longC[k].value;

              if (weights_parallel_theta.size()>1) {
                _ptvalue *= fabs(cos(weights_parallel_theta[l].value*pi/180.0));
              }
              sum += _ptvalue;
              //Find average volume
              vol += weights_shortA[i].weight
                  * weights_midB[j].weight
                  * weights_longC[k].weight
                  * weights_shortA[i].value*weights_midB[j].value
                  * weights_longC[k].value;
              //Find norm for volume
              norm_vol += weights_shortA[i].weight
                  * weights_midB[j].weight
                  * weights_longC[k].weight;

              norm += weights_shortA[i].weight
                  * weights_midB[j].weight
                  * weights_longC[k].weight
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
double CSParallelepipedModel :: evaluate_rphi(double q, double phi) {
  double qx = q*cos(phi);
  double qy = q*sin(phi);
  return (*this).operator()(qx, qy);
}
/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double CSParallelepipedModel :: calculate_ER() {
  CSParallelepipedParameters dp;
  dp.shortA   = shortA();
  dp.midB   = midB();
  dp.longC  = longC();
  dp.rimA   = rimA();
  dp.rimB   = rimB();
  dp.rimC  = rimC();

  double rad_out = 0.0;
  double pi = 4.0*atan(1.0);
  double suf_rad = sqrt((dp.shortA*dp.midB+2.0*dp.rimA*dp.midB+2.0*dp.rimA*dp.shortA)/pi);
  double height =(dp.longC + 2.0*dp.rimC);
  // Perform the computation, with all weight points
  double sum = 0.0;
  double norm = 0.0;

  // Get the dispersion points for the short_edgeA
  vector<WeightPoint> weights_shortA;
  shortA.get_weights(weights_shortA);

  // Get the dispersion points for the longer_edgeB
  vector<WeightPoint> weights_midB;
  midB.get_weights(weights_midB);

  // Get angular averaging for the longuest_edgeC
  vector<WeightPoint> weights_longC;
  longC.get_weights(weights_longC);

  // Loop over radius weight points
  for(int i=0; i< (int)weights_shortA.size(); i++) {
    dp.shortA = weights_shortA[i].value;

    // Loop over longer_edgeB weight points
    for(int j=0; j< (int)weights_midB.size(); j++) {
      dp.midB = weights_midB[j].value;

      // Average over longuest_edgeC distribution
      for(int k=0; k< (int)weights_longC.size(); k++) {
        dp.longC = weights_longC[k].value;
        //Calculate surface averaged radius
        //This is rough approximation.
        suf_rad = sqrt((dp.shortA*dp.midB+2.0*dp.rimA*dp.midB+2.0*dp.rimA*dp.shortA)/pi);
        height =(dp.longC + 2.0*dp.rimC);
        //Note: output of "DiamCyl(dp.length,dp.radius)" is a DIAMETER.
        sum +=weights_shortA[i].weight* weights_midB[j].weight
            * weights_longC[k].weight*DiamCyl(height, suf_rad)/2.0;
        norm += weights_shortA[i].weight* weights_midB[j].weight*weights_longC[k].weight;
      }
    }
  }

  if (norm != 0){
    //return the averaged value
    rad_out =  sum/norm;}
  else{
    //return normal value
    //Note: output of "DiamCyl(length,radius)" is DIAMETER.
    rad_out = DiamCyl(dp.longC, suf_rad)/2.0;}
  return rad_out;

}
double CSParallelepipedModel :: calculate_VR() {
  return 1.0;
}
