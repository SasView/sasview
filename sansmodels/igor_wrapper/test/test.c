#include "../include/danse.h"
#include <stdio.h>

int main(){
	double output;
	double pars[11];	
	double q, phi;
	double theta_vals[17];
	double theta_w[17];
	double phi_vals[17];
	double phi_w[17];
	int i;
	
	pars[0] = 1.0;
	pars[1] = 20.0; // radius
	pars[2] = 400.0; // length
	pars[3] = 1.0;  // contrast
	pars[4] = 0.0;  // bck
	pars[5] = 1.57; //theta
	pars[6] = 0.0;  // phi
	pars[7] = 0.0;  // disp theta
	pars[8] = 0.0;  // disp phi
	pars[9] = 0.0;  // disp radius
	pars[10] = 0.0;
	
	theta_vals[0] = 0.01;
	theta_vals[1] = 0.1;
	theta_vals[2] = 0.2;
	theta_vals[3] = 0.3;
	theta_vals[4] = 0.4;
	theta_vals[5] = 0.5;
	theta_vals[6] = 0.6;
	theta_vals[7] = 0.7;
	theta_vals[8] = 0.8;
	theta_vals[9] = 0.9;
	theta_vals[10] = 1.0;
	theta_vals[11] = 1.1;
	theta_vals[12] = 1.2;
	theta_vals[13] = 1.3;
	theta_vals[14] = 1.4;
	theta_vals[15] = 1.5;
	theta_vals[16] = 1.6;
	
	for(i=0; i<17; i++) {
	   theta_w[i] = 1.0;
	}
	
	q = 0.025;
	phi = 0.0;
	
	// Testing oriented cylinder
	output = oriented_cylinder_2D(pars, q, phi);
	printf("oriented output = %g\n", output);
	
	// Testing dispersed with no dispersion
	output = disperse_cylinder_analytical_2D(pars, q, phi);
	printf("disp output     = %g\n", output);

	// Testing dispersed with dispersion
	pars[10] = 100.0;
	pars[7]  = 3.0;
	output = disperse_cylinder_analytical_2D(pars, q, phi);
	printf("disp output     = %g\n", output);

	// Testing input dist
	pars[10] = 0.0;
	pars[7]  = 0.0;
	pars[1]  = 20.0;
	output = cylinder_Weights(pars, phi_vals, phi_w, 0, 
								theta_vals, theta_w, 17, 
								q, phi); 
	printf("weight output     = %g\n", output);

}