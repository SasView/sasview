/**
	This software was developed by the University of Tennessee as part of the
	Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
	project funded by the US National Science Foundation.

	If you use DANSE applications to do scientific research that leads to
	publication, we ask that you acknowledge the use of the software with the
	following sentence:

	"This work benefited from DANSE software developed under NSF award DMR-0520547."

	copyright 2009, University of Tennessee
 */
#include "smearer.hh"
#include <stdio.h>
#include <math.h>
using namespace std;


/**
 * Constructor for BaseSmearer
 *
 * @param qmin: minimum Q value
 * @param qmax: maximum Q value
 * @param nbins: number of Q bins
 */
BaseSmearer :: BaseSmearer(double qmin, double qmax, int nbins) {
	// Number of bins
	this->nbins = nbins;
	this->qmin = qmin;
	this->qmax = qmax;
	// Flag to keep track of whether we have a smearing matrix or
	// whether we need to compute one
	has_matrix = false;
};

/**
 * Constructor for SlitSmearer
 *
 * @param width: slit width in Q units
 * @param height: slit height in Q units
 * @param qmin: minimum Q value
 * @param qmax: maximum Q value
 * @param nbins: number of Q bins
 */
SlitSmearer :: SlitSmearer(double width, double height, double qmin, double qmax, int nbins) :
	BaseSmearer(qmin, qmax, nbins){
	this->height = height;
	this->width = width;
};

	/**
	 * Constructor for SlitSmearer
	 *
	 * @param width: array slit widths for each Q point, in Q units
	 * @param qmin: minimum Q value
	 * @param qmax: maximum Q value
	 * @param nbins: number of Q bins
	 */
QSmearer :: QSmearer(double* width, double qmin, double qmax, int nbins) :
	BaseSmearer(qmin, qmax, nbins){
	this->width = width;
};

/**
 * Compute the slit smearing matrix
 */
void SlitSmearer :: compute_matrix(){

	weights = new vector<double>(nbins*nbins,0);

	// Loop over all q-values
	for(int i=0; i<nbins; i++) {
		double q = qmin + (double)i*(qmax-qmin)/((double)nbins-1.0);

		// For each q-value, compute the weight of each other q-bin
		// in the I(q) array
		int npts_h = height>0 ? npts : 1;
		int npts_w = width>0 ? npts : 1;

		// If both height and width are great than zero,
		// modify the number of points in each direction so
		// that the total number of points is still what
		// the user would expect (downgrade resolution)
		if(npts_h>1 && npts_w>1){
			npts_h = (int)ceil(sqrt((double)npts));
			npts_w = npts_h;
		}

		double shift_h, shift_w;
		for(int k=0; k<npts_h; k++){
			if(npts_h==1){
				shift_h = 0;
			} else {
				shift_h = height/((double)npts_h-1.0) * (double)k;
			}
			for(int j=0; j<npts_w; j++){
				if(npts_w==1){
					shift_w = 0;
				} else {
					shift_w = width/((double)npts_w-1.0) * (double)j;
				}
				double q_shifted = sqrt( ((q-shift_w)*(q-shift_w) + shift_h*shift_h) );
				int q_i = (int)(floor( (q_shifted-qmin) /((qmax-qmin)/((double)nbins -1.0)) ));

				// Skip the entries outside our I(q) range
				//TODO: be careful with edge effect
				if(q_i<nbins)
					(*weights)[i*nbins+q_i]++;
			}
		}
	}
};

/**
 * Compute the point smearing matrix
 */
void QSmearer :: compute_matrix(){
	weights = new vector<double>(nbins*nbins,0);

	// Loop over all q-values
	double step = (qmax-qmin)/((double)nbins-1.0);
	for(int i=0; i<nbins; i++) {
		double q = qmin + (double)i*step;
		double q_min = q - 0.5*step;
		double q_max = q + 0.5*step;

		for(int j=0; j<nbins; j++) {
			double q_j = qmin + (double)j*step;

			// Compute the fraction of the Gaussian contributing
			// to the q bin between q_min and q_max
			double value =  erf( (q_max-q_j)/(sqrt(2.0)*width[j]) );
        	value -= erf( (q_min-q_j)/(sqrt(2.0)*width[j]) );
        	(*weights)[i*nbins+j] += value;
		}
	}
}

/**
 * Perform smearing by applying the smearing matrix to the input Q array
 */
void BaseSmearer :: smear(double *iq_in, double *iq_out, int first_bin, int last_bin){

	// If we haven't computed the smearing matrix, do it now
	if(!has_matrix) {
		compute_matrix();
		has_matrix = true;
	}

	// Loop over q-values and multiply apply matrix
	for(int q_i=first_bin; q_i<=last_bin; q_i++){
		double sum = 0.0;
		double counts = 0.0;

		for(int i=first_bin; i<=last_bin; i++){
			sum += iq_in[i] * (*weights)[q_i*nbins+i];
			counts += (*weights)[q_i*nbins+i];
		}

		// Normalize counts
		iq_out[q_i] = (counts>0.0) ? sum/counts : 0;
	}
}
