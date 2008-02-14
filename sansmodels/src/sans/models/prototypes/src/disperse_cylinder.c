/**
 * Scattering model for a cylinder
 * @author: Mathieu Doucet / UTK
 */

#include "cylinder.h"
#include "disperse_cylinder.h"
#include <math.h>
#include "libCylinder.h"

double c_disperser( double (*eval)(), double dp[], int n_pars, 
					int *idList, double *sigmaList, int n_pts, double q, double phi );

/**
 * Function to evaluate 1D scattering function
 * @param pars: parameters of the cylinder
 * @param q: q-value
 * @return: function value
 */
double disperse_cylinder_analytical_1D(DispCylinderParameters *pars, double q) {
	double dp[5];
	
	// Fill paramater array
	dp[0] = pars->scale;
	dp[1] = pars->radius;
	dp[2] = pars->length;
	dp[3] = pars->contrast;
	dp[4] = pars->background;
	
	return CylinderForm(dp, q);
}
	
double disp_cyl_run(double pars[], double q, double phi) {
	CylinderParameters danse_pars;
	danse_pars.scale        = pars[0];
	danse_pars.radius       = pars[1];
	danse_pars.length       = pars[2];
	danse_pars.contrast     = pars[3];
	danse_pars.background   = pars[4];
	danse_pars.cyl_theta    = pars[5];
	danse_pars.cyl_phi      = pars[6];

	return cylinder_analytical_2D(&danse_pars, q, phi);		
		
}
	
/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the cylinder
 * @param q: q-value
 * @return: function value
 */
double disperse_cylinder_analytical_2D(DispCylinderParameters *pars, double q, double phi) {
	CylinderParameters cyl_pars;
	double dp[6];
	int paramList[3];
	double sigmaList[3];
	int npts;
	
	
	// Fill paramater struct
	dp[0] = pars->scale;
	dp[1] = pars->radius;
	dp[2] = pars->length;
	dp[3] = pars->contrast;
	dp[4] = pars->background;
	dp[6] = pars->cyl_phi;
	dp[5] = pars->cyl_theta;
	
	paramList[0] = 6;
	paramList[1] = 5;
	paramList[2] = 1;
	
	
	sigmaList[0] = pars->sigma_phi;
	sigmaList[1] = pars->sigma_theta;
	sigmaList[2] = pars->sigma_radius;
	
	npts = (int)(floor(pars->n_pts));
	
	return c_disperser( &disp_cyl_run, &dp, 3, 
					paramList, sigmaList, npts, q, phi ); 

	
}
    