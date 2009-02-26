/**
 * SquareWell Structure factor 
 * @author: Jae Hie Cho / UTK
 */

#include "SquareWell.h"
#include "libStructureFactor.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>


/**
 * Function to evaluate 1D scattering function
 * @param pars: parameters of the SquareWellStruct
 * @param q: q-value
 * @return: function value
 */
double SquareWell_analytical_1D(SquareWellParameters *pars, double q) {
	double dp[4];

	dp[0] = pars->radius;
	dp[1] = pars->volfraction;
	dp[2] = pars->welldepth;
	dp[3] = pars->wellwidth;
	
	return SquareWellStruct(dp, q);
}
    
/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the SquareWellStruct
 * @param q: q-value
 * @return: function value
 */
double SquareWell_analytical_2D(SquareWellParameters *pars, double q, double phi) {
	return SquareWell_analytical_1D(pars,q);
}

double SquareWell_analytical_2DXY(SquareWellParameters *pars, double qx, double qy){
	return SquareWell_analytical_1D(pars,sqrt(qx*qx+qy*qy));	
}
