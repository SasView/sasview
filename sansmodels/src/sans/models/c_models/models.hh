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
#ifndef MODEL_CLASS_H
#define MODEL_CLASS_H

#include <vector>
#include "parameters.hh"
extern "C" {
	#include "cylinder.h"
}

using namespace std;

class Cylinder{

public:
	// Model parameters
	Parameter radius;
	Parameter scale;
	Parameter length;
	Parameter contrast;
	Parameter background;
	Parameter cyl_theta;
	Parameter cyl_phi;
	// TODO: replace this by an array of parameters

	// Constructor
	Cylinder();

	// Operators to get I(Q)
	double operator()(double q);
	double operator()(double qx, double qy);
	double evaluate_rphi(double q, double phi);
};

#endif
