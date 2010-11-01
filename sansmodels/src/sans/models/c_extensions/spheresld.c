/**
 * spheresld model
 */
#include <math.h>
#include "spheresld.h"
#include "libmultifunc/librefl.h"
#include <stdio.h>
#include <stdlib.h>

#define lamda 4.62


double sphere_sld_kernel(double dp[], double q) {
	int n = dp[0];
	int i,j,k,fun_type[n+2];

	double scale = dp[1];
	double thick_inter_core = dp[2];
	double sld_core = dp[4];
	double sld_solv = dp[5];
	double background = dp[6];
	double npts = dp[57]; //number of sub_layers in each interface

	double sld[n+2],thick_inter[n+2],thick[n+2],fun_coef[n+2],total_thick;
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

	double nsl=npts;//21.0; //nsl = Num_sub_layer:  MUST ODD number in double //no other number works now
	int n_s;
	int floor_nsl;

    double sld_i,sld_f,dz,bes,fun,f,vol,vol_pre,vol_sub,qr,r,contr,f2;
    double sign,slope=0.0;
    double pi;

    pi = 4.0*atan(1.0);
    f = 0.0;
    r = 0.0;
    vol = 0.0;
    vol_pre = 0.0;
    vol_sub = 0.0;
    sld_f = sld_core;
    double r0 = 0.0, thick_inter_f;

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
					//	vol_sub += (vol_pre - vol);
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
    return (f2);
}

/**
 * Function to evaluate spheresld function
 * @param pars: parameters of spheresld
 * @param q: q-value
 * @return: function value
 */

double sphere_sld_analytical_1D(SphereSLDParameters *pars, double q) {
	double dp[60];

	dp[0] = pars->n_shells;
	dp[1] = pars->scale;
	dp[2] = pars->thick_inter0;
	dp[3] = pars->func_inter0;
	dp[4] = pars->sld_core0;
	dp[5] = pars->sld_solv;
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

	dp[47] = pars->nu_inter1;
	dp[48] = pars->nu_inter2;
	dp[49] = pars->nu_inter3;
	dp[50] = pars->nu_inter4;
	dp[51] = pars->nu_inter5;
	dp[52] = pars->nu_inter6;
	dp[53] = pars->nu_inter7;
	dp[54] = pars->nu_inter8;
	dp[55] = pars->nu_inter9;
	dp[56] = pars->nu_inter10;

	dp[57] = pars->npts_inter;
	dp[58] = pars->nu_inter0;
	dp[59] = pars->rad_core0;

	return sphere_sld_kernel(dp, q);
}

/**
 * Function to evaluate spheresld function
 * @param pars: parameters of spheresld
 * @param q: q-value
 * @return: function value
 */
double sphere_sld_analytical_2D(SphereSLDParameters *pars, double q, double phi) {
	return sphere_sld_analytical_1D(pars,q);
}

double sphere_sld_analytical_2DXY(SphereSLDParameters *pars, double qx, double qy){
	return sphere_sld_analytical_1D(pars,sqrt(qx*qx+qy*qy));
}
