#ifndef MODEL_CLASS_H
#define MODEL_CLASS_H

extern "C" {
	#include "cylinder.h"
}

class Cylinder {

public:
	// Model parameters
	CylinderParameters parameters;

	// Constructor
	Cylinder();

	// Operators to get I(Q)
	double operator()(double q);
	double operator()(double qx, double qy);

};

#endif
