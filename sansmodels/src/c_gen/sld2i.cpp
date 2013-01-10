/**
Computes the (magnetic) scattering form sld (n and m) profile
 */
#include "sld2i.hh"
#include <stdio.h>
#include <math.h>
using namespace std;
extern "C" {
	#include "libmultifunc/libfunc.h"
	#include "libmultifunc/librefl.h"
}
/**
 * Constructor for GenI
 *
 * binning
 * //@param qx: array of Qx values
 * //@param qy: array of Qy values
 * //@param qz: array of Qz values
 * @param x: array of x values
 * @param y: array of y values
 * @param z: array of z values
 * @param sldn: array of sld n
 * @param mx: array of sld mx
 * @param my: array of sld my
 * @param mz: array of sld mz
 * @param in_spin: ratio of up spin in Iin
 * @param out_spin: ratio of up spin in Iout
 * @param s_theta: angle (from x-axis) of the up spin in degree
 */
GenI :: GenI(int npix, double* x, double* y, double* z, double* sldn,
			double* mx, double* my, double* mz, double* voli,
			double in_spin, double out_spin,
			double s_theta) {
	//this->qx_val = qx;
	//this->qy_val = qy;
	//this->qz_val = qz;
	this->n_pix = npix;
	this->x_val = x;
	this->y_val = y;
	this->z_val = z;
	this->sldn_val = sldn;
	this->mx_val = mx;
	this->my_val = my;
	this->mz_val = mz;
	this->vol_pix = voli;
	this->inspin = in_spin;
	this->outspin = out_spin;
	this->stheta = s_theta;
};

/**
 * Compute
 */
void GenI :: genicom(int npoints, double *qx, double *qy, double *I_out){
	// Assumes that q doesn't have qz component and sld_n is all real
	double q = 0.0;
	//double Pi = 4.0*atan(1.0);
	polar_sld b_sld;
	double qr = 0.0;
	complex iqr = cassign(0.0, 0.0);
	complex ephase = cassign(0.0, 0.0);
	complex comp_sld = cassign(0.0, 0.0);
	complex sumj;
	complex sumj_uu;
	complex sumj_ud;
	complex sumj_du;
	complex sumj_dd;
	complex temp_fi;

	double count = 0.0;
	//Assume that pixel volumes are given in vol_pix in A^3 unit
	//int x_size = 0; //in Ang
	//int y_size = 0; //in Ang
	//int z_size = 0; //in Ang
	// Loop over q-values and multiply apply matrix

	for(int i=0; i<npoints; i++){
		//I_out[i] = 0.0;
		sumj = cassign(0.0, 0.0);
		sumj_uu = cassign(0.0, 0.0);
		sumj_ud = cassign(0.0, 0.0);
		sumj_du = cassign(0.0, 0.0);
		sumj_dd = cassign(0.0, 0.0);		
		//printf ("%d ", i);
		q = sqrt(qx[i]*qx[i] + qy[i]*qy[i]); // + qz[i]*qz[i]);

		for(int j=0; j<n_pix; j++){
			
			if (sldn_val[j]!=0.0||mx_val[j]!=0.0||my_val[j]!=0.0||mz_val[j]!=0.0)
			{	
				temp_fi = cassign(0.0, 0.0);
				b_sld = cal_msld(0, qx[i], qy[i], sldn_val[j],
								 mx_val[j], my_val[j], mz_val[j],
				 				 inspin, outspin, stheta);
				qr = (qx[i]*x_val[j] + qy[i]*y_val[j]);
				iqr = cassign(0.0, qr);
				ephase = cplx_exp(iqr);
				//up_up
				if (inspin > 0.0 && outspin > 0.0){
					comp_sld = cassign(b_sld.uu, 0.0);
					temp_fi = cplx_mult(comp_sld, ephase);
					temp_fi = rcmult(vol_pix[j],temp_fi);
					sumj_uu = cplx_add(sumj_uu, temp_fi);
					}
				//down_down
				if (inspin < 1.0 && outspin < 1.0){
					comp_sld = cassign(b_sld.dd, 0.0);
					temp_fi = cplx_mult(comp_sld, ephase);
					temp_fi = rcmult(vol_pix[j],temp_fi);
					sumj_dd = cplx_add(sumj_dd, temp_fi);
					}
				//up_down
				if (inspin > 0.0 && outspin < 1.0){
					comp_sld = cassign(b_sld.re_ud, b_sld.im_ud);
					temp_fi = cplx_mult(comp_sld, ephase);
					temp_fi = rcmult(vol_pix[j],temp_fi);
					sumj_ud = cplx_add(sumj_ud, temp_fi);
					}
				//down_up
				if (inspin < 1.0 && outspin > 0.0){
					comp_sld = cassign(b_sld.re_du, b_sld.im_du);
					temp_fi = cplx_mult(comp_sld, ephase);
					temp_fi = rcmult(vol_pix[j],temp_fi);
					sumj_du = cplx_add(sumj_du, temp_fi);
					}
				if (i == 0){
					count += vol_pix[j];
				}
			}
		}
		//printf("aa%d=%g %g %d\n", i, (sumj_uu.re*sumj_uu.re + sumj_uu.im*sumj_uu.im), (sumj_dd.re*sumj_dd.re + sumj_dd.im*sumj_dd.im), count);
		I_out[i] = (sumj_uu.re*sumj_uu.re + sumj_uu.im*sumj_uu.im);
		I_out[i] += (sumj_ud.re*sumj_ud.re + sumj_ud.im*sumj_ud.im);
		I_out[i] += (sumj_du.re*sumj_du.re + sumj_du.im*sumj_du.im);
		I_out[i] += (sumj_dd.re*sumj_dd.re + sumj_dd.im*sumj_dd.im);
		I_out[i] *= (1.0E+8 / count); //in cm (unit) / number; //to be multiplied by vol_pix
	}
	//printf ("count = %d %g %g %g %g\n", count, sldn_val[0],mx_val[0], my_val[0], mz_val[0]);
}
