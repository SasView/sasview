
#include <math.h>
#include "parameters.hh"
#include <stdio.h>
#include <stdlib.h>

extern "C" {
#include "libmultifunc/librefl.h"
}

#include "spheresld.h"

using namespace std;

// Convenience structure
typedef struct {
  /// number of shells
  //  [DEFAULT]=n_shells=1
  int n_shells;
  /// Scale factor
  //  [DEFAULT]=scale= 1.0
  double scale;
  /// thick_inter0 [A]
  //  [DEFAULT]=thick_inter0=50.0 [A]
  double thick_inter0;
  /// func_inter0
  //  [DEFAULT]=func_inter0= 0
  double func_inter0;
  /// sld_core0 [1/A^(2)]
  //  [DEFAULT]=sld_core0= 2.07e-6 [1/A^(2)]
  double sld_core0;
  /// sld_solv [1/A^(2)]
  //  [DEFAULT]=sld_solv= 1.0e-6 [1/A^(2)]
  double sld_solv;
  /// Background
  //  [DEFAULT]=background=0
  double background;

  //  [DEFAULT]=sld_flat1=4.0e-06 [1/A^(2)]
  double sld_flat1;
  //  [DEFAULT]=sld_flat2=3.5e-06 [1/A^(2)]
  double sld_flat2;
  //  [DEFAULT]=sld_flat3=4.0e-06 [1/A^(2)]
  double sld_flat3;
  //  [DEFAULT]=sld_flat4=3.5e-06 [1/A^(2)]
  double sld_flat4;
  //  [DEFAULT]=sld_flat5=4.0e-06 [1/A^(2)]
  double sld_flat5;
  //  [DEFAULT]=sld_flat6=3.5e-06 [1/A^(2)]
  double sld_flat6;
  //  [DEFAULT]=sld_flat7=4.0e-06 [1/A^(2)]
  double sld_flat7;
  //  [DEFAULT]=sld_flat8=3.5e-06 [1/A^(2)]
  double sld_flat8;
  //  [DEFAULT]=sld_flat9=4.0e-06 [1/A^(2)]
  double sld_flat9;
  //  [DEFAULT]=sld_flat10=3.5e-06 [1/A^(2)]
  double sld_flat10;

  //  [DEFAULT]=thick_inter1=50.0 [A]
  double thick_inter1;
  //  [DEFAULT]=thick_inter2=50.0 [A]
  double thick_inter2;
  //  [DEFAULT]=thick_inter3=50.0 [A]
  double thick_inter3;
  //  [DEFAULT]=thick_inter4=50.0 [A]
  double thick_inter4;
  //  [DEFAULT]=thick_inter5=50.0 [A]
  double thick_inter5;
  //  [DEFAULT]=thick_inter6=50.0 [A]
  double thick_inter6;
  //  [DEFAULT]=thick_inter7=50.0 [A]
  double thick_inter7;
  //  [DEFAULT]=thick_inter8=50.0 [A]
  double thick_inter8;
  //  [DEFAULT]=thick_inter9=50.0 [A]
  double thick_inter9;
  //  [DEFAULT]=thick_inter10=50.0 [A]
  double thick_inter10;

  //  [DEFAULT]=thick_flat1=100 [A]
  double thick_flat1;
  //  [DEFAULT]=thick_flat2=100 [A]
  double thick_flat2;
  //  [DEFAULT]=thick_flat3=100 [A]
  double thick_flat3;
  //  [DEFAULT]=thick_flat4=100 [A]
  double thick_flat4;
  //  [DEFAULT]=thick_flat5=100 [A]
  double thick_flat5;
  //  [DEFAULT]=thick_flat6=100 [A]
  double thick_flat6;
  //  [DEFAULT]=thick_flat7=100 [A]
  double thick_flat7;
  //  [DEFAULT]=thick_flat8=100 [A]
  double thick_flat8;
  //  [DEFAULT]=thick_flat9=100 [A]
  double thick_flat9;
  //  [DEFAULT]=thick_flat10=100 [A]
  double thick_flat10;

  //  [DEFAULT]=func_inter1=0
  double func_inter1;
  //  [DEFAULT]=func_inter2=0
  double func_inter2;
  //  [DEFAULT]=func_inter3=0
  double func_inter3;
  //  [DEFAULT]=func_inter4=0
  double func_inter4;
  //  [DEFAULT]=func_inter5=0
  double func_inter5;
  //  [DEFAULT]=func_inter6=0
  double func_inter6;
  //  [DEFAULT]=func_inter7=0
  double func_inter7;
  //  [DEFAULT]=func_inter8=0
  double func_inter8;
  //  [DEFAULT]=func_inter9=0
  double func_inter9;
  //  [DEFAULT]=func_inter10=0
  double func_inter10;

  //  [DEFAULT]=nu_inter1=2.5
  double nu_inter1;
  //  [DEFAULT]=nu_inter2=2.5
  double nu_inter2;
  //  [DEFAULT]=nu_inter3=2.5
  double nu_inter3;
  //  [DEFAULT]=nu_inter4=2.5
  double nu_inter4;
  //  [DEFAULT]=nu_inter5=2.5
  double nu_inter5;
  //  [DEFAULT]=nu_inter6=2.5
  double nu_inter6;
  //  [DEFAULT]=nu_inter7=2.5
  double nu_inter7;
  //  [DEFAULT]=nu_inter8=2.5
  double nu_inter8;
  //  [DEFAULT]=nu_inter9=2.5
  double nu_inter9;
  //  [DEFAULT]=nu_inter10=2.5
  double nu_inter10;

  //  [DEFAULT]=npts_inter=35.0
  double npts_inter;
  //  [DEFAULT]=nu_inter0=2.5
  double nu_inter0;
  //  [DEFAULT]=rad_core0=50.0 [A]
  double rad_core0;
} SphereSLDParameters;


static double sphere_sld_kernel(double dp[], double q) {
  int n = dp[0];
  int i,j,k;

  double scale = dp[1];
  double thick_inter_core = dp[2];
  double sld_core = dp[4];
  double sld_solv = dp[5];
  double background = dp[6];
  double npts = dp[57]; //number of sub_layers in each interface
  double nsl=npts;//21.0; //nsl = Num_sub_layer:  MUST ODD number in double //no other number works now
  int n_s;

  double sld_i,sld_f,dz,bes,fun,f,vol,vol_pre,vol_sub,qr,r,contr,f2;
  double sign,slope=0.0;
  double pi;

  int* fun_type;
  double* sld;
  double* thick_inter;
  double* thick;
  double* fun_coef;

  double total_thick=0.0;

  fun_type = (int*)malloc((n+2)*sizeof(int));
  sld = (double*)malloc((n+2)*sizeof(double));
  thick_inter = (double*)malloc((n+2)*sizeof(double));
  thick = (double*)malloc((n+2)*sizeof(double));
  fun_coef = (double*)malloc((n+2)*sizeof(double));

  fun_type[0] = dp[3];
  fun_coef[0] = fabs(dp[58]);
  for (i =1; i<=n; i++){
    sld[i] = dp[i+6];
    thick_inter[i]= dp[i+16];
    thick[i] = dp[i+26];
    fun_type[i] = dp[i+36];
    fun_coef[i] = fabs(dp[i+46]);
    total_thick += thick[i] + thick_inter[i];
  }
  sld[0] = sld_core;
  sld[n+1] = sld_solv;
  thick[0] = dp[59];
  thick[n+1] = total_thick/5.0;
  thick_inter[0] = thick_inter_core;
  thick_inter[n+1] = 0.0;
  fun_coef[n+1] = 0.0;

  pi = 4.0*atan(1.0);
  f = 0.0;
  r = 0.0;
  vol = 0.0;
  vol_pre = 0.0;
  vol_sub = 0.0;
  sld_f = sld_core;

  //floor_nsl = floor(nsl/2.0);

  dz = 0.0;
  // iteration for # of shells + core + solvent
  for (i=0;i<=n+1; i++){
    //iteration for N sub-layers
    //if (fabs(thick[i]) <= 1e-24){
    //   continue;
    //}
    // iteration for flat and interface
    for (j=0;j<2;j++){
      // iteration for sub_shells in the interface
      // starts from #1 sub-layer
      for (n_s=1;n_s<=nsl; n_s++){
        // for solvent, it doesn't have an interface
        if (i==n+1 && j==1)
          break;
        // for flat layers
        if (j==0){
          dz = thick[i];
          sld_i = sld[i];
          slope = 0.0;
        }
        // for interfacial sub_shells
        else{
          dz = thick_inter[i]/nsl;
          // find sld_i at the outer boundary of sub-layer #n_s
          sld_i = intersldfunc(fun_type[i],nsl, n_s, fun_coef[i], sld[i], sld[i+1]);
          // calculate slope
          slope= (sld_i -sld_f)/dz;
        }
        contr = sld_f-slope*r;
        // iteration for the left and right boundary of the shells(or sub_shells)
        for (k=0; k<2; k++){
          // At r=0, the contribution to I is zero, so skip it.
          if ( i == 0 && j == 0 && k == 0){
            continue;
          }
          // On the top of slovent there is no interface; skip it.
          if (i == n+1 && k == 1){
            continue;
          }
          // At the right side (outer) boundary
          if ( k == 1){
            sign = 1.0;
            r += dz;
          }
          // At the left side (inner) boundary
          else{
            sign = -1.0;
          }
          qr = q * r;
          fun = 0.0;
          if(qr == 0.0){
            // sigular point
            bes = sign * 1.0;
          }
          else{
            // for flat sub-layer
            bes = sign *  3.0 * (sin(qr) - qr * cos(qr)) / (qr * qr * qr);
            // with linear slope
            if (fabs(slope) > 0.0 ){
              fun = sign * 3.0 * r * (2.0*qr*sin(qr)-((qr*qr)-2.0)*cos(qr))/(qr * qr * qr * qr);
            }
          }
          // update total volume
          vol = 4.0 * pi / 3.0 * r * r * r;
          // we won't do the following volume correction for now.
          // substrate empty area of volume
          //if (k == 1 && fabs(sld_in[i]-sld_solv) < 1e-04*fabs(sld_solv) && fun_type[i]==0){
          //  vol_sub += (vol_pre - vol);
          //}
          f += vol * (bes * contr + fun * slope);
        }
        // remember this sld as sld_f
        sld_f =sld_i;
        // no sub-layer iteration (n_s loop) for the flat layer
        if (j==0)
          break;
      }
    }
  }
  //vol += vol_sub;
  f2 = f * f / vol * 1.0e8;
  f2 *= scale;
  f2 += background;

  free(fun_type);
  free(sld);
  free(thick_inter);
  free(thick);
  free(fun_coef);

  return (f2);
}


SphereSLDModel :: SphereSLDModel() {
  n_shells = Parameter(1.0);
  scale = Parameter(1.0);
  thick_inter0 = Parameter(1.0, true);
  thick_inter0.set_min(0.0);
  func_inter0 = Parameter(0);
  sld_core0 = Parameter(2.07e-06);
  sld_solv = Parameter(1.0e-06);
  background = Parameter(0.0);


  sld_flat1 = Parameter(2.7e-06);
  sld_flat2 = Parameter(3.5e-06);
  sld_flat3 = Parameter(4.0e-06);
  sld_flat4 = Parameter(3.5e-06);
  sld_flat5 = Parameter(4.0e-06);
  sld_flat6 = Parameter(3.5e-06);
  sld_flat7 = Parameter(4.0e-06);
  sld_flat8 = Parameter(3.5e-06);
  sld_flat9 = Parameter(4.0e-06);
  sld_flat10 = Parameter(3.5e-06);


  thick_inter1 = Parameter(1.0);
  thick_inter2 = Parameter(1.0);
  thick_inter3 = Parameter(1.0);
  thick_inter4 = Parameter(1.0);
  thick_inter5 = Parameter(1.0);
  thick_inter6 = Parameter(1.0);
  thick_inter7 = Parameter(1.0);
  thick_inter8 = Parameter(1.0);
  thick_inter9 = Parameter(1.0);
  thick_inter10 = Parameter(1.0);


  thick_flat1 = Parameter(100.0);
  thick_flat2 = Parameter(100.0);
  thick_flat3 = Parameter(100.0);
  thick_flat4 = Parameter(100.0);
  thick_flat5 = Parameter(100.0);
  thick_flat6 = Parameter(100.0);
  thick_flat7 = Parameter(100.0);
  thick_flat8 = Parameter(100.0);
  thick_flat9 = Parameter(100.0);
  thick_flat10 = Parameter(100.0);


  func_inter1 = Parameter(0);
  func_inter2 = Parameter(0);
  func_inter3 = Parameter(0);
  func_inter4 = Parameter(0);
  func_inter5 = Parameter(0);
  func_inter6 = Parameter(0);
  func_inter7 = Parameter(0);
  func_inter8 = Parameter(0);
  func_inter9 = Parameter(0);
  func_inter10 = Parameter(0);

  nu_inter1 = Parameter(2.5);
  nu_inter2 = Parameter(2.5);
  nu_inter3 = Parameter(2.5);
  nu_inter4 = Parameter(2.5);
  nu_inter5 = Parameter(2.5);
  nu_inter6 = Parameter(2.5);
  nu_inter7 = Parameter(2.5);
  nu_inter8 = Parameter(2.5);
  nu_inter9 = Parameter(2.5);
  nu_inter10 = Parameter(2.5);

  npts_inter = Parameter(35.0);
  nu_inter0 = Parameter(2.5);
  rad_core0 = Parameter(60.0, true);
  rad_core0.set_min(0.0);
}

/**
 * Function to evaluate 1D SphereSLD function
 * @param q: q-value
 * @return: function value
 */
double SphereSLDModel :: operator()(double q) {
  double dp[60];
  // Fill parameter array for IGOR library
  // Add the background after averaging
  dp[0] = n_shells();
  dp[1] = scale();
  dp[2] = thick_inter0();
  dp[3] = func_inter0();
  dp[4] = sld_core0();
  dp[5] = sld_solv();
  dp[6] = 0.0;

  dp[7] = sld_flat1();
  dp[8] = sld_flat2();
  dp[9] = sld_flat3();
  dp[10] = sld_flat4();
  dp[11] = sld_flat5();
  dp[12] = sld_flat6();
  dp[13] = sld_flat7();
  dp[14] = sld_flat8();
  dp[15] = sld_flat9();
  dp[16] = sld_flat10();

  dp[17] = thick_inter1();
  dp[18] = thick_inter2();
  dp[19] = thick_inter3();
  dp[20] = thick_inter4();
  dp[21] = thick_inter5();
  dp[22] = thick_inter6();
  dp[23] = thick_inter7();
  dp[24] = thick_inter8();
  dp[25] = thick_inter9();
  dp[26] = thick_inter10();

  dp[27] = thick_flat1();
  dp[28] = thick_flat2();
  dp[29] = thick_flat3();
  dp[30] = thick_flat4();
  dp[31] = thick_flat5();
  dp[32] = thick_flat6();
  dp[33] = thick_flat7();
  dp[34] = thick_flat8();
  dp[35] = thick_flat9();
  dp[36] = thick_flat10();

  dp[37] = func_inter1();
  dp[38] = func_inter2();
  dp[39] = func_inter3();
  dp[40] = func_inter4();
  dp[41] = func_inter5();
  dp[42] = func_inter6();
  dp[43] = func_inter7();
  dp[44] = func_inter8();
  dp[45] = func_inter9();
  dp[46] = func_inter10();

  dp[47] = nu_inter1();
  dp[48] = nu_inter2();
  dp[49] = nu_inter3();
  dp[50] = nu_inter4();
  dp[51] = nu_inter5();
  dp[52] = nu_inter6();
  dp[53] = nu_inter7();
  dp[54] = nu_inter8();
  dp[55] = nu_inter9();
  dp[56] = nu_inter10();


  dp[57] = npts_inter();
  dp[58] = nu_inter0();
  dp[59] = rad_core0();

  // No polydispersion supported in this model.
  // Get the dispersion points for the radius
  vector<WeightPoint> weights_rad_core0;
  rad_core0.get_weights(weights_rad_core0);
  vector<WeightPoint> weights_thick_inter0;
  thick_inter0.get_weights(weights_thick_inter0);
  // Perform the computation, with all weight points
  double sum = 0.0;
  double norm = 0.0;
  double vol = 0.0;

  // Loop over core weight points
  for(size_t i=0; i<weights_rad_core0.size(); i++) {
    dp[59] = weights_rad_core0[i].value;
    // Loop over thick_inter0 weight points
    for(size_t j=0; j<weights_thick_inter0.size(); j++) {
      dp[2] = weights_thick_inter0[j].value;

      //Un-normalize Sphere by volume
      sum += weights_rad_core0[i].weight * weights_thick_inter0[j].weight
          * sphere_sld_kernel(dp,q) * pow((weights_rad_core0[i].value +
              weights_thick_inter0[j].value),3.0);
      //Find average volume
      vol += weights_rad_core0[i].weight * weights_thick_inter0[j].weight
          * pow((weights_rad_core0[i].value+weights_thick_inter0[j].value),3.0);

      norm += weights_rad_core0[i].weight * weights_thick_inter0[j].weight;
    }
  }

  if (vol != 0.0 && norm != 0.0) {
    //Re-normalize by avg volume
    sum = sum/(vol/norm);}

  return sum/norm + background();
}

/**
 * Function to evaluate 2D SphereSLD function
 * @param q_x: value of Q along x
 * @param q_y: value of Q along y
 * @return: function value
 */
double SphereSLDModel :: operator()(double qx, double qy) {
  double q = sqrt(qx*qx + qy*qy);
  return (*this).operator()(q);
}

/**
 * Function to evaluate SphereSLD function
 * @param pars: parameters of the SphereSLD
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double SphereSLDModel :: evaluate_rphi(double q, double phi) {
  return (*this).operator()(q);
}

/**
 * Function to calculate TOTAL radius
 * ToDo: Find What is the effective radius for this model.
 * @return: effective radius value
 */
// No polydispersion supported in this model.
// Calculate max radius assumming max_radius = effective radius
// Note that this max radius is not affected by sld of layer, sld of interface, or
// sld of solvent.
double SphereSLDModel :: calculate_ER() {
  SphereSLDParameters dp;

  dp.n_shells = n_shells();

  dp.rad_core0 = rad_core0();
  dp.thick_flat1 = thick_flat1();
  dp.thick_flat2 = thick_flat2();
  dp.thick_flat3 = thick_flat3();
  dp.thick_flat4 = thick_flat4();
  dp.thick_flat5 = thick_flat5();
  dp.thick_flat6 = thick_flat6();
  dp.thick_flat7 = thick_flat7();
  dp.thick_flat8 = thick_flat8();
  dp.thick_flat9 = thick_flat9();
  dp.thick_flat10 = thick_flat10();

  dp.thick_inter0 = thick_inter0();
  dp.thick_inter1 = thick_inter1();
  dp.thick_inter2 = thick_inter2();
  dp.thick_inter3 = thick_inter3();
  dp.thick_inter4 = thick_inter4();
  dp.thick_inter5 = thick_inter5();
  dp.thick_inter6 = thick_inter6();
  dp.thick_inter7 = thick_inter7();
  dp.thick_inter8 = thick_inter8();
  dp.thick_inter9 = thick_inter9();
  dp.thick_inter10 = thick_inter10();

  double rad_out = 0.0;
  double out = 0.0;
  // Perform the computation, with all weight points
  double sum = 0.0;
  double norm = 0.0;

  // Get the dispersion points for the radius
  vector<WeightPoint> weights_rad_core0;
  rad_core0.get_weights(weights_rad_core0);

  // Get the dispersion points for the thick 1
  vector<WeightPoint> weights_thick_inter0;
  thick_inter0.get_weights(weights_thick_inter0);
  // Loop over radius weight points
  for(size_t i=0; i<weights_rad_core0.size(); i++) {
    dp.rad_core0 = weights_rad_core0[i].value;
    // Loop over radius weight points
    for(size_t j=0; j<weights_thick_inter0.size(); j++) {
      dp.thick_inter0 = weights_thick_inter0[j].value;
      rad_out = dp.rad_core0 + dp.thick_inter0;
      if (dp.n_shells > 0)
        rad_out += dp.thick_flat1 + dp.thick_inter1;
      if (dp.n_shells > 1)
        rad_out += dp.thick_flat2 + dp.thick_inter2;
      if (dp.n_shells > 2)
        rad_out += dp.thick_flat3 + dp.thick_inter3;
      if (dp.n_shells > 3)
        rad_out += dp.thick_flat4 + dp.thick_inter4;
      if (dp.n_shells > 4)
        rad_out += dp.thick_flat5 + dp.thick_inter5;
      if (dp.n_shells > 5)
        rad_out += dp.thick_flat6 + dp.thick_inter6;
      if (dp.n_shells > 6)
        rad_out += dp.thick_flat7 + dp.thick_inter7;
      if (dp.n_shells > 7)
        rad_out += dp.thick_flat8 + dp.thick_inter8;
      if (dp.n_shells > 8)
        rad_out += dp.thick_flat9 + dp.thick_inter9;
      if (dp.n_shells > 9)
        rad_out += dp.thick_flat10 + dp.thick_inter10;
      sum += weights_rad_core0[i].weight*weights_thick_inter0[j].weight
          * (rad_out);
      norm += weights_rad_core0[i].weight*weights_thick_inter0[j].weight;
    }
  }
  if (norm != 0){
    //return the averaged value
    out =  sum/norm;}
  else{
    //return normal value
    out = dp.rad_core0 + dp.thick_inter0;
    if (dp.n_shells > 0)
      out += dp.thick_flat1 + dp.thick_inter1;
    if (dp.n_shells > 1)
      out += dp.thick_flat2 + dp.thick_inter2;
    if (dp.n_shells > 2)
      out += dp.thick_flat3 + dp.thick_inter3;
    if (dp.n_shells > 3)
      out += dp.thick_flat4 + dp.thick_inter4;
    if (dp.n_shells > 4)
      out += dp.thick_flat5 + dp.thick_inter5;
    if (dp.n_shells > 5)
      out += dp.thick_flat6 + dp.thick_inter6;
    if (dp.n_shells > 6)
      out += dp.thick_flat7 + dp.thick_inter7;
    if (dp.n_shells > 7)
      out += dp.thick_flat8 + dp.thick_inter8;
    if (dp.n_shells > 8)
      out += dp.thick_flat9 + dp.thick_inter9;
    if (dp.n_shells > 9)
      out += dp.thick_flat10 + dp.thick_inter10;
  }

  return out;

}
double SphereSLDModel :: calculate_VR() {
  return 1.0;
}
