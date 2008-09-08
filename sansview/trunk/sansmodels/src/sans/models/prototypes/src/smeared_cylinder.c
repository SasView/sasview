/**
 * Scattering model for a cylinder
 * @author: Mathieu Doucet / UTK
 */

#include "cylinder.h"
#include "smeared_cylinder.h"
#include <math.h>
#include "libCylinder.h"


/**
 * Function to evaluate 1D scattering function
 * @param pars: parameters of the cylinder
 * @param q: q-value
 * @return: function value
 */
double smeared_cylinder_analytical_1D(SmearCylinderParameters *pars, double q) {
	double dp[5];
	int i_r;
	double r_0, r, step_r, min_r;
	int npts;
	double weight, func, norm;
	
	// Fill paramater array
	dp[0] = pars->scale;
	dp[1] = pars->radius;
	dp[2] = pars->length;
	dp[3] = pars->contrast;
	dp[4] = pars->background;
	
	if(pars->sigma_radius==0) {
		return CylinderForm(dp, q);
	}
	
	// Central value is the current value 
	r_0     = pars->radius;
	
	npts = 100;
	step_r     = 4.0*pars->sigma_radius/npts;
	min_r     = r_0 - 2.0*pars->sigma_radius;
	
	
	norm = 0.0;
	func = 0.0;
	
	for (i_r=0; i_r<100; i_r++) {
			r = min_r + step_r*i_r;
			dp[1] = r;
			
			// Weigth for that position
			weight = smeared_cylinder_dist( r, r_0, pars->sigma_radius );
			norm += weight;
			
			// Evaluate I(q) at that r-value
			func += weight * CylinderForm(dp, q);	
	}
	
	return func/norm;
}
	
	
/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the cylinder
 * @param q: q-value
 * @return: function value
 */
double smeared_cylinder_analytical_2D(SmearCylinderParameters *pars, double q, double phi) {
	CylinderParameters cyl_pars;
	int i_theta, i_phi, i_r;
	int n_theta, n_phi, n_r;
	double theta_0, phi_0, r_0;
	int npts;
	double weight_theta, weight_phi, weight_r;
	double min_theta, min_phi, min_r;
	double step_theta, step_phi, step_r;
	double func, norm;
	double n_width = 3.0;
	
	// Fill paramater struct
	cyl_pars.scale      = pars->scale;
	cyl_pars.radius     = pars->radius;
	cyl_pars.length     = pars->length;
	cyl_pars.contrast   = pars->contrast;
	cyl_pars.background = pars->background;
	cyl_pars.cyl_phi    = pars->cyl_phi;
	cyl_pars.cyl_theta  = pars->cyl_theta;
	
	theta_0 = pars->cyl_theta;
	phi_0   = pars->cyl_phi;
	r_0     = pars->radius;
	
	npts = 25;
	step_theta = 2.0*n_width*pars->sigma_theta/npts;
	step_phi   = 2.0*n_width*pars->sigma_phi/npts;
	step_r     = 2.0*n_width*pars->sigma_radius/npts;
	
	if (step_theta>0) {
		n_theta = npts;
	} else {
		n_theta = 1;
	}
	
	if (step_phi>0) {
		n_phi = npts;
	} else {
		n_phi = 1;
	}
	
	if (step_r>0) {
		n_r = npts;
	} else {
		n_r = 1;
	}
	
	
	
	min_theta = theta_0 - n_width*pars->sigma_theta;
	min_phi   = phi_0 - n_width*pars->sigma_phi;
	min_r     = r_0 - n_width*pars->sigma_radius;
	
	func = 0.0;
	norm = 0.0;
	
	for (i_theta=0; i_theta<n_theta; i_theta++) {
			
		// Weight for that position
		if(pars->sigma_theta>0) {
			cyl_pars.cyl_theta = min_theta + step_theta*i_theta;
			weight_theta = smeared_cylinder_dist( cyl_pars.cyl_theta, theta_0, pars->sigma_theta );
		} else {
			weight_theta = 1.0;
		}
						
		for (i_phi=0; i_phi<n_phi; i_phi++) {
				
			// Weight for that position
			if(pars->sigma_phi>0) {
				cyl_pars.cyl_phi = min_phi + step_phi*i_phi;
				weight_phi = smeared_cylinder_dist( cyl_pars.cyl_phi, phi_0, pars->sigma_phi );
			} else {
				weight_phi = 1.0;
			}
		
			for (i_r=0; i_r<n_r; i_r++) {
				
				if(pars->sigma_radius>0) {
					cyl_pars.radius = min_r + step_r*i_r;
					
					// Weight for that position
					weight_r = smeared_cylinder_dist( cyl_pars.radius, r_0, pars->sigma_radius );
				} else {
					weight_r = 1.0;
				}
					
				// Evaluate I(q) at that r-value
				func += weight_theta * weight_r * weight_phi * cylinder_analytical_2D(&cyl_pars, q, phi);	
				norm += weight_theta * weight_r * weight_phi;
			}
		}
	}
	

	return func/norm;
}
    
double smeared_cylinder_dist( double x, double mean, double sigma ) {
	double vary;
	double expo;
		
	//return 1.0;
		
	vary = x-mean;
    expo = -vary*vary/(2.0*sigma*sigma);
	return exp(expo);

}
