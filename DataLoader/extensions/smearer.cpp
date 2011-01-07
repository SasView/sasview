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
	even_binning = true;
};

/**
 * Constructor for BaseSmearer
 *
 * Used for uneven binning
 * @param q: array of Q values
 * @param nbins: number of Q bins
 */
BaseSmearer :: BaseSmearer(double* q, int nbins) {
	// Number of bins
	this->nbins = nbins;
	this->q_values = q;
	// Flag to keep track of whether we have a smearing matrix or
	// whether we need to compute one
	has_matrix = false;
	even_binning = false;
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
 * @param width: slit width in Q units
 * @param height: slit height in Q units
 * @param q: array of Q values
 * @param nbins: number of Q bins
 */
SlitSmearer :: SlitSmearer(double width, double height, double* q, int nbins) :
	BaseSmearer(q, nbins){
	this->height = height;
	this->width = width;
};

/**
 * Constructor for QSmearer
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
 * Constructor for QSmearer
 *
 * @param width: array slit widths for each Q point, in Q units
 * @param q: array of Q values
 * @param nbins: number of Q bins
 */
QSmearer :: QSmearer(double* width, double* q, int nbins) :
	BaseSmearer(q, nbins){
	this->width = width;
};

/**
 * Compute the slit smearing matrix
 *
 * For even binning (q_min to q_max with nbins):
 *
 *   step = (q_max-q_min)/(nbins-1)
 *   first bin goes from q_min to q_min+step
 *   last bin goes from q_max to q_max+step
 *
 * For binning according to q array:
 *
 * Each q point represents a bin going from half the distance between it
 * and the previous point to half the distance between it and the next point.
 *
 *    Example: bin i goes from (q_values[i-1]+q_values[i])/2 to (q_values[i]+q_values[i+1])/2
 *
 * The exceptions are the first and last bins, which are centered at the first and
 * last q-values, respectively. The width of the first and last bins is the distance between
 * their respective neighboring q-value.
 */
void SlitSmearer :: compute_matrix(){

	weights = new vector<double>(nbins*nbins,0);

	// Check the length of the data
	if (nbins<2) return;

	// Loop over all q-values
	for(int i=0; i<nbins; i++) {
		double q, q_min, q_max;
		get_bin_range(i, &q, &q_min, &q_max);

		// For each q-value, compute the weight of each other q-bin
		// in the I(q) array
		int npts_h = height>0 ? npts : 1;
		int npts_w = width>0 ? npts : 1;

		// If both height and width are great than zero,
		// modify the number of points in each direction so
		// that the total number of points is still what
		// the user would expect (downgrade resolution)
		// Never down-grade npts_h. That will give incorrect slit smearing...
		if(npts_h>1 && npts_w>1){
			npts_h = npts;//(int)ceil(sqrt((double)npts));
			// In general width is much smaller than height, so smaller npt_w
			// should work fine.
			// Todo: It is still very expansive in time. Think about better way.
			npts_w = (int)ceil(npts_h / 100);
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

				// Find in which bin this shifted value belongs
				int q_i=nbins;
				if (even_binning) {
					// This is kept for backward compatibility since the binning
					// was originally defined differently for even bins.
					q_i = (int)(floor( (q_shifted-qmin) /((qmax-qmin)/((double)nbins -1.0)) ));
				} else {
					for(int t=0; t<nbins; t++) {
						double q_t, q_high, q_low;
						get_bin_range(t, &q_t, &q_low, &q_high);
						if(q_shifted>=q_low && q_shifted<q_high) {
							q_i = t;
							break;
						}
					}
				}

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
	double q, q_min, q_max;
	double q_j, q_jmax, q_jmin;
	for(int i=0; i<nbins; i++) {
		get_bin_range(i, &q, &q_min, &q_max);

		for(int j=0; j<nbins; j++) {
			get_bin_range(j, &q_j, &q_jmin, &q_jmax);

			// Compute the fraction of the Gaussian contributing
			// to the q_j bin between q_jmin and q_jmax
			double value =  erf( (q_jmax-q)/(sqrt(2.0)*width[i]) );
        	value -= erf( (q_jmin-q)/(sqrt(2.0)*width[i]) );
        	(*weights)[i*nbins+j] += value;
		}
	}
}

/**
 * Computes the Q range of a given bin of the Q distribution.
 * The range is computed according the the data distribution that
 * was given to the object at initialization.
 *
 * @param i: number of the bin in the distribution
 * @param q: q-value of bin i
 * @param q_min: lower bound of the bin
 * @param q_max: higher bound of the bin
 *
 */
int BaseSmearer :: get_bin_range(int i, double* q, double* q_min, double* q_max) {
	if (even_binning) {
		double step = (qmax-qmin)/((double)nbins-1.0);
		*q = qmin + (double)i*step;
		*q_min = *q - 0.5*step;
		*q_max = *q + 0.5*step;
		return 1;
	} else if (i>=0 && i<nbins) {
		*q = q_values[i];
		if (i==0) {
			double step = (q_values[1]-q_values[0])/2.0;
			*q_min = *q - step;
			*q_max = *q + step;
		} else if (i==nbins-1) {
			double step = (q_values[i]-q_values[i-1])/2.0;
			*q_min = *q - step;
			*q_max = *q + step;
		} else {
			*q_min = *q - (q_values[i]-q_values[i-1])/2.0;
			*q_max = *q + (q_values[i+1]-q_values[i])/2.0;
		}
		return 1;
	}
	return -1;
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
			// Skip if weight is less than 1e-04(this value is much smaller than
			// the weight at the 3*sigma distance
			// Will speed up a little bit...
			if ((*weights)[q_i*nbins+i] < 1.0e-004){
				continue;
			}
			sum += iq_in[i] * (*weights)[q_i*nbins+i];
			counts += (*weights)[q_i*nbins+i];
		}

		// Normalize counts
		iq_out[q_i] = (counts>0.0) ? sum/counts : 0;
	}
}
