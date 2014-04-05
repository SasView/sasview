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
 *    TODO: add 2D function
 */

#include <math.h>
#include "parameters.hh"
#include <stdio.h>
#include <iostream>
using namespace std;

extern "C" {
    #include "libCylinder.h"
    #include "libStructureFactor.h"
    #include "libmultifunc/libfunc.h"
}
#include "RectangularHollowPrism.h"

// Convenience parameter structure
typedef struct {
    double scale;
    double short_side;
    double b2a_ratio;
    double c2a_ratio;
    double thickness;
    double sldPipe;
    double sldSolv;
    double background;
} RectangularHollowPrismParameters;


RectangularHollowPrismModel :: RectangularHollowPrismModel() {
    scale      = Parameter(1.0);
    short_side = Parameter(35.0, true);
    short_side.set_min(1.0);
    b2a_ratio   = Parameter(1.0, true);
    b2a_ratio.set_min(1.0);
    c2a_ratio   = Parameter(1.0, true);
    c2a_ratio.set_min(1.0);
    thickness = Parameter(1.0, true);
    thickness.set_min(0.0);
    sldPipe   = Parameter(6.3e-6);
    sldSolv   = Parameter(1.0e-6);
    background = Parameter(0.0);
}

/**
 * Function to evaluate 1D scattering function
 * @param q: q-value
 * @return: function value
 */
double RectangularHollowPrismModel :: operator()(double q) {

    double dp[8];

    // Fill parameter array for IGOR library
    // Add the background after averaging
    dp[0] = scale();
    dp[1] = short_side();
    dp[2] = b2a_ratio();
    dp[3] = c2a_ratio();
    dp[4] = thickness();
    dp[5] = sldPipe();
    dp[6] = sldSolv();
    dp[7] = 0.0;

    // Get the dispersion points for a
    vector<WeightPoint> weights_short_side;
    short_side.get_weights(weights_short_side);

    // Get the dispersion points for b/a ratio
    vector<WeightPoint> weights_b2a_ratio;
    b2a_ratio.get_weights(weights_b2a_ratio);

    // Get the dispersion points for c/a ratio
    vector<WeightPoint> weights_c2a_ratio;
    c2a_ratio.get_weights(weights_c2a_ratio);

    // Get the dispersion points for the thickness
    vector<WeightPoint> weights_thickness;
    thickness.get_weights(weights_thickness);

    // Perform the computation, with all weight points
    double sum = 0.0;
    double norm = 0.0;
    double vol = 0.0;

    // Loop over short_side weight points
    for (int i=0; i < (int)weights_short_side.size(); i++) {

        dp[1] = weights_short_side[i].value;

        // Loop over b/a ratios
        for (int j=0; j < (int)weights_b2a_ratio.size(); j++) {

            dp[2] = weights_b2a_ratio[j].value;

            // Loop over c/a ratios
            for (int k=0; k < (int)weights_c2a_ratio.size(); k++) {

                dp[3] = weights_c2a_ratio[k].value;

                // Loop over thicknesses
                for (int l=0; l < (int)weights_thickness.size(); l++) {

                    dp[4] = weights_thickness[l].value;

        	        // Un-normalize  by volume = abc - (a-2*t)*(b-2*t)*(c-2*t)

		            double a = dp[1];
		            double b = dp[1] * dp[2];
		            double c = dp[1] * dp[3];
		            double t = dp[4];
		            double vol_i = a*b*c - (a-2*t)*(b-2*t)*(c-2*t);

        	        sum += weights_short_side[i].weight *
        	               weights_b2a_ratio[j].weight *
        	               weights_c2a_ratio[k].weight *
			               weights_thickness[l].weight *
        	               RectangularHollowPrism(dp, q) *
        	               vol_i;

        	        //Find average volume (ABC)

        	        vol += weights_short_side[i].weight *
        	               weights_b2a_ratio[j].weight *
        	               weights_c2a_ratio[k].weight *
			               weights_thickness[l].weight *
        	               vol_i;

        	        norm += weights_short_side[i].weight *
                	        weights_b2a_ratio[j].weight *
                	        weights_c2a_ratio[k].weight *
			                weights_thickness[l].weight;
                }
            }
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
double RectangularHollowPrismModel :: operator()(double qx, double qy) {
    return 1.0;
}


/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the cylinder
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double RectangularHollowPrismModel :: evaluate_rphi(double q, double phi) {
    double qx = q*cos(phi);
    double qy = q*sin(phi);
    return (*this).operator()(qx, qy);
}

/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double RectangularHollowPrismModel :: calculate_ER() {
    return 1.0;

}
double RectangularHollowPrismModel :: calculate_VR() {
  return 1.0;
}
