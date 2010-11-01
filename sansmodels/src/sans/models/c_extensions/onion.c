/**
 * Scattering model for a onion
 */

#include <math.h>
#include "onion.h"
#include <stdio.h>
#include <stdlib.h>
// some details can be found in sld_cal.c
double so_kernel(double dp[], double q) {
	int n = dp[0];
	double scale = dp[1];
	double rad_core0 = dp[2];
	double sld_core0 = dp[3];
	double sld_solv = dp[4];
	double background = dp[5];
	double sld_out[n+2];
	double slope[n+2];
	double sld_in[n+2];
	double thick[n+2];
	double A[n+2];
	int fun_type[n+2];
	int i,j;

	for (i =1; i<=n; i++){
		sld_out[i] = dp[i+5];
		sld_in[i] = dp[i+15];
		A[i] = dp[i+25];
		thick[i] = dp[i+35];
		fun_type[i] = dp[i+45];
	}
	sld_out[0] = sld_core0;
	sld_out[n+1] = sld_solv;
	sld_in[0] = sld_core0;
	sld_in[n+1] = sld_solv;
	thick[0] = rad_core0;
	thick[n+1] = 1e+10;
	A[0] = 0.0;
	A[n+1] = 0.0;
	fun_type[0] = 0;
	fun_type[n+1] = 0;

    double bes,fun,alpha,f,vol,vol_pre,vol_sub,qr,r,contr,f2;
    double sign;
    double pi;

    pi = 4.0*atan(1.0);
    f = 0.0;
    r = 0.0;
    vol = 0.0;
    vol_pre = 0.0;
    vol_sub = 0.0;
    double r0 = 0.0;

    for (i =0; i<= n+1; i++){
    	if (thick[i] == 0.0){
    		continue;
    	}
    	if (fun_type[i]== 0 ){
    		slope[i] = 0.0;
    		A[i] = 0.0;
    	}
    	vol_pre = vol;
        switch(fun_type[i]){
            case 2 :
					r0 = r;
					if (A[i] == 0.0){
						slope[i] = 0.0;
					}
					else{
						slope[i] = (sld_out[i]-sld_in[i])/(exp(A[i])-1.0);
					}
                    for (j=0; j<2; j++){
                        if ( i == 0 && j == 0){
                            continue;
                            }
                        if (i == n+1 && j == 1){
                            continue;
                            }
                        if ( j == 1){
                            sign = 1.0;
                            r += thick[i];
                            }
                        else{
                            sign = -1.0;
                       		}
                        qr = q * r;
                        alpha = A[i] * r/thick[i];
                        fun = 0.0;
                        if(qr == 0.0){
                            fun = sign * 1.0;
                            bes = sign * 1.0;
                            }
                        else{
                            if (fabs(A[i]) > 0.0 ){
                                fun = 3.0 * ((alpha*alpha - qr * qr) * sin(qr) - 2.0 * alpha * qr * cos(qr))/ ((alpha * alpha + qr * qr) * (alpha * alpha + qr * qr) * qr);
                                fun = fun - 3.0 * (alpha * sin(qr) - qr * cos(qr)) / ((alpha * alpha + qr * qr) * qr);
                                fun = - sign *fun;
                                bes = sign * 3.0 * (sin(qr) - qr * cos(qr)) / (qr * qr * qr);
                                }
                            else {
                                fun = sign * 3.0 * (sin(qr) - qr * cos(qr)) / (qr * qr * qr);
                                bes = sign * 3.0 * (sin(qr) - qr * cos(qr)) / (qr * qr * qr);
                                }
                            }
                        contr = slope[i]*exp(A[i]*(r-r0)/thick[i]);

                        vol = 4.0 * pi / 3.0 * r * r * r;
                        //if (j == 1 && fabs(sld_in[i]-sld_solv) < 1e-04*fabs(sld_solv) && A[i]==0.0){
                        //	vol_sub += (vol_pre - vol);
                        //}
                        f += vol * (contr * (fun) + (sld_in[i]-slope[i]) * bes);
                        }
                        break;
            default :
						if (fun_type[i]==0){
							slope[i] = 0.0;
						}
						else{
							slope[i]= (sld_out[i] -sld_in[i])/thick[i];
						}
                        contr = sld_in[i]-slope[i]*r;
                        for (j=0; j<2; j++){
                            if ( i == 0 && j == 0){
                                continue;
                                }
                            if (i == n+1 && j == 1){
                                continue;
                                }
                            if ( j == 1){
                            	sign = 1.0;
                                r += thick[i];
                                }
                            else{
                            	sign = -1.0;
								}

                            qr = q * r;
                            fun = 0.0;
                            if(qr == 0.0){
                                bes = sign * 1.0;
                                }
                            else{
                                bes = sign *  3.0 * (sin(qr) - qr * cos(qr)) / (qr * qr * qr);
                                if (fabs(slope[i]) > 0.0 ){
                                    fun = sign * 3.0 * r * (2.0*qr*sin(qr)-((qr*qr)-2.0)*cos(qr))/(qr * qr * qr * qr);
                                    }
                                }
                            vol = 4.0 * pi / 3.0 * r * r * r;
                            //if (j == 1 && fabs(sld_in[i]-sld_solv) < 1e-04*fabs(sld_solv) && fun_type[i]==0){
                            //	vol_sub += (vol_pre - vol);
                            //}
                            f += vol * (bes * contr + fun * slope[i]);
                            }
                            break;
				}

        }
    //vol += vol_sub;
    f2 = f * f / vol * 1.0e8;
	f2 *= scale;
	f2 += background;
    return (f2);
}
/**
 * Function to evaluate 1D scattering function
 * @param pars: parameters of the sphere
 * @param q: q-value
 * @return: function value
 */
double onion_analytical_1D(OnionParameters *pars, double q) {
	double dp[56];

	dp[0] = pars->n_shells;
	dp[1] = pars->scale;
	dp[2] = pars->rad_core0;
	dp[3] = pars->sld_core0;
	dp[4] = pars->sld_solv;
	dp[5] = pars->background;

	dp[6] = pars->sld_out_shell1;
	dp[7] = pars->sld_out_shell2;
	dp[8] = pars->sld_out_shell3;
	dp[9] = pars->sld_out_shell4;
	dp[10] = pars->sld_out_shell5;
	dp[11] = pars->sld_out_shell6;
	dp[12] = pars->sld_out_shell7;
	dp[13] = pars->sld_out_shell8;
	dp[14] = pars->sld_out_shell9;
	dp[15] = pars->sld_out_shell10;

	dp[16] = pars->sld_in_shell1;
	dp[17] = pars->sld_in_shell2;
	dp[18] = pars->sld_in_shell3;
	dp[19] = pars->sld_in_shell4;
	dp[20] = pars->sld_in_shell5;
	dp[21] = pars->sld_in_shell6;
	dp[22] = pars->sld_in_shell7;
	dp[23] = pars->sld_in_shell8;
	dp[24] = pars->sld_in_shell9;
	dp[25] = pars->sld_in_shell10;

	dp[26] = pars->A_shell1;
	dp[27] = pars->A_shell2;
	dp[28] = pars->A_shell3;
	dp[29] = pars->A_shell4;
	dp[30] = pars->A_shell5;
	dp[31] = pars->A_shell6;
	dp[32] = pars->A_shell7;
	dp[33] = pars->A_shell8;
	dp[34] = pars->A_shell9;
	dp[35] = pars->A_shell10;

	dp[36] = pars->thick_shell1;
	dp[37] = pars->thick_shell2;
	dp[38] = pars->thick_shell3;
	dp[39] = pars->thick_shell4;
	dp[40] = pars->thick_shell5;
	dp[41] = pars->thick_shell6;
	dp[42] = pars->thick_shell7;
	dp[43] = pars->thick_shell8;
	dp[44] = pars->thick_shell9;
	dp[45] = pars->thick_shell10;

	dp[46] = pars->func_shell1;
	dp[47] = pars->func_shell2;
	dp[48] = pars->func_shell3;
	dp[49] = pars->func_shell4;
	dp[50] = pars->func_shell5;
	dp[51] = pars->func_shell6;
	dp[52] = pars->func_shell7;
	dp[53] = pars->func_shell8;
	dp[54] = pars->func_shell9;
	dp[55] = pars->func_shell10;

	return so_kernel(dp, q);
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the sphere
 * @param q: q-value
 * @return: function value
 */
double onion_analytical_2D(OnionParameters *pars, double q, double phi) {
	return onion_analytical_1D(pars,q);
}

double onion_analytical_2DXY(OnionParameters *pars, double qx, double qy){
	return onion_analytical_1D(pars,sqrt(qx*qx+qy*qy));
}
