#include <math.h>
#include "invertor.h"

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
        sum_err += err[i]*err[i]*func_value*func_value;
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
double reg_term(double *pars, double d_max, int n_c) {
    double sum = 0.0; 
    double r;
    double deriv;
	int i;
    for (i=0; i<25; i++) {
    	r = d_max/25.0*i;
    	deriv = dprdr(pars, d_max, n_c, r);
        sum += deriv*deriv;
    }
    return sum/25.0*d_max;
}

