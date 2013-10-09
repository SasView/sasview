
/*
	This software was developed by the University of Tennessee as part of the
	Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
	project funded by the US National Science Foundation.

	If you use DANSE applications to do scientific research that leads to
	publication, we ask that you acknowledge the use of the software with the
	following sentence:

	"This work benefited from DANSE software developed under NSF award DMR-0520547."

	copyright 2008, University of Tennessee
    
    SHIBAYAMA-GEISSLER TWO-LENGTH SCALE SCATTERING FUNCTION FOR GELS

    See Sibayama, Tanaka & Han, J Chem Phys, (1992), 97(9), 6829-6841
    or  Mallam, Horkay, Hecht, Rennie & Geissler, Macromol, (1991), 24, 543

    Ported to C++ from Fortran by Robert Whitley (2012)
*/

#include <math.h>
#include "parameters.hh"
#include <stdio.h>
using namespace std;
#include "GelFit.h"

GelFitModel::GelFitModel()
{
    lScale = Parameter(3.5);
    gScale = Parameter(1.7);
    zeta = Parameter(16.0);
    radius = Parameter(104.0,true);
    radius.set_min(2.0);
    scale = Parameter(2.0,true);
    background = Parameter(0.01);
}

double GelFitModel::operator()(double q) 
{
    double dp[3];
    dp[0] = zeta();
    dp[1] = radius();
    dp[2] = scale();
    
    if (dp[2] <= 0)
    {
        //cout << "\n\nThe Scaling Exponent must be > 0";
        //cout << "\nWill set to 2.0";
        dp[2] = 2.0;
    }

    // Lorentzian Term
    ////////////////////////double a(x[i]*x[i]*zeta*zeta);
    double a(q*q*dp[0]*dp[0]);
    double b(1.0 + (((dp[2] + 1.0)/3.0)*a) );
    double c(pow(b, (dp[2]/2.0) ) );
    
    // Exponential Term
    ////////////////////////double d(x[i]*x[i]*rg*rg);
    double d(q*q*dp[1]*dp[1]);
    double e(-1.0*(d/3.0) );
    double f(exp(e));
        
        // Scattering Law
    double result((lScale()/c) + (gScale()*f) + background());
    return result;
}


/**
 * Function to evaluate 2D scattering function
 * @param q_x: value of Q along x
 * @param q_y: value of Q along y
 * @return: function value
 */
double GelFitModel::operator()(double qx, double qy) 
{
  double q = sqrt(qx*qx + qy*qy);
  return (*this).operator()(q);
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the cylinder
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double GelFitModel::evaluate_rphi(double q, double phi) 
{
  double qx = q*cos(phi);
  double qy = q*sin(phi);
  return (*this).operator()(qx, qy);
}
/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double GelFitModel::calculate_ER() 
{
  //NOT implemented yet!!!
  return 0.0;
}
double GelFitModel::calculate_VR() 
{
  return 1.0;
}