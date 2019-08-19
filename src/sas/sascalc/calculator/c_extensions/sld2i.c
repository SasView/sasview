/**
Computes the (magnetic) scattering form sld (n and m) profile
 */
#include <stdio.h>
#include <math.h>
#include "sld2i.h"
#include "libfunc.h"
#include "librefl.h"
#include <stdlib.h>
#include<time.h>

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
void initGenI(GenI* this, int is_avg, int npix, double* x, double* y, double* z, double* sldn,
			double* mx, double* my, double* mz, double* voli,
			double in_spin, double out_spin,
			double s_theta) {
	this->is_avg = is_avg;
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
}

/**
 * Compute 2D anisotropic
 */
void genicomXY(GenI* this, int npoints, double *qx, double *qy, double *I_out){
	//npoints is given negative for angular averaging
	// Assumes that q doesn't have qz component and sld_n is all real
	//double q = 0.0;
	//double Pi = 4.0*atan(1.0);
	polar_sld b_sld;
	double qr = 0.0;
	Cplx iqr;
	Cplx ephase;
	Cplx comp_sld;

	Cplx sumj_uu;
	Cplx sumj_ud;
	Cplx sumj_du;
	Cplx sumj_dd;
	Cplx temp_fi;

	double count = 0.0;
	int i, j;

	cassign(&iqr, 0.0, 0.0);
	cassign(&ephase, 0.0, 0.0);
	cassign(&comp_sld, 0.0, 0.0);

	//Assume that pixel volumes are given in vol_pix in A^3 unit
	//int x_size = 0; //in Ang
	//int y_size = 0; //in Ang
	//int z_size = 0; //in Ang

	// Loop over q-values and multiply apply matrix

	//printf("npoints: %d, npix: %d\n", npoints, this->n_pix);
	for(i=0; i<npoints; i++){
		//I_out[i] = 0.0;
		cassign(&sumj_uu, 0.0, 0.0);
		cassign(&sumj_ud, 0.0, 0.0);
		cassign(&sumj_du, 0.0, 0.0);
		cassign(&sumj_dd, 0.0, 0.0);
		//printf("i: %d\n", i);
		//q = sqrt(qx[i]*qx[i] + qy[i]*qy[i]); // + qz[i]*qz[i]);

		for(j=0; j<this->n_pix; j++){
			if (this->sldn_val[j]!=0.0
				||this->mx_val[j]!=0.0
				||this->my_val[j]!=0.0
				||this->mz_val[j]!=0.0)
			{
			    // printf("i,j: %d,%d\n", i,j);
				//anisotropic
				cassign(&temp_fi, 0.0, 0.0);
				cal_msld(&b_sld, 0, qx[i], qy[i], this->sldn_val[j],
							 this->mx_val[j], this->my_val[j], this->mz_val[j],
			 				 this->inspin, this->outspin, this->stheta);
				qr = (qx[i]*this->x_val[j] + qy[i]*this->y_val[j]);
				cassign(&iqr, 0.0, qr);
				cplx_exp(&ephase, iqr);

				//Let's multiply pixel(atomic) volume here
				rcmult(&ephase, this->vol_pix[j], ephase);
				//up_up
				if (this->inspin > 0.0 && this->outspin > 0.0){
					cassign(&comp_sld, b_sld.uu, 0.0);
					cplx_mult(&temp_fi, comp_sld, ephase);
					cplx_add(&sumj_uu, sumj_uu, temp_fi);
				}
				//down_down
				if (this->inspin < 1.0 && this->outspin < 1.0){
					cassign(&comp_sld, b_sld.dd, 0.0);
					cplx_mult(&temp_fi, comp_sld, ephase);
					cplx_add(&sumj_dd, sumj_dd, temp_fi);
				}
				//up_down
				if (this->inspin > 0.0 && this->outspin < 1.0){
					cassign(&comp_sld, b_sld.re_ud, b_sld.im_ud);
					cplx_mult(&temp_fi, comp_sld, ephase);
					cplx_add(&sumj_ud, sumj_ud, temp_fi);
				}
				//down_up
				if (this->inspin < 1.0 && this->outspin > 0.0){
					cassign(&comp_sld, b_sld.re_du, b_sld.im_du);
					cplx_mult(&temp_fi, comp_sld, ephase);
					cplx_add(&sumj_du, sumj_du, temp_fi);
				}

				if (i == 0){
					count += this->vol_pix[j];
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
	//printf("count = %d %g %g %g %g\n", count, this->sldn_val[0],this->mx_val[0], this->my_val[0], this->mz_val[0]);
}
/**
 * Compute 1D isotropic
 * Isotropic: Assumes all slds are real (no magnetic)
 * Also assumes there is no polarization: No dependency on spin
 */
void genicom(GenI* this, int npoints, double *q, double *I_out){
	//npoints is given negative for angular averaging
	// Assumes that q doesn't have qz component and sld_n is all real
	//double Pi = 4.0*atan(1.0);
	double qr = 0.0;
	double sumj;
	double sld_j = 0.0;
	double count = 0.0;
	int i, j, k;

	//Assume that pixel volumes are given in vol_pix in A^3 unit
	// Loop over q-values and multiply apply matrix
	for(i=0; i<npoints; i++){
		sumj =0.0;
		for(j=0; j<this->n_pix; j++){
			//Isotropic: Assumes all slds are real (no magnetic)
			//Also assumes there is no polarization: No dependency on spin
			if (this->is_avg == 1){
				// approximation for a spherical symmetric particle
				qr = sqrt(this->x_val[j]*this->x_val[j]+this->y_val[j]*this->y_val[j]+this->z_val[j]*this->z_val[j])*q[i];
				if (qr > 0.0){
					qr = sin(qr) / qr;
					sumj += this->sldn_val[j] * this->vol_pix[j] * qr;
				}
				else{
					sumj += this->sldn_val[j] * this->vol_pix[j];
				}
			}
			else{
				//full calculation
				//pragma omp parallel for
				for(k=0; k<this->n_pix; k++){
					sld_j =  this->sldn_val[j] * this->sldn_val[k] * this->vol_pix[j] * this->vol_pix[k];
					qr = (this->x_val[j]-this->x_val[k])*(this->x_val[j]-this->x_val[k])+
						      (this->y_val[j]-this->y_val[k])*(this->y_val[j]-this->y_val[k])+
						      (this->z_val[j]-this->z_val[k])*(this->z_val[j]-this->z_val[k]);
					qr = sqrt(qr) * q[i];
					if (qr > 0.0){
						sumj += sld_j*sin(qr)/qr;
					}
					else{
						sumj += sld_j;
					}
				}
			}
			if (i == 0){
				count += this->vol_pix[j];
			}
		}
		I_out[i] = sumj;
		if (this->is_avg == 1) {
			I_out[i] *= sumj;
		}
		I_out[i] *= (1.0E+8 / count); //in cm (unit) / number; //to be multiplied by vol_pix
	}
	//printf("count = %d %g %g %g %g\n", count, sldn_val[0],mx_val[0], my_val[0], mz_val[0]);
}

int main() {
	int is_avg = 0;
	int npix = 301;
	double* x = malloc(npix * sizeof(double));
	double* y = malloc(npix * sizeof(double));
	double* z = malloc(npix * sizeof(double));
	double* sldn = malloc(npix * sizeof(double));
	double* mx = malloc(npix * sizeof(double));
	double* my = malloc(npix * sizeof(double));
	double* mz = malloc(npix * sizeof(double));
	double* voli = malloc(npix * sizeof(double));
	double* q = malloc(npix * sizeof(double));

	double in_spin = 0.5;
	double out_spin = 0.2;
	double s_theta = 0.1;

	double lin_space = 0.4 / (npix-1);
	double start = 0.1;

	int i = 0;
	for(i = 0; i < npix; i++) {
		x[i] = start + (lin_space * i);
		y[i] = start + (lin_space * i);
		z[i] = start + (lin_space * i);
		sldn[i] = start + (lin_space * i);
		mx[i] = start + (lin_space * i);
		my[i] = start + (lin_space * i);
		mz[i] = start + (lin_space * i);
		voli[i] = start + (lin_space * i);
		q[i] = start + (lin_space * i);
	}

	GenI* obj = malloc(sizeof(GenI));
	//printf("Test: %d", obj->is_avg);

	/*GenI* this, int is_avg, int npix, double* x, double* y, double* z, double* sldn,
			double* mx, double* my, double* mz, double* voli,
			double in_spin, double out_spin,
			double s_theta*/
	initGenI(obj, is_avg, npix, x, y, z, sldn, mx, my, mz, voli, in_spin, out_spin, s_theta);

	int npoints = 301;

	double* I_out = malloc(301 * sizeof(double));
	genicom(obj, npoints, q, I_out);
	double time_spent = 0.0;
	i = 0;
	int trials = 10;

	for(i = 0; i < trials; i++) {
		clock_t begin = clock();
		genicom(obj, npoints, q, I_out);
		clock_t end = clock();

		time_spent = (double)(end - begin) / CLOCKS_PER_SEC;

		printf("Time elapsed is %f seconds", time_spent);
	}
	i = 0;

	for(i = 0; i < npoints; i++) {
		printf("%e ", I_out[i]);
		if(i % 4 == 0) {
			printf("\n");
		}
	}

	free(obj);
	free(x);
	free(y);
	free(z);
	free(sldn);
	free(mx);
	free(my);
	free(mx);
	free(voli);
	free(I_out);
	free(q);
}
