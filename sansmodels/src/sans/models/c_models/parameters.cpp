/**
	This software was developed by the University of Tennessee as part of the
	Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
	project funded by the US National Science Foundation.

	If you use DANSE applications to do scientific research that leads to
	publication, we ask that you acknowledge the use of the software with the
	following sentence:

	"This work benefited from DANSE software developed under NSF award DMR-0520547."

	copyright 2008, University of Tennessee
 */
#include "parameters.hh"
#include <stdio.h>
#include <math.h>
using namespace std;

#if defined(_MSC_VER)
#include "gamma_win.h"
#endif

/**
 * TODO: normalize all dispersion weight lists
 */


/**
 * Weight points
 */
WeightPoint :: WeightPoint() {
	value = 0.0;
	weight = 0.0;
}

WeightPoint :: WeightPoint(double v, double w) {
	value = v;
	weight = w;
}

/**
 * Dispersion models
 */
DispersionModel :: DispersionModel() {
	npts  = 1;
	width = 0.0;
};

void DispersionModel :: accept_as_source(DispersionVisitor* visitor, void* from, void* to) {
	visitor->dispersion_to_dict(from, to);
}
void DispersionModel :: accept_as_destination(DispersionVisitor* visitor, void* from, void* to) {
	visitor->dispersion_from_dict(from, to);
}
void DispersionModel :: operator() (void *param, vector<WeightPoint> &weights){
	// Check against zero width
	if (width<=0) {
		width = 0.0;
		npts  = 1;
	}

	Parameter* par = (Parameter*)param;
	double value = (*par)();
	double sig;
	if (npts<2) {
		weights.insert(weights.end(), WeightPoint(value, 1.0));
	} else {
		for(int i=0; i<npts; i++) {

			if ((*par).has_min==false){
				// width = sigma for angles
				sig = width;
			}
			else{
				//width = polydispersity (=sigma/value) for length
				sig = width * value;
			}
			double val = value + sig * (1.0*double(i)/double(npts-1) - 0.5);
			if ( ((*par).has_min==false || val>(*par).min)
			  && ((*par).has_max==false || val<(*par).max)  )
				weights.insert(weights.end(), WeightPoint(val, 1.0));
		}
	}
}

/**
 * Method to set the weights
 * Not implemented for this class
 */
void DispersionModel :: set_weights(int npoints, double* values, double* weights){}

/**
 * Gaussian dispersion
 */

GaussianDispersion :: GaussianDispersion() {
	npts  = 100;
	width = 0.0;
	nsigmas = 10;
};

void GaussianDispersion :: accept_as_source(DispersionVisitor* visitor, void* from, void* to) {
	visitor->gaussian_to_dict(from, to);
}
void GaussianDispersion :: accept_as_destination(DispersionVisitor* visitor, void* from, void* to) {
	visitor->gaussian_from_dict(from, to);
}

double gaussian_weight(double mean, double sigma, double x) {
	double vary, expo_value;
    vary = x-mean;
    expo_value = -vary*vary/(2.0*sigma*sigma);
    //return 1.0;
    return exp(expo_value);
}

/**
 * Gaussian dispersion
 * @param mean: mean value of the Gaussian
 * @param sigma: standard deviation of the Gaussian
 * @param x: value at which the Gaussian is evaluated
 * @return: value of the Gaussian
 */
void GaussianDispersion :: operator() (void *param, vector<WeightPoint> &weights){
	// Check against zero width
	if (width<=0) {
		width = 0.0;
		npts  = 1;
		nsigmas = 10;
	}

	Parameter* par = (Parameter*)param;
	double value = (*par)();
	double sig;
	if (npts<2) {
		weights.insert(weights.end(), WeightPoint(value, 1.0));
	} else {
		for(int i=0; i<npts; i++) {
			if ((*par).has_min==false){
				// width = sigma for angles
				sig = width;
			}
			else{
				//width = polydispersity (=sigma/value) for length
				sig = width * value;
			}
			// We cover n(nsigmas) times sigmas on each side of the mean
			double val = value + sig * (2.0*nsigmas*double(i)/double(npts-1) - nsigmas);
			if ( ((*par).has_min==false || val>(*par).min)
			  && ((*par).has_max==false || val<(*par).max)  ) {
				double _w = gaussian_weight(value, sig, val);
				weights.insert(weights.end(), WeightPoint(val, _w));
			}
		}
	}
}


/**
 * Flat dispersion
 */

RectangleDispersion :: RectangleDispersion() {
	npts  = 100;
	width = 0.0;
	nsigmas = 1.73205;
};

void RectangleDispersion :: accept_as_source(DispersionVisitor* visitor, void* from, void* to) {
	visitor->rectangle_to_dict(from, to);
}
void RectangleDispersion :: accept_as_destination(DispersionVisitor* visitor, void* from, void* to) {
	visitor->rectangle_from_dict(from, to);
}

double rectangle_weight(double mean, double sigma, double x) {
    double wid = fabs(sigma) * sqrt(3.0);
    if (x>= (mean-wid) && x<=(mean+wid)){
    	return 1.0;
    }
    else{
    	return 0.0;
    }
}

/**
 * Flat dispersion
 * @param mean: mean value
 * @param sigma: half width of top hat function
 * @param x: value at which the Flat is evaluated
 * @return: value of the Flat
 */
void RectangleDispersion :: operator() (void *param, vector<WeightPoint> &weights){
	// Check against zero width
	if (width<=0) {
		width = 0.0;
		npts  = 1;
		nsigmas = 1.73205;
	}

	Parameter* par = (Parameter*)param;
	double value = (*par)();
	double sig;
	if (npts<2) {
		weights.insert(weights.end(), WeightPoint(value, 1.0));
	} else {
		for(int i=0; i<npts; i++) {
			if ((*par).has_min==false){
				// width = sigma for angles
				sig = width;
			}
			else{
				//width = polydispersity (=sigma/value) for length
				sig = width * value;
			}
			// We cover n(nsigmas) times sigmas on each side of the mean
			double val = value + sig * (2.0*nsigmas*double(i)/double(npts-1) - nsigmas);
			if ( ((*par).has_min==false || val>(*par).min)
			  && ((*par).has_max==false || val<(*par).max)  ) {
				double _w = rectangle_weight(value, sig, val);
				weights.insert(weights.end(), WeightPoint(val, _w));
			}
		}
	}
}


/**
 * LogNormal dispersion
 */

LogNormalDispersion :: LogNormalDispersion() {
	npts  = 100;
	width = 0.0;
	nsigmas = 10.0;
};

void LogNormalDispersion :: accept_as_source(DispersionVisitor* visitor, void* from, void* to) {
	visitor->lognormal_to_dict(from, to);
}
void LogNormalDispersion :: accept_as_destination(DispersionVisitor* visitor, void* from, void* to) {
	visitor->lognormal_from_dict(from, to);
}

double lognormal_weight(double mean, double sigma, double x) {

	double sigma2 = pow(sigma, 2.0);
	return 1.0/(x*sigma) * exp( -pow((log(x) - mean), 2.0) / (2.0*sigma2));

}

/**
 * Lognormal dispersion
 * @param mean: mean value of the LogNormal
 * @param sigma: standard deviation of the LogNormal
 * @param x: value at which the LogNormal is evaluated
 * @return: value of the LogNormal
 */
void LogNormalDispersion :: operator() (void *param, vector<WeightPoint> &weights){
	// Check against zero width
	if (width<=0) {
		width = 0.0;
		npts  = 1;
		nsigmas = 10.0;
	}

	Parameter* par = (Parameter*)param;
	double value = (*par)();
	double sig;
	if (npts<2) {
		weights.insert(weights.end(), WeightPoint(value, 1.0));
	} else {
		for(int i=0; i<npts; i++) {
			// Note that the definition of sigma is different from Gaussian
			if ((*par).has_min==false){
				// sig  for angles
				sig = width;
			}
			else{
				// by lognormal definition, PD is same as sigma
				sig = width * value;
			}
			
			// We cover n(nsigmas) times sigmas on each side of the mean
			//constant bin in real space
			double val = value + sig * (2.0*nsigmas*double(i)/double(npts-1) - nsigmas);
			// sigma in the lognormal function is in ln(R) space, thus needs converting
			sig = fabs(sig/value); 
			if ( ((*par).has_min==false || val>(*par).min)
			  && ((*par).has_max==false || val<(*par).max)  ) {
				double _w = lognormal_weight(log(value), sig, val);
				weights.insert(weights.end(), WeightPoint(val, _w));
				//printf("%g \t %g\n",val,_w);

			}
		}
	}
}



/**
 * Schulz dispersion
 */

SchulzDispersion :: SchulzDispersion() {
	npts  = 100;
	width = 0.0;
	nsigmas = 10.0;
};

void SchulzDispersion :: accept_as_source(DispersionVisitor* visitor, void* from, void* to) {
	visitor->schulz_to_dict(from, to);
}
void SchulzDispersion :: accept_as_destination(DispersionVisitor* visitor, void* from, void* to) {
	visitor->schulz_from_dict(from, to);
}

double schulz_weight(double mean, double sigma, double x) {
    double z = pow(mean/ sigma, 2.0)-1.0;
	double R= x/mean;
	double zz= z+1.0;
	double expo;
	expo = zz*log(zz)+z*log(R)-R*zz-log(mean)-lgamma(zz);
	return  exp(expo);
}

/**
 * Schulz dispersion
 * @param mean: mean value of the Schulz
 * @param sigma: standard deviation of the Schulz
 * @param x: value at which the Schulz is evaluated
 * @return: value of the Schulz
 */
void SchulzDispersion :: operator() (void *param, vector<WeightPoint> &weights){
	// Check against zero width
	if (width<=0) {
		width = 0.0;
		npts  = 1;
		nsigmas = 10.0;
	}

	Parameter* par = (Parameter*)param;
	double value = (*par)();
	double sig;
	if (npts<2) {
		weights.insert(weights.end(), WeightPoint(value, 1.0));
	} else {
		for(int i=0; i<npts; i++) {
			if ((*par).has_min==false){
				// width = sigma for angles
				sig = width;
			}
			else{
				//width = polydispersity (=sigma/value) for length
				sig = width * value;
			}
			// We cover n(nsigmas) times sigmas on each side of the mean
			double val = value + sig * (2.0*nsigmas*double(i)/double(npts-1) - nsigmas);

			if ( ((*par).has_min==false || val>(*par).min)
			  && ((*par).has_max==false || val<(*par).max)  ) {
				double _w = schulz_weight(value, sig, val);
				weights.insert(weights.end(), WeightPoint(val, _w));
			}
		}
	}
}




/**
 * Array dispersion based on input arrays
 */

void ArrayDispersion :: accept_as_source(DispersionVisitor* visitor, void* from, void* to) {
	visitor->array_to_dict(from, to);
}
void ArrayDispersion :: accept_as_destination(DispersionVisitor* visitor, void* from, void* to) {
	visitor->array_from_dict(from, to);
}

/**
 * Method to get the weights
 */
void ArrayDispersion :: operator() (void *param, vector<WeightPoint> &weights) {
	Parameter* par = (Parameter*)param;
	double value = (*par)();

	if (npts<2) {
		weights.insert(weights.end(), WeightPoint(value, 1.0));
	} else {
		for(int i=0; i<npts; i++) {
			double val = _values[i]; //+ value;  //ToDo: Talk to Paul and put back the 'value'.

			if ( ((*par).has_min==false || val>(*par).min)
			  && ((*par).has_max==false || val<(*par).max)  )
				weights.insert(weights.end(), WeightPoint(val, _weights[i]));
		}
	}
}
/**
 * Method to set the weights
 */
void ArrayDispersion :: set_weights(int npoints, double* values, double* weights){
	npts = npoints;
	_values = values;
	_weights = weights;
}


/**
 * Parameters
 */
Parameter :: Parameter() {
	value = 0;
	min   = 0.0;
	max   = 0.0;
	has_min = false;
	has_max = false;
	has_dispersion = false;
	dispersion = new GaussianDispersion();
}

Parameter :: Parameter(double _value) {
	value = _value;
	min   = 0.0;
	max   = 0.0;
	has_min = false;
	has_max = false;
	has_dispersion = false;
	dispersion = new GaussianDispersion();
}

Parameter :: Parameter(double _value, bool disp) {
	value = _value;
	min   = 0.0;
	max   = 0.0;
	has_min = false;
	has_max = false;
	has_dispersion = disp;
	dispersion = new GaussianDispersion();
}

void Parameter :: get_weights(vector<WeightPoint> &weights) {
	(*dispersion)((void*)this, weights);
}

void Parameter :: set_min(double value) {
	has_min = true;
	min = value;
}

void Parameter :: set_max(double value) {
	has_max = true;
	max = value;
}

double Parameter :: operator()() {
	return value;
}

double Parameter :: operator=(double _value){
	value = _value;
	return value;
}
