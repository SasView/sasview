/**
 * Straight C disperser
 * 
 * This code was written as part of the DANSE project
 * http://danse.us/trac/sans/
 *
 * Copyright 2007: University of Tennessee, for the DANSE project
 */
#if !defined(c_disperser_h)
#define c_disperser_h

double c_disperser( double (*eval)(double[], double, double), double dp[], int n_pars, 
					int *idList, double *sigmaList, int n_pts, double q, double phi );

double weight_dispersion( double (*eval)(double[], double, double), 
						  double *par_values, double *weight_values, 
						  int npts, int i_par,
						  double dp[], double q, double phi );


#endif
