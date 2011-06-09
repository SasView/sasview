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
#ifndef SMEARER2D_HELPER_CLASS_H
#define SMEARER2D_HELPER_CLASS_H

#include <vector>

using namespace std;

/**
 * Base smearer class, implementing the matrix multiplication only
 */
class Smearer_helper {
protected:
	// Smearing matrix
	vector<double>* weights;
	vector<double>* qx_out;
	vector<double>* qy_out;
	// Q vector
	double* qx_values;
	double* qy_values;
	double* dqx_values;
	double* dqy_values;
    // r limit
    double rlimit;
    // Numbers
    int npoints;
    int nrbins;
    int nphibins;

public:
    // Constructor
	Smearer_helper(int npoints, double* qx, double* qy, double* dqx, double* dqy,
			double rlimit, int nrbins, int nphibins);
	// Smear function
	virtual void smear2d(double *weights, double *qx_out, double *qy_out);
};

#endif
