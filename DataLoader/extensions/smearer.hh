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
#ifndef SMEARER_CLASS_H
#define SMEARER_CLASS_H

#include <vector>

using namespace std;

/**
 * Base smearer class, implementing the matrix multiplication only
 */
class BaseSmearer {
protected:
	bool has_matrix;
    // Smearing matrix
    vector<double>* weights;
    // Q_min (Min Q-value for I(q))
    double qmin;
    // Q_max (Max Q_value for I(q))
    double qmax;
    // Number of Q bins
    int nbins;

public:
    // Constructor
    BaseSmearer(double qmin, double qmax, int nbins);
	// Smear function
	virtual void smear(double *, double *, int, int);
	// Compute the smearing matrix
	virtual void compute_matrix(){};
	// Utility function to check the number of bins
	int get_nbins() { return nbins; }
};


/**
 * Slit smearer class
 */
class SlitSmearer : public BaseSmearer {

protected:
    // Number of points used in the smearing computation
    static const int npts   = 10000;

public:
    // Slit width in Q units
    double width;
    // Slit height in Q units
    double height;

    // Constructor
	SlitSmearer(double width, double height, double qmin, double qmax, int nbins);
	// Compute the smearing matrix
	virtual void compute_matrix();
};


/**
 * Point smearer class
 */
class QSmearer : public BaseSmearer {

protected:
    // Standard deviation in Q [A-1]
    double* width;

public:

    // Constructor
    QSmearer(double* width,double qmin, double qmax, int nbins);
	// Compute the smearing matrix
	virtual void compute_matrix();
};

#endif
