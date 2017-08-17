#include <math.h>
#include "invertor.h"
#include <memory.h>
#include <stdio.h>
#include <stdlib.h>

double pi = 3.1416;

/**
 * Deallocate memory
 */
void invertor_dealloc(Invertor_params *pars) {
	free(pars->x);
	free(pars->y);
	free(pars->err);
}

void invertor_init(Invertor_params *pars) {
	pars->d_max = 180;
	pars->q_min = -1.0;
	pars->q_max = -1.0;
	pars->est_bck = 0;
}


/**
 * P(r) of a sphere, for test purposes
 *
 * @param R: radius of the sphere
 * @param r: distance, in the same units as the radius
 * @return: P(r)
 */
double pr_sphere(double R, double r) {
    if (r <= 2.0*R) {
        return 12.0* pow(0.5*r/R, 2.0) * pow(1.0-0.5*r/R, 2.0) * ( 2.0 + 0.5*r/R );
    } else {
        return 0.0;
    }
}

/**
 * Orthogonal functions:
 * B(r) = 2r sin(pi*nr/d)
 *
 */
double ortho(double d_max, int n, double r) {
	return 2.0*r*sin(pi*n*r/d_max);
}

/**
 * Fourier transform of the nth orthogonal function
 *
 */
double ortho_transformed(double d_max, int n, double q) {
	return 8.0*pow(pi, 2.0)/q * d_max * n * pow(-1.0, n+1)
		*sin(q*d_max) / ( pow(pi*n, 2.0) - pow(q*d_max, 2.0) );
}

/**
 * Slit-smeared Fourier transform of the nth orthogonal function.
 * Smearing follows Lake, Acta Cryst. (1967) 23, 191.
 */
double ortho_transformed_smeared(double d_max, int n, double height, double width, double q, int npts) {
	double sum, y, z;
	int i, j, n_height, n_width;
	double count_w;
	double fnpts;
	sum = 0.0;
	fnpts = (float)npts-1.0;

	// Check for zero slit size
	n_height = (height>0) ? npts : 1;
	n_width  = (width>0)  ? npts : 1;

	count_w = 0.0;

	for(j=0; j<n_height; j++) {
		if(height>0){
			z = height/fnpts*(float)j;
		} else {
			z = 0.0;
		}

		for(i=0; i<n_width; i++) {
			if(width>0){
				y = -width/2.0+width/fnpts*(float)i;
			} else {
				y = 0.0;
			}
			if (((q-y)*(q-y)+z*z)<=0.0) continue;
			count_w += 1.0;
			sum += ortho_transformed(d_max, n, sqrt((q-y)*(q-y)+z*z));
		}
	}
	return sum/count_w;
}

/**
 * First derivative in of the orthogonal function dB(r)/dr
 *
 */
double ortho_derived(double d_max, int n, double r) {
    return 2.0*sin(pi*n*r/d_max) + 2.0*r*cos(pi*n*r/d_max);
}

/**
 * Scattering intensity calculated from the expansion.
 */
double iq(double *pars, double d_max, int n_c, double q) {
    double sum = 0.0;
	int i;
    for (i=0; i<n_c; i++) {
        sum += pars[i] * ortho_transformed(d_max, i+1, q);
    }
    return sum;
}

/**
 * Scattering intensity calculated from the expansion,
 * slit-smeared.
 */
double iq_smeared(double *pars, double d_max, int n_c, double height, double width, double q, int npts) {
    double sum = 0.0;
	int i;
    for (i=0; i<n_c; i++) {
        sum += pars[i] * ortho_transformed_smeared(d_max, i+1, height, width, q, npts);
    }
    return sum;
}

/**
 * P(r) calculated from the expansion.
 */
double pr(double *pars, double d_max, int n_c, double r) {
    double sum = 0.0;
	int i;
    for (i=0; i<n_c; i++) {
        sum += pars[i] * ortho(d_max, i+1, r);
    }
    return sum;
}

/**
 * P(r) calculated from the expansion, with errors
 */
void pr_err(double *pars, double *err, double d_max, int n_c,
		double r, double *pr_value, double *pr_value_err) {
    double sum = 0.0;
    double sum_err = 0.0;
    double func_value;
	int i;
    for (i=0; i<n_c; i++) {
    	func_value = ortho(d_max, i+1, r);
        sum += pars[i] * func_value;
        //sum_err += err[i]*err[i]*func_value*func_value;
        sum_err += err[i*n_c+i]*func_value*func_value;
    }
    *pr_value = sum;
    if (sum_err>0) {
    	*pr_value_err = sqrt(sum_err);
    } else {
    	*pr_value_err = sum;
    }
}

/**
 * dP(r)/dr calculated from the expansion.
 */
double dprdr(double *pars, double d_max, int n_c, double r) {
    double sum = 0.0;
	int i;
    for (i=0; i<n_c; i++) {
        sum += pars[i] * 2.0*(sin(pi*(i+1)*r/d_max) + pi*(i+1)*r/d_max * cos(pi*(i+1)*r/d_max));
    }
    return sum;
}

/**
 * regularization term calculated from the expansion.
 */
double reg_term(double *pars, double d_max, int n_c, int nslice) {
    double sum = 0.0;
    double r;
    double deriv;
	int i;
    for (i=0; i<nslice; i++) {
    	r = d_max/(1.0*nslice)*i;
    	deriv = dprdr(pars, d_max, n_c, r);
        sum += deriv*deriv;
    }
    return sum/(1.0*nslice)*d_max;
}

/**
 * regularization term calculated from the expansion.
 */
double int_p2(double *pars, double d_max, int n_c, int nslice) {
    double sum = 0.0;
    double r;
    double value;
	int i;
    for (i=0; i<nslice; i++) {
    	r = d_max/(1.0*nslice)*i;
    	value = pr(pars, d_max, n_c, r);
        sum += value*value;
    }
    return sum/(1.0*nslice)*d_max;
}

/**
 * Integral of P(r)
 */
double int_pr(double *pars, double d_max, int n_c, int nslice) {
    double sum = 0.0;
    double r;
    double value;
	int i;
    for (i=0; i<nslice; i++) {
    	r = d_max/(1.0*nslice)*i;
    	value = pr(pars, d_max, n_c, r);
        sum += value;
    }
    return sum/(1.0*nslice)*d_max;
}

/**
 * Get the number of P(r) peaks.
 */
int npeaks(double *pars, double d_max, int n_c, int nslice) {
    double r;
    double value;
	int i;
	double previous = 0.0;
	double slope    = 0.0;
	int count = 0;
    for (i=0; i<nslice; i++) {
    	r = d_max/(1.0*nslice)*i;
    	value = pr(pars, d_max, n_c, r);
    	if (previous<=value){
    		//if (slope<0) count += 1;
    		slope = 1;
    	} else {
    		//printf("slope -1");
    		if (slope>0) count += 1;
    		slope = -1;
    	}
    	previous = value;
    }
    return count;
}

/**
 * Get the fraction of the integral of P(r) over the whole range
 * of r that is above zero.
 * A valid P(r) is define as being positive for all r.
 */
double positive_integral(double *pars, double d_max, int n_c, int nslice) {
    double r;
    double value;
	int i;
	double sum_pos = 0.0;
	double sum = 0.0;

    for (i=0; i<nslice; i++) {
    	r = d_max/(1.0*nslice)*i;
    	value = pr(pars, d_max, n_c, r);
    	if (value>0.0) sum_pos += value;
    	sum += fabs(value);
    }
    return sum_pos/sum;
}

/**
 * Get the fraction of the integral of P(r) over the whole range
 * of r that is at least one sigma above zero.
 */
double positive_errors(double *pars, double *err, double d_max, int n_c, int nslice) {
    double r;
	int i;
	double sum_pos = 0.0;
	double sum = 0.0;
	double pr_val;
	double pr_val_err;

    for (i=0; i<nslice; i++) {
    	r = d_max/(1.0*nslice)*i;
    	pr_err(pars, err, d_max, n_c, r, &pr_val, &pr_val_err);
    	if (pr_val>pr_val_err) sum_pos += pr_val;
    	sum += fabs(pr_val);


    }
    return sum_pos/sum;
}

/**
 * R_g radius of gyration calculation
 *
 * R_g**2 = integral[r**2 * p(r) dr] /  (2.0 * integral[p(r) dr])
 */
double rg(double *pars, double d_max, int n_c, int nslice) {
    double sum_r2 = 0.0;
    double sum    = 0.0;
    double r;
    double value;
	int i;
    for (i=0; i<nslice; i++) {
    	r = d_max/(1.0*nslice)*i;
    	value = pr(pars, d_max, n_c, r);
        sum += value;
        sum_r2 += r*r*value;
    }
    return sqrt(sum_r2/(2.0*sum));
}
