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

#if defined(_MSC_VER)
extern "C" {
#include "winFuncs.h"
}
#endif
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
	int npts_h = height>0.0 ? npts : 1;
	int npts_w = width>0.0 ? npts : 1;

	// If both height and width are great than zero,
	// modify the number of points in each direction so
	// that the total number of points is still what
	// the user would expect (downgrade resolution)
	//if(npts_h>1 && npts_w>1){
	//	npts_h = (int)ceil(sqrt((double)npts));
	//	npts_w = npts_h;
	//}
	double shift_h, shift_w, hbin_size, wbin_size;
	// Make sure height and width are all positive (FWMH/2)
	// Assumption; height and width are all same for all q points
	if(npts_h == 1){
		shift_h = 0.0;
	} else {
		shift_h = fabs(height);
	}
	if(npts_w == 1){
		shift_w = 0.0;
	} else {
		shift_w = fabs(width);
	}
	// size of the h bin and w bin
	hbin_size = shift_h / nbins;
	wbin_size = shift_w / nbins;

	// Loop over all q-values
	double q, q_min, q_max, q_0=0.0;
	for(int i=0; i<nbins; i++) {
		// Find Weights
		// Find q where the resolution smearing calculation of I(q) occurs
		get_bin_range(i, &q, &q_min, &q_max);
		// Block q becomes <=0
		if (q <= 0){
			continue;
		}
		// Find q[0] value to normalize the weight later,
		//  otherwise, we will have a precision problem.
		if (i == 0){
			q_0 = q;
		}
		// Loop over all qj-values
		for(int j=0; j<nbins; j++) {
			double q_j, q_high, q_low;
			// Calculate bin size of q_j
			get_bin_range(j, &q_j, &q_low, &q_high);
			// Block q_j becomes <=0
			if (q_j <= 0){
				continue;
			}
			// Check q_low that can not be negative.
			if (q_low < 0.0){
				q_low = 0.0;
			}
			// default parameter values
			(*weights)[i*nbins+j] = 0.0;
			// protect for negative q
			if (q <= 0.0 || q_j <= 0.0){
					continue;
			}
			double shift_w = 0.0;
			// Condition: zero slit smear.
			if (npts_w == 1 && npts_h == 1){
				if(q_j == q) {
					(*weights)[i*nbins+j] = 1.0;
				}
			}
			//Condition:Smear weight integration for width >0 when the height (=0) does not present.
			//Or height << width.
			else if((npts_w!=1 && npts_h == 1)|| (npts_w!=1 && npts_h != 1 && width/height > 100.0)){
				shift_w = width;
				//del_w = width/((double)npts_w-1.0);
				double q_shifted_low = q - shift_w;
				// High limit of the resolution range
				double q_shifted_high = q + shift_w;
				// Go through all the q_js for weighting those points
				if(q_j >= q_shifted_low && q_j <= q_shifted_high) {
					// The weighting factor comes,
					// Give some weight (delq_bin) for the q_j within the resolution range
					// Weight should be same for all qs except
					// for the q bin size at j.
					// Note that the division by q_0 is only due to the precision problem
					// where q_high - q_low gets to very small.
					// Later, it will be normalized again.
					(*weights)[i*nbins+j] += (q_high - q_low)/q_0 ;
				}
			}
			else{
				// Loop for width (;Height is analytical.)
				// Condition: height >>> width, otherwise, below is not accurate enough.
				// Smear weight numerical iteration for width >0 when the height (>0) presents.
				// When width = 0, the numerical iteration will be skipped.
				// The resolution calculation for the height is done by direct integration,
				// assuming the I(q'=sqrt(q_j^2-(q+shift_w)^2)) is constant within a q' bin, [q_high, q_low].
				// In general, this weight numerical iteration for width >0 might be a rough approximation,
				// but it must be good enough when height >>> width.
				for(int k=(-npts_w + 1); k<npts_w; k++){
					if(npts_w!=1){
						shift_w = width/((double)npts_w-1.0)*(double)k;
					}
					// For each q-value, compute the weight of each other q-bin
					// in the I(q) array
					// Low limit of the resolution range
					double q_shift = q + shift_w;
					if (q_shift < 0.0){
						q_shift = 0.0;
					}
					double q_shifted_low = q_shift;
					// High limit of the resolution range
					double q_shifted_high = sqrt(q_shift * q_shift + shift_h * shift_h);


					// Go through all the q_js for weighting those points
					if(q_j >= q_shifted_low && q_j <= q_shifted_high) {
						// The weighting factor comes,
						// Give some weight (delq_bin) for the q_j within the resolution range
						// Weight should be same for all qs except
						// for the q bin size at j.
						// Note that the division by q_0 is only due to the precision problem
						// where q_high - q_low gets to very small.
						// Later, it will be normalized again.

						// The fabs below are not necessary but in case: the weight should never be imaginary.
						// At the edge of each sub_width. weight += u(at q_high bin) - u(0), where u(0) = 0,
						// and weighted by (2.0* npts_w -1.0)once for each q.
						//if (q == q_j) {
						if (q_low <= q_shift && q_high > q_shift) {
							//if (k==0)
								(*weights)[i*nbins+j] += (sqrt(fabs((q_high)*(q_high)-q_shift * q_shift)))/q_0;// * (2.0*double(npts_w)-1.0);
						}
						// For the rest of sub_width. weight += u(at q_high bin) - u(at q_low bin)
						else{// if (u > 0.0){
							(*weights)[i*nbins+j] += (sqrt(fabs((q_high)*(q_high)- q_shift * q_shift))-sqrt(fabs((q_low)*(q_low)- q_shift * q_shift)))/q_0 ;
						}
					}
				}
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
	double q, q_min, q_max;
	double q_j, q_jmax, q_jmin;
	for(int i=0; i<nbins; i++) {
		get_bin_range(i, &q, &q_min, &q_max);

		for(int j=0; j<nbins; j++) {
			get_bin_range(j, &q_j, &q_jmin, &q_jmax);

			// Compute the fraction of the Gaussian contributing
			// to the q_j bin between q_jmin and q_jmax
			long double value =  erf( (q_jmax-q)/(sqrt(2.0)*width[i]) );
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
			// Skip if weight is less than 1e-03(this value is much smaller than
			// the weight at the 3*sigma distance
			// Will speed up a little bit...
			if ((*weights)[q_i*nbins+i] < 1.0e-003){
				continue;
			}
			sum += iq_in[i] * (*weights)[q_i*nbins+i];
			counts += (*weights)[q_i*nbins+i];
		}

		// Normalize counts
		iq_out[q_i] = (counts>0.0) ? sum/counts : 0.0;
	}
}
