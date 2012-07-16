
/*
	This software was developed by the University of Tennessee as part of the
	Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
	project funded by the US National Science Foundation.

	If you use DANSE applications to do scientific research that leads to
	publication, we ask that you acknowledge the use of the software with the
	following sentence:

	"This work benefited from DANSE software developed under NSF award DMR-0520547."

	copyright 2008, University of Tennessee

    See Schmidt, J Appl Cryst, 24, (1991), 414-435, Eqn (19)
    See Hurd, Schaefer & Martin, 35, (1987), 2361-2364

    Ported to C++ from Fortran by Robert Whitley (2012)
*/

#include <math.h>
#include "parameters.hh"
#include <stdio.h>
#include "FractalQtoN.h"
using namespace std;

FractalO_Z::FractalO_Z()
{
    scale = Parameter(10000.0, true);
    m_fractal = Parameter(1.8);
    cluster_rg = Parameter(3250.0);
    s_fractal = Parameter(2.5);
    primary_rg = Parameter(82.0);
    background = Parameter(0.01);
}

double FractalO_Z :: operator()(double q)
{
    double dp[3];
    dp[0] = m_fractal();
    dp[1] = s_fractal();
    
    
    if (dp[0] <= 0)
    {
        //std::cout << "\n\nThe mass fractal dimension must be > 0!";
        //std::cout << "\nWill set to 3.";
        dp[0] = 3.0;
    }
    else 
    {
        if (dp[0] > 6)
        {
            //std::cout << "\n\nThe mass fractal dimension must be <= 6!";
            //std::cout << "\nWill be set to 3."; 
            dp[0] = 3.0;
        }
    }
    
    if (dp[1] <= 0)
    {
        //std::cout << "\n\nThe surface dimension must be > 0!";
        //std::cout << "\nWill be set to 2.";
        dp[1] = 2.0;
    }
    else
    {
        if (dp[1] > 6)
        {
            //std::cout << "\n\nThe surface dimension must be <= 6!";
            //std::cout << "\nWill be set to 2.";
            dp[1] = 2.0;
        }
    }
    
    double a(dp[0]/2.0);
    double b((cluster_rg() * cluster_rg())/(3.0*a) );
    
    // If C goes negative, it will crash with undefined exponentiation.
    // So (Ds + Dm) <= 6
    // c = ((ds-6.0)/-2.0)-a
    if ((dp[1] > (6.0-dp[0])) && (primary_rg() > 0.0))
    {
        dp[1] = 6.0 - dp[0];
        //std::cout << "\n\nThe surface fractal dimension must be <= (6-Dm)!\n";
        //std::cout << setprecision(5) << fixed << dp[1];
    }
    
    // c = (ds -6.0 + dm)/-2.0;
    double c = (6.0 - dp[1] - dp[0])/2.0;
    double d(0.0);
    
    // If c = 0 then it will crash with a floating divide by zero.
    if (c == 0)
    {
        d = 1.0e+37;
    }
    else
    {
        d = (primary_rg() * primary_rg()) / (3.0 * c);
    }

    double eVar = q*q*b;
    double fVar = q*q*d;
    double g = pow((1.0+eVar),a);
    double h = pow((1.0+fVar),c);
    double i = g*h;
    double result((scale()/i) + background() );
    return result;
}


/**
 * Function to evaluate 2D scattering function
 * @param q_x: value of Q along x
 * @param q_y: value of Q along y
 * @return: function value
 */
double FractalO_Z :: operator()(double qx, double qy) {
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
double FractalO_Z :: evaluate_rphi(double q, double phi) {
  double qx = q*cos(phi);
  double qy = q*sin(phi);
  return (*this).operator()(qx, qy);
}
/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double FractalO_Z :: calculate_ER() {
  //NOT implemented yet!!!
  return 0.0;
}
double FractalO_Z :: calculate_VR() {
  return 1.0;
}