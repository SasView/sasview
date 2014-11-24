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

/**
 * Scattering model classes
 * The classes use the IGOR library found in
 *   sansmodels/src/libigor
 *
 */

#include <math.h>
#include "parameters.hh"
#include <stdio.h>
#include <iostream>
using namespace std;
#include "micelleSphCore.h"

extern "C" {
#include "libSphere.h"
}


MicelleSphCoreModel :: MicelleSphCoreModel() {
    scale      = Parameter(1.0);
    ndensity   = Parameter(8.94e15);
    ndensity.set_min(0.0);
    v_core     = Parameter(62624.0);
    v_core.set_min(0.0);
    v_corona   = Parameter(61940.0);
    v_corona.set_min(0.0);
    rho_solv   = Parameter(6.4e-6);
    rho_core   = Parameter(3.4e-7);
    rho_corona = Parameter(8.0e-7);
    radius_core = Parameter(45.0, true);
    radius_core.set_min(0.0);
    radius_gyr = Parameter(20.0, true);
    radius_gyr.set_min(0.0);
    d_penetration = Parameter(1.0);
    d_penetration.set_min(0.0);
    n_aggreg = Parameter(6.0);
    n_aggreg.set_min(1.0);
    background = Parameter(0.0);
}


/**
 * Function to evaluate 1D scattering function
 * @param q: q-value
 * @return: function value
 */
double MicelleSphCoreModel :: operator()(double q) {
	double dp[12];
	
	// Fill parameter array
	// Add the background after averaging
        dp[0] = scale();
        dp[1] = ndensity();
        dp[2] = v_core();
        dp[3] = v_corona();
        dp[4] = rho_solv();
        dp[5] = rho_core();
        dp[6] = rho_corona();
        dp[7] = radius_core();
        dp[8] = radius_gyr();
        dp[9] = d_penetration();
        dp[10] = n_aggreg();
        dp[11] = 0.0;


        // Get the dispersion points for the core radius
        vector<WeightPoint> weights_rcore;
        radius_core.get_weights(weights_rcore);

         // Get the dispersion points for the gyration radius
        vector<WeightPoint> weights_rgyr;
        radius_gyr.get_weights(weights_rgyr);

       // Perform the computation, with all weight points
        double sum = 0.0;
        double norm = 0.0;
        double vol = 0.0;
	double vol_micelle = 0.0;

        // Loop over core radius weight points
        for(int i=0; i< (int)weights_rcore.size(); i++) {

            dp[7] = weights_rcore[i].value;

            // Loop over gyration radius weight points
            for(int j=0; j< (int)weights_rgyr.size(); j++) {

                dp[8] = weights_rgyr[j].value;
		
		//cout << "\n loop i,j = " << i << "  " << j;
		//cout << "\n radius_core: value weight = " << weights_rcore[i].value << "  " << weights_rcore[i].weight;
		//cout << "\n radius_gyr:  value weight = " << weights_rgyr[j].value << "  " << weights_rgyr[j].weight;
                //cout << "\n";

                vol_micelle = pow(weights_rcore[i].value+weights_rgyr[j].value,3);

                //Un-normalize SphereForm by volume
                sum += weights_rcore[i].weight *  weights_rgyr[j].weight *
		       MicelleSphericalCore(dp, q) *
                       vol_micelle;
      
                //Find average volume
                vol += weights_rcore[i].weight * weights_rgyr[j].weight * vol_micelle;

                norm += weights_rcore[i].weight * weights_rgyr[j].weight;
	    }	

        }

        if (vol != 0.0 && norm != 0.0) {
             //Re-normalize by avg volume
             sum = sum/(vol/norm);}
	     
        return sum/norm + background();

}


/**
 * Function to evaluate 2D scattering function
 * @param q_x: value of Q along x
 * @param q_y: value of Q along y
 * @return: function value
 */
double MicelleSphCoreModel :: operator()(double qx, double qy) {
	double q = sqrt(qx*qx + qy*qy);
	return (*this).operator()(q);
}


/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the model
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double MicelleSphCoreModel :: evaluate_rphi(double q, double phi) {
	return (*this).operator()(q);
}


/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double MicelleSphCoreModel :: calculate_ER() {
	return 1.0;
}


/**
 * Function to calculate particle volume/total volume for shape models:
 *	Most case returns 1 but for example for the vesicle model it is 
 *	(total volume - core volume)/total volume 
 *	(< 1 depending on the thickness).
 * @return: effective radius value
 */
double MicelleSphCoreModel :: calculate_VR() {
  return 1.0;
}
