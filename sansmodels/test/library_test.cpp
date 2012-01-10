/*
 * Sanity check to verify that one can link to the library
 * and get models.
 *
 */
#include <stdio.h>
#include <iostream>
#include "cylinder.h"
#include <math.h>
int main( int argc, const char* argv[] )
{
	std::cout << "Testing Cylinder Model" << std::endl;
	CylinderModel * model = new CylinderModel();
	double value = (*model)(0.001);
	double reference = 450.355;

	std::cout << "   I(q=0.001) = " << value;
	if (fabs(value-reference)>0.01)
		std::cout << "  ERROR: Expected " << reference << std::endl;
	else
		std::cout << "  OK" << std::endl;
}
