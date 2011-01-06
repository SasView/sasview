// The original code, of which work was not DANSE funded,
// was provided by J. Cho.
/**
 * NR model Parratt method
 */
#include <math.h>
#include "refl_adv.h"
#include "libmultifunc/librefl.h"
#include <stdio.h>
#include <stdlib.h>

#define lamda 4.62


double re_adv_kernel(double dp[], double q) {
	int n = dp[0];
	int i,j,fun_type[n+2];

	double scale = dp[1];
	double thick_inter_sub = dp[2];
	double sld_sub = dp[4];
	double sld_super = dp[5];
	double background = dp[6];
	double npts = dp[69]; //number of sub_layers in each interface

	double sld[n+2],sld_im[n+2],thick_inter[n+2],thick[n+2],fun_coef[n+2],total_thick;
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

	double nsl=npts;//21.0; //nsl = Num_sub_layer:  MUST ODD number in double //no other number works now
	int n_s;

    double sld_i,sldim_i,dz,phi,R,ko2;
    double sign,erfunc;
    double pi;
	complex  inv_n,phi1,alpha,alpha2,kn,fnm,fnp,rn,Xn,nn,nn2,an,nnp1,one,zero,two,n_sub,n_sup,knp1,Xnp1;
	pi = 4.0*atan(1.0);
    one = cassign(1.0,0.0);
	//zero = cassign(0.0,0.0);
	two= cassign(0.0,-2.0);

	//Checking if floor is available.
	//no imaginary sld inputs in this function yet
    n_sub=cassign(1.0-sld_sub*pow(lamda,2.0)/(2.0*pi),pow(lamda,2.0)/(2.0*pi)*sld_im[0]);
    n_sup=cassign(1.0-sld_super*pow(lamda,2.0)/(2.0*pi),pow(lamda,2.0)/(2.0*pi)*sld_im[n+1]);
    ko2 = pow(2.0*pi/lamda,2.0);

    phi = asin(lamda*q/(4.0*pi));
    phi1 = cdiv(rcmult(phi,one),n_sup);
    alpha = cmult(n_sup,ccos(phi1));
	alpha2 = cmult(alpha,alpha);

    nnp1=n_sub;
    knp1=csqrt(rcmult(ko2,csub(cmult(nnp1,nnp1),alpha2)));  //nnp1*ko*sin(phinp1)
    Xnp1=cassign(0.0,0.0);
    dz = 0.0;
    // iteration for # of layers +sub from the top
    for (i=1;i<=n+1; i++){
    	//if (fun_coef[i]==0.0)
    	//	// this condition protects an error in numerical multiplication
    	//	fun_coef[i] = 1e-14;
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
				nn2=cmult(nn,nn);

				kn=csqrt(rcmult(ko2,csub(nn2,alpha2)));        //nn*ko*sin(phin)
				an=cexp(rcmult(dz,cmult(two,kn)));

				fnm=csub(kn,knp1);
				fnp=cadd(kn,knp1);
				rn=cdiv(fnm,fnp);
				Xn=cmult(an,cdiv(cadd(rn,Xnp1),cadd(one,cmult(rn,Xnp1))));    //Xn=an*((rn+Xnp1*anp1)/(1+rn*Xnp1*anp1))

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

    return R;

}

/**
 * Function to evaluate NR function
 * @param pars: parameters of refl
 * @param q: q-value
 * @return: function value
 */

double refl_adv_analytical_1D(ReflAdvParameters *pars, double q) {
	double dp[71];

	dp[0] = pars->n_layers;
	dp[1] = pars->scale;
	dp[2] = pars->thick_inter0;
	dp[3] = pars->func_inter0;
	dp[4] = pars->sld_bottom0;
	dp[5] = pars->sld_medium;
	dp[6] = pars->background;

	dp[7] = pars->sld_flat1;
	dp[8] = pars->sld_flat2;
	dp[9] = pars->sld_flat3;
	dp[10] = pars->sld_flat4;
	dp[11] = pars->sld_flat5;
	dp[12] = pars->sld_flat6;
	dp[13] = pars->sld_flat7;
	dp[14] = pars->sld_flat8;
	dp[15] = pars->sld_flat9;
	dp[16] = pars->sld_flat10;

	dp[17] = pars->thick_inter1;
	dp[18] = pars->thick_inter2;
	dp[19] = pars->thick_inter3;
	dp[20] = pars->thick_inter4;
	dp[21] = pars->thick_inter5;
	dp[22] = pars->thick_inter6;
	dp[23] = pars->thick_inter7;
	dp[24] = pars->thick_inter8;
	dp[25] = pars->thick_inter9;
	dp[26] = pars->thick_inter10;

	dp[27] = pars->thick_flat1;
	dp[28] = pars->thick_flat2;
	dp[29] = pars->thick_flat3;
	dp[30] = pars->thick_flat4;
	dp[31] = pars->thick_flat5;
	dp[32] = pars->thick_flat6;
	dp[33] = pars->thick_flat7;
	dp[34] = pars->thick_flat8;
	dp[35] = pars->thick_flat9;
	dp[36] = pars->thick_flat10;

	dp[37] = pars->func_inter1;
	dp[38] = pars->func_inter2;
	dp[39] = pars->func_inter3;
	dp[40] = pars->func_inter4;
	dp[41] = pars->func_inter5;
	dp[42] = pars->func_inter6;
	dp[43] = pars->func_inter7;
	dp[44] = pars->func_inter8;
	dp[45] = pars->func_inter9;
	dp[46] = pars->func_inter10;

	dp[47] = pars->sldIM_flat1;
	dp[48] = pars->sldIM_flat2;
	dp[49] = pars->sldIM_flat3;
	dp[50] = pars->sldIM_flat4;
	dp[51] = pars->sldIM_flat5;
	dp[52] = pars->sldIM_flat6;
	dp[53] = pars->sldIM_flat7;
	dp[54] = pars->sldIM_flat8;
	dp[55] = pars->sldIM_flat9;
	dp[56] = pars->sldIM_flat10;

	dp[57] = pars->nu_inter1;
	dp[58] = pars->nu_inter2;
	dp[59] = pars->nu_inter3;
	dp[60] = pars->nu_inter4;
	dp[61] = pars->nu_inter5;
	dp[62] = pars->nu_inter6;
	dp[63] = pars->nu_inter7;
	dp[64] = pars->nu_inter8;
	dp[65] = pars->nu_inter9;
	dp[66] = pars->nu_inter10;

	dp[67] = pars->sldIM_sub0;
	dp[68] = pars->sldIM_medium;
	dp[69] = pars->npts_inter;
	dp[70] = pars->nu_inter0;

	return re_adv_kernel(dp, q);
}

/**
 * Function to evaluate NR function
 * @param pars: parameters of NR
 * @param q: q-value
 * @return: function value
 */
double refl_adv_analytical_2D(ReflAdvParameters *pars, double q, double phi) {
	return refl_adv_analytical_1D(pars,q);
}

double refl_adv_analytical_2DXY(ReflAdvParameters *pars, double qx, double qy){
	return refl_adv_analytical_1D(pars,sqrt(qx*qx+qy*qy));
}
