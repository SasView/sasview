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
#ifndef PARAM_CLASS_H
#define PARAM_CLASS_H
/**
 * TODO: will need to write a bridge class
 * to convert the dispersion model parameters
 * into dictionary parameters for python.
 */
#include <vector>
#include "dispersion_visitor.hh"

using namespace std;

/**
 * Weight point class to hold averaging points
 */
class WeightPoint {
public:
	/// Value of the weight point
	double value;
	/// Weight of the weight point
	double weight;

	WeightPoint();
	WeightPoint(double, double);
};

/**
 * Basic averaging model. The class instance will
 * generate a flat distribution of weight points
 * according to the number of points specified
 * and the width of the distribution. The center
 * of the distribution is specified by the
 * Parameter object taken in as a parameter.
 */
class DispersionModel {
public:
	/// Number of points to average over
	int npts;
	/// Width of the distribution (step function)
	double width;

	DispersionModel();
	/// Method that generates the weight points
	virtual void operator()(void *, vector<WeightPoint>&);
	virtual void set_weights(int, double*, double*);
	virtual void accept_as_source(DispersionVisitor*, void*, void*);
	virtual void accept_as_destination(DispersionVisitor*, void*, void*);
};


/**
 * Gaussian dispersion model
 */
class GaussianDispersion: public DispersionModel {
public:
	/// Number of sigmas on each side of the mean
	double nsigmas;

	GaussianDispersion();
	void operator()(void *, vector<WeightPoint>&);
	void accept_as_source(DispersionVisitor*, void*, void*);
	void accept_as_destination(DispersionVisitor*, void*, void*);
};

/**
 * Flat dispersion model
 */
class RectangleDispersion: public DispersionModel {
public:
	/// Number of sigmas on each side of the mean
	double nsigmas;

	RectangleDispersion();
	void operator()(void *, vector<WeightPoint>&);
	void accept_as_source(DispersionVisitor*, void*, void*);
	void accept_as_destination(DispersionVisitor*, void*, void*);
};

/**
 * Schulz dispersion model
 */
class SchulzDispersion: public DispersionModel {
public:
	/// Number of sigmas on each side of the mean
	double nsigmas;

	SchulzDispersion();
	void operator()(void *, vector<WeightPoint>&);
	void accept_as_source(DispersionVisitor*, void*, void*);
	void accept_as_destination(DispersionVisitor*, void*, void*);
};

/**
 * LogNormal dispersion model
 */
class LogNormalDispersion: public DispersionModel {
public:
	/// Number of sigmas on each side of the mean
	double nsigmas;

	LogNormalDispersion();
	void operator()(void *, vector<WeightPoint>&);
	void accept_as_source(DispersionVisitor*, void*, void*);
	void accept_as_destination(DispersionVisitor*, void*, void*);
};


/**
 * Dispersion model based on arrays provided by the user
 */
class ArrayDispersion: public DispersionModel {
private:
	/// Array of values
	double* _values;
	/// Array of weights
	double* _weights;

	/// Method to set the weight points from arrays
	void set_weights(int, double*, double*);
	void operator()(void *, vector<WeightPoint>&);
	void accept_as_source(DispersionVisitor*, void*, void*);
	void accept_as_destination(DispersionVisitor*, void*, void*);
public:

};

/**
 * Parameter class to hold information about a
 * parameter.
 */
class Parameter {
public:
	/// Current value of the parameter
	double value;
	/// True if the parameter has a minimum bound
	bool has_min;
	/// True if the parameter has a maximum bound
	bool has_max;
	/// Minimum bound
	double min;
	/// Maximum bound
	double max;
	/// True if the parameter can be dispersed or averaged
	bool has_dispersion;
	/// Pointer to the dispersion model object for this parameter
	DispersionModel* dispersion;

	Parameter();
	Parameter(double);
	Parameter(double, bool);

	/// Method to set a minimum value
	void set_min(double);
	/// Method to set a maximum value
	void set_max(double);
	/// Method to get weight points for this parameter
	void get_weights(vector<WeightPoint>&);
	/// Returns the value of the parameter
	double operator()();
	/// Sets the value of the parameter
	double operator=(double);
};
#endif
