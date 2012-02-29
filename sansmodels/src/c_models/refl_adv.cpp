
#include <math.h>
#include "parameters.hh"
#include <stdio.h>
#include <stdlib.h>
#include "refl_adv.h"

extern "C" {
#include "libmultifunc/librefl.h"
}

using namespace std;

#define lamda 4.62


double re_adv_kernel(double dp[], double q) {
  int n = dp[0];
  int i,j;
  double nsl;

  double scale = dp[1];
  double thick_inter_sub = dp[2];
  double sld_sub = dp[4];
  double sld_super = dp[5];
  double background = dp[6];
  double npts = dp[69]; //number of sub_layers in each interface

  double total_thick=0.0;

  int n_s;
  double sld_i,sldim_i,dz,phi,R,ko2;
  double pi;

  int* fun_type;
  double* sld;
  double* sld_im;
  double* thick_inter;
  double* thick;
  double* fun_coef;
  complex  phi1,alpha,alpha2,kn,fnm,fnp,rn,Xn,nn,nn2,an,nnp1,one,two,n_sub,n_sup,knp1,Xnp1;

  fun_type = (int*)malloc((n+2)*sizeof(int));
  sld = (double*)malloc((n+2)*sizeof(double));
  sld_im = (double*)malloc((n+2)*sizeof(double));
  thick_inter = (double*)malloc((n+2)*sizeof(double));
  thick = (double*)malloc((n+2)*sizeof(double));
  fun_coef = (double*)malloc((n+2)*sizeof(double));

  fun_type[0] = dp[3];
  fun_coef[0] = fabs(dp[70]);
  for (i =1; i<=n; i++){
    sld[i] = dp[i+6];
    thick_inter[i]= dp[i+16];
    thick[i] = dp[i+26];
    fun_type[i] = dp[i+36];
    sld_im[i] = dp[i+46];
    fun_coef[i] = fabs(dp[i+56]);
    //printf("type_func2 =%g\n",fun_coef[i]);

    total_thick += thick[i] + thick_inter[i];
  }
  sld[0] = sld_sub;
  sld[n+1] = sld_super;
  sld_im[0] = fabs(dp[1+66]);
  sld_im[n+1] = fabs(dp[2+66]);
  thick[0] = total_thick/5.0;
  thick[n+1] = total_thick/5.0;
  thick_inter[0] = thick_inter_sub;
  thick_inter[n+1] = 0.0;
  fun_coef[n+1] = 0.0;

  nsl=npts;//21.0; //nsl = Num_sub_layer:  MUST ODD number in double //no other number works now

  pi = 4.0*atan(1.0);
  one = cassign(1.0,0.0);
  Xn = cassign(0.0,0.0);
  two = cassign(0.0,-2.0);

  //Checking if floor is available.
  //no imaginary sld inputs in this function yet
  n_sub=cassign(1.0-sld_sub*pow(lamda,2.0)/(2.0*pi),pow(lamda,2.0)/(2.0*pi)*sld_im[0]);
  n_sup=cassign(1.0-sld_super*pow(lamda,2.0)/(2.0*pi),pow(lamda,2.0)/(2.0*pi)*sld_im[n+1]);
  ko2 = pow(2.0*pi/lamda,2.0);

  phi = asin(lamda*q/(4.0*pi));
  phi1 = cplx_div(rcmult(phi,one),n_sup);
  alpha = cplx_mult(n_sup,cplx_cos(phi1));
  alpha2 = cplx_mult(alpha,alpha);

  nnp1=n_sub;
  knp1=cplx_sqrt(rcmult(ko2,cplx_sub(cplx_mult(nnp1,nnp1),alpha2)));  //nnp1*ko*sin(phinp1)
  Xnp1=cassign(0.0,0.0);
  dz = 0.0;
  // iteration for # of layers +sub from the top
  for (i=1;i<=n+1; i++){
    //if (fun_coef[i]==0.0)
    //  // this condition protects an error in numerical multiplication
    //  fun_coef[i] = 1e-14;
    //iteration for 9 sub-layers
    for (j=0;j<2;j++){
      for (n_s=0;n_s<nsl; n_s++){
        // for flat layer
        if (j==1){
          if (i==n+1)
            break;
          dz = thick[i];
          sld_i = sld[i];
          sldim_i = sld_im[i];
        }
        // for interface
        else{
          dz = thick_inter[i-1]/nsl;
          if (sld[i-1] == sld[i]){
            sld_i = sld[i];
          }
          else{
            sld_i = intersldfunc(fun_type[i-1],nsl, n_s+0.5, fun_coef[i-1], sld[i-1], sld[i]);
          }
          if (sld_im[i-1] == sld_im[i]){
            sldim_i = sld_im[i];
          }
          else{
            sldim_i = intersldfunc(fun_type[i-1],nsl, n_s+0.5, fun_coef[i-1], sld_im[i-1], sld_im[i]);
          }
        }
        nn = cassign(1.0-sld_i*pow(lamda,2.0)/(2.0*pi),pow(lamda,2.0)/(2.0*pi)*sldim_i);
        nn2=cplx_mult(nn,nn);

        kn=cplx_sqrt(rcmult(ko2,cplx_sub(nn2,alpha2)));        //nn*ko*sin(phin)
        an=cplx_exp(rcmult(dz,cplx_mult(two,kn)));

        fnm=cplx_sub(kn,knp1);
        fnp=cplx_add(kn,knp1);
        rn=cplx_div(fnm,fnp);
        Xn=cplx_mult(an,cplx_div(cplx_add(rn,Xnp1),cplx_add(one,cplx_mult(rn,Xnp1))));    //Xn=an*((rn+Xnp1*anp1)/(1+rn*Xnp1*anp1))

        Xnp1=Xn;
        knp1=kn;
        // no for-loop for flat layer
        if (j==1)
          break;
      }
    }
  }
  R=pow(Xn.re,2.0)+pow(Xn.im,2.0);
  // This temperarily fixes the total reflection for Rfunction and linear.
  // ToDo: Show why it happens that Xn.re=0 and Xn.im >1!
  if (Xn.im == 0.0 || R > 1){
    R=1.0;
  }
  R *= scale;
  R += background;

  free(fun_type);
  free(sld);
  free(sld_im);
  free(thick_inter);
  free(thick);
  free(fun_coef);

  return R;

}
ReflAdvModel :: ReflAdvModel() {
  n_layers = Parameter(1.0);
  scale = Parameter(1.0);
  thick_inter0 = Parameter(1.0);
  func_inter0 = Parameter(0);
  sld_bottom0 = Parameter(2.07e-06);
  sld_medium = Parameter(1.0e-06);
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


  thick_flat1 = Parameter(15.0);
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

  sldIM_flat1 = Parameter(0);
  sldIM_flat2 = Parameter(0);
  sldIM_flat3 = Parameter(0);
  sldIM_flat4 = Parameter(0);
  sldIM_flat5 = Parameter(0);
  sldIM_flat6 = Parameter(0);
  sldIM_flat7 = Parameter(0);
  sldIM_flat8 = Parameter(0);
  sldIM_flat9 = Parameter(0);
  sldIM_flat10 = Parameter(0);

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

  sldIM_sub0 = Parameter(0.0);
  sldIM_medium = Parameter(0.0);
  npts_inter = Parameter(21.0);
  nu_inter0 = Parameter(2.5);
}

/**
 * Function to evaluate 1D NR function
 * @param q: q-value
 * @return: function value
 */
double ReflAdvModel :: operator()(double q) {
  double dp[71];
  // Fill parameter array for IGOR library
  // Add the background after averaging
  dp[0] = n_layers();
  dp[1] = scale();
  dp[2] = thick_inter0();
  dp[3] = func_inter0();
  dp[4] = sld_bottom0();
  dp[5] = sld_medium();
  dp[6] = background();

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

  dp[47] = sldIM_flat1();
  dp[48] = sldIM_flat2();
  dp[49] = sldIM_flat3();
  dp[50] = sldIM_flat4();
  dp[51] = sldIM_flat5();
  dp[52] = sldIM_flat6();
  dp[53] = sldIM_flat7();
  dp[54] = sldIM_flat8();
  dp[55] = sldIM_flat9();
  dp[56] = sldIM_flat10();

  dp[57] = nu_inter1();
  dp[58] = nu_inter2();
  dp[59] = nu_inter3();
  dp[60] = nu_inter4();
  dp[61] = nu_inter5();
  dp[62] = nu_inter6();
  dp[63] = nu_inter7();
  dp[64] = nu_inter8();
  dp[65] = nu_inter9();
  dp[66] = nu_inter10();

  dp[67] = sldIM_sub0();
  dp[68] = sldIM_medium();
  dp[69] = npts_inter();
  dp[70] = nu_inter0();
  // Get the dispersion points for the radius
  //vector<WeightPoint> weights_thick;
  //thick_inter0.get_weights(weights_thick_inter0);


  return re_adv_kernel(dp,q);
}

/**
 * Function to evaluate 2D NR function
 * @param q_x: value of Q along x
 * @param q_y: value of Q along y
 * @return: function value
 */
double ReflAdvModel :: operator()(double qx, double qy) {
  // For 2D set qy as q, ignoring qx.
  double q = qy;//sqrt(qx*qx + qy*qy);
  if (q < 0.0){
    return 0.0;
  }
  return (*this).operator()(q);
}

/**
 * Function to evaluate 2D NR function
 * @param pars: parameters of the sphere
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double ReflAdvModel :: evaluate_rphi(double q, double phi) {
  return (*this).operator()(q);
}

/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double ReflAdvModel :: calculate_ER() {
  //NOT implemented yet!!!
  return 0.0;
}
double ReflAdvModel :: calculate_VR() {
  return 1.0;
}
