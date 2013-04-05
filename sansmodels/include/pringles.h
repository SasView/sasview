/**
 * (c) 2013 / Andrew J Jackson / andrew.jackson@esss.se
 *
 * Model for "pringles" particle from K. Edler @ Bath University
 *
 */

#if !defined(pringles_h)
#define pringles_h
#include "parameters.hh"

//[PYTHONCLASS] = PringlesModel
//[DISP_PARAMS] = radius,thickness,alpha,beta,
//[DESCRIPTION] = <text> Pringles model for K Edler. Represents a disc that is bent in two directions. </text>
//[FIXED]= <text> radius.width; thickness.width; alpha.width; beta.width</text>
//[ORIENTATION_PARAMS]= <text> </text>

class PringlesModel {
public:
	//[DEFAULT]=scale=1.0
	Parameter scale;
	//[DEFAULT]=radius=60.0 [A]
	Parameter radius;
	//[DEFAULT]=thickness=10.00 [A]
	Parameter thickness;
	//[DEFAULT]=alpha=0.001 [rad]
	Parameter alpha;
	//[DEFAULT]=beta=0.02 [rad]
	Parameter beta;
	//[DEFAULT]=sld_pringle=1.0e-6 [A^(-2)]
	Parameter sld_pringle;
	//[DEFAULT]=sld_solvent=6.35e-6 [A^(-2)]
	Parameter sld_solvent;
	//[DEFAULT]=background=0.0 [1/cm]
	Parameter background;
	//Constructor
	PringlesModel();
	// Operators to get I(Q)
	double operator()(double q);
	double operator()(double qx, double qy);
	double calculate_ER();
	double calculate_VR();
	double evaluate_rphi(double q, double phi);
};

static double pringle_form(double dp[], double q);
static double pringle_kernel(double dp[], double q, double phi);
static double pringleC(double dp[], double q, double n, double phi);
static double pringleS(double dp[], double q, double n, double phi);
#endif
