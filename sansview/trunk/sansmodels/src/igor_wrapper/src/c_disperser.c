/**
 * Straight C disperser
 * 
 * This code was written as part of the DANSE project
 * http://danse.us/trac/sans/
 *
 * Copyright 2007: University of Tennessee, for the DANSE project
 */
#include "math.h"
#include <stdio.h>
#include <stdlib.h>

/**
 * Weight distribution to give to each point in the dispersion
 * The distribution is a Gaussian with
 * 
 * @param mean: mean value of the Gaussian
 * @param sigma: sigma of the Gaussian
 * @param x: point to evaluate at
 * @return: weight value
 * 
 */
double c_disperser_weight(double mean, double sigma, double x) {
	double vary, expo_value;
    vary = x-mean;
    expo_value = -vary*vary/(2*sigma*sigma);
    return exp(expo_value);
}

/**
 * Function to apply dispersion to a list of parameters.
 * 
 * This function is re-entrant. It should be called with iPar=0.
 * It will then call itself with increasing values for iPar until
 * all parameters to be dispersed have been dealt with.
 *
 * 
 * @param eval: pointer to the function used to evaluate the model at
 * 				a particular point.
 * @param dp: complete array of parameter values for the model.
 * @param n_pars: number of parameters to apply dispersion to.
 * @param idList: list of parameter indices for the parameters to apply
 * 				dispersion to. For a given parameter, its index is the
 * 				index of its position in the parameter vector of the model
 * 				function.
 * @param sigmaList: list of sigma values for the parameters to apply 
 * 				dispersion to.
 * @param centers: list of mean values for the parameters to apply 
 * 				dispersion to.
 * @param n_pts: number of points to use when applying dispersion.
 * @param q: q-value to evaluate the model at.
 * @param phi: angle of the q-vector with the q_x axis.
 * @param iPar: index of the parameter to apply dispersion to (should
 * 				be 0 when called by the user). 
 * 
 */
double c_disperseParam( double (*eval)(double[], double, double), double dp[], int n_pars, 
					int *idList, double *sigmaList, double *centers, 
					int n_pts, double q, double phi, int iPar ) {
	double min_value, max_value;
	double step;
	double prev_value;
	double value_sum;
	double gauss_sum;
	double gauss_value;
	double func_value;
	double error_sys;
	double value;
	int n_sigma;
	int i;
	// Number of std variations to average over	
	n_sigma = 2;	
    if( iPar < n_pars ) {
            
		// Average over Gaussian distribution (2 sigmas)
        value_sum = 0.0;
        gauss_sum = 0.0;
            
        // Average over 4 sigmas wide
        min_value = centers[iPar] - n_sigma*sigmaList[iPar];
        max_value = centers[iPar] + n_sigma*sigmaList[iPar];
            
        // Calculate step size
        step = (max_value - min_value)/(n_pts-1);
            
        // If we are not changing the parameter, just return the 
        // value of the function
        if (step == 0.0) {
            return c_disperseParam(eval, dp, n_pars, idList, sigmaList, 
            						centers, n_pts, q, phi, iPar+1);
        }
            
        // Compute average
        prev_value = 0.0;
        error_sys  = 0.0;
        for( i=0; i<n_pts; i++ ) {
            // Set the parameter value           
            value = min_value + (double)i*step;
            dp[idList[iPar]] = value;
                
			gauss_value = c_disperser_weight(centers[iPar], sigmaList[iPar], value);
            func_value = c_disperseParam(eval, dp, n_pars, idList, sigmaList, 
            						centers, n_pts, q, phi, iPar+1);

            value_sum += gauss_value * func_value;
        	gauss_sum += gauss_value;	
        }   
        return value_sum/gauss_sum;
        
    } else {
    	 return (*eval)(dp, q, phi);
    }
	
}

/**
 * Function to add dispersion to a model.
 * The dispersion is Gaussian around the value of given parameters.
 * 
 * @param eval: pointer to the function used to evaluate the model at
 * 				a particular point.
 * @param n_pars: number of parameters to apply dispersion to.
 * @param idList: list of parameter indices for the parameters to apply
 * 				dispersion to. For a given parameter, its index is the
 * 				index of its position in the parameter vector of the model
 * 				function.
 * @param sigmaList: list of sigma values for the parameters to apply 
 * 				dispersion to.
 * @param n_pts: number of points to use when applying dispersion.
 * @param q: q-value to evaluate the model at.
 * @param phi: angle of the q-vector with the q_x axis.
 * 
 */
double c_disperser( double (*eval)(double[], double, double), double dp[], int n_pars, 
					int *idList, double *sigmaList, int n_pts, double q, double phi ) {
	double *centers;
	double value;
	int i;
	
	// Allocate centers array
	if( n_pars > 0 ) {
	    centers = (double *)malloc(n_pars * sizeof(double));
		if(centers==NULL) {
		    printf("c_disperser could not allocate memory\n");
			return 0.0;
		}
	}
	
	// Store current values in centers array
	for(i=0; i<n_pars; i++) {
		centers[i] = dp[idList[i]];	
	}
	
	
	if( n_pars > 0 ) {
		value = c_disperseParam(eval, dp, n_pars, idList, sigmaList, centers, n_pts, q, phi, 0);
    } else {
    	value = (*eval)(dp, q, phi);
	}
	free(centers);
	return value;
}

/**
 * 
 * Angles are in radian.
 * 
 * 
 */
double weight_dispersion( double (*eval)(double[], double, double), 
						  double *par_values, double *weight_values, 
						  int npts, int i_par,
						  double dp[], double q, double phi ) {
	int i;
	double value;
	double norma;
				
	value = 0.0;
	norma = 0.0;	  	

	// If we have an empty array of points, just 
	// evaluate the function
	if(npts == 0) {
		return (*eval)(dp, q, phi);
	} else {
		for(i=0; i<npts; i++) {
			dp[i_par] = par_values[i];
			value += weight_values[i] * (*eval)(dp, q, phi);
			//dp[i_par] = -par_values[i];
			//value += weight_values[i] * (*eval)(dp, q, phi);
			
			norma += weight_values[i];
		}
	}
	return value/norma/2.0;
						  	
}
