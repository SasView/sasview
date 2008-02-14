#include "simcylinder.h"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#include <memory.h>
#include "modelCalculations.h"
#include "libCylinder.h"

double test_analytical_2D(SimCylinderParameters *pars, double q, double phi) {
	double cyl_x, cyl_y, cyl_z;
	double q_x, q_y, q_z, lenq;
	double theta, alpha, f, vol, sin_val, cos_val;
	double answer;
        
    // Cylinder orientation
    cyl_x = sin(pars->theta) * cos(pars->phi);
    cyl_y = sin(pars->theta) * sin(pars->phi);
    cyl_z = cos(pars->theta);
     
    // q orientation
    
    q_x = cos(phi);
    q_y = sin(phi);
    q_z = 0;
    
    // Length of q vector
    //lenq = sqrt(q_x*q_x + q_y*q_y + q_z*q_z);
    
    // Normalize unit vector q
    //q_x = q_x/lenq;
    //q_y = q_y/lenq;
    //q_z = q_z/lenq;
    
    // Compute the angle btw vector q and the
    // axis of the cylinder
    cos_val = cyl_x*q_x + cyl_y*q_y + cyl_z*q_z;
    
    // The following test should always pass
    if (fabs(cos_val)>1.0) {
    	printf("cyl_ana_2D: Unexpected error: cos(alpha)>1\n");
     	return 0;
    }
    
	alpha = acos( cos_val );
	
	// Call the IGOR library function to get the kernel
	answer = acos(-1.0)/2.0 * CylKernel(q, pars->radius, pars->length/2.0, alpha)/sin(alpha);
	
	//normalize by cylinder volume
	//NOTE that for this (Fournet) definition of the integral, one must MULTIPLY by Vcyl
    vol = acos(-1.0) * pars->radius * pars->radius * pars->length;
	answer *= vol;
	
	//Scale
	answer *= pars->scale;
	
	//convert to [cm-1]
	//answer *= 1.0e8;
	
	return answer;
}


/// 1D scattering function
double simcylinder_analytical_1D(SimCylinderParameters *pars, double q) {
	/***
	 * Things to keep here:
	 * 	- volume calc
	 *  - point generation
	 *  
	 */
	
	// Check if Rho array is available
	int volume_points;
	int r_points;
	int ptsGenerated;
	
	double r_step;
	double vol;
	double bin_width;
	double twopiq;
	double tmp;
		
	//printf("returning %g %g\n",test_analytical_2D(pars, q, 0.0), pars->length);
	return test_analytical_2D(pars, q, 0.0);
	
	
	// These should be parameters
	vol = 1.0*acos(-1.0)*pars->radius*pars->radius*pars->length;
	
	
	r_points      = pars->calcPars.r_points;
	volume_points = pars->calcPars.volume_points;
	
	if(pars->calcPars.isPointMemAllocated==0) {
		
		// Call modelCalc function here to init_volume
		
		//twopiq        = (2*acos(-1.0)*pars->qmax);
		//tmp           = twopiq*twopiq*twopiq*vol;
		//volume_points = (int) floor(tmp);
		//r_points = (int) floor(10.0*pow(tmp,0.3333));
		//r_points      = (int) floor(pow(tmp,0.3333));
		//printf("v, r = %d, %d\n",volume_points, r_points); 
		
		// TEST
		volume_points = 1000;
		r_points = 1000;
		
		pars->calcPars.volume_points = volume_points;
		pars->calcPars.r_points      = r_points;
		
		// Memory allocation
		pars->calcPars.points = (SpacePoint*)malloc(volume_points*sizeof(SpacePoint));
		if(pars->calcPars.points==NULL) {
			printf("Problem allocating memory for 1D volume points\n");
			return -1.0;
		}
		pars->calcPars.isPointMemAllocated=1;
	}

    r_step = sqrt(pars->radius*pars->radius*4.0+pars->length*pars->length)/(double)r_points;
	
	//printf("step=%g  r=%g  l=%g\n", r_step, pars->radius, pars->length);
	if(pars->calcPars.isRhoAvailable==0) {
		// Generate random points accross the volume
		ptsGenerated = simcylinder_generatePoints(pars->calcPars.points, volume_points, pars->radius, pars->length);
		
		// Consistency check
		if(ptsGenerated <= 0) {
			// Set error code here
			return 0;
		}
		
		// Allocate memory
		
		pars->calcPars.rho = (double*) malloc(r_points*sizeof(double));
		if(pars->calcPars.rho==NULL){
			printf("Problem allocating memory for 1D correlation points\n");
			return 0;
		}
		
				
		if(modelcalculations_calculatePairCorrelation_1D(pars->calcPars.points, volume_points, pars->calcPars.rho, r_points, r_step)<=0){
			printf("Error occured!\n");
			return 0;
		};
		pars->calcPars.isRhoAvailable=1;
	} 
	
	// Calculate I(q,phi) and return that value
	
	return acos(-1.0)/2.0*modelcalculations_calculateIq_1D(pars->calcPars.rho, r_points, r_step, q) * vol;

}

/// 1D scattering function
double simcylinder_analytical_2D(SimCylinderParameters *pars, double q, double phi) {
	// Check if Rho array is available
	int volume_points;
	int r_points;
	int ptsGenerated;
	double bin_width;
	double r_step;
	double vol;
	double retval;
	
	// These should be parameters
	//r_points      = pars->calcPars.r_points;
	//volume_points = pars->calcPars.volume_points;
	volume_points = 50000;
	r_points = 100;
	if(pars->calcPars.isPointMemAllocated_2D==0) {
		//volume_points = 1000;
		//r_points = 100;
		pars->calcPars.points_2D = (SpacePoint*)malloc(volume_points*sizeof(SpacePoint));
		if(pars->calcPars.points_2D==NULL) {
			printf("Problem allocating memory for 2D volume points\n");
			return -1.0;
		}
		pars->calcPars.isPointMemAllocated_2D=1;
	}
		  
    r_step = sqrt(pars->radius*pars->radius*4.0+pars->length*pars->length)/(double)r_points;
	if(pars->calcPars.isRhoAvailable_2D==0) {
	    // Initialize random number generator 
		int seed;    
		seed = 10000;
		srand(seed);
		
		// Generate random points accross the volume
		ptsGenerated = simcylinder_generatePoints(pars->calcPars.points_2D, volume_points, pars->radius, pars->length);
		
		// Calculate correlation function
		pars->calcPars.rho_2D = (float*) malloc(r_points*r_points*sizeof(float));
		if(pars->calcPars.rho_2D==NULL){
			printf("Problem allocating memory for 2D correlations points\n");
			return -1.0;
		}
		//if(modelcalculations_calculatePairCorrelation_2D(pars->calcPars.points_2D, volume_points, pars->calcPars.rho_2D, r_points, r_step)==NULL){
		if(modelcalculations_calculatePairCorrelation_2D_vector(pars->calcPars.points_2D, 
			volume_points, pars->calcPars.rho_2D, r_points, r_step,
			pars->theta, pars->phi,0.0)==0){
			return 0;
		};
		pars->calcPars.isRhoAvailable_2D=1;
	} 
	// Calculate I(q,phi) and return that value
	vol = acos(-1.0)*pars->radius*pars->radius*pars->length;
	
	//printf("in ana_2D %f %f\n",q, phi);
	retval = modelcalculations_calculateIq_2D(pars->calcPars.rho_2D, r_points, r_step, q, phi)*vol;	
	//printf("I=%g %f %f\n",retval, q, pars->theta);
	return acos(-1.0)/2.0*retval;
}

/// 1D scattering function
double simcylinder_analytical_2D_3Darray(SimCylinderParameters *pars, double q, double phi) {
	// Check if Rho array is available
	int volume_points;
	int r_points;
	int ptsGenerated;
	double bin_width;
	double r_step;
	double vol;
	
	// These should be parameters
	volume_points = 5000;
	r_points = 100;
	
	if(pars->calcPars.isPointMemAllocated_2D==0) {
		pars->calcPars.points_2D = (SpacePoint*)malloc(volume_points*sizeof(SpacePoint));
		if(pars->calcPars.points_2D==NULL) {
			printf("Problem allocating memory for 2D volume points\n");
			return -1.0;
		}
		pars->calcPars.isPointMemAllocated_2D=1;
	}
		  
    r_step = sqrt(pars->radius*pars->radius*4.0+pars->length*pars->length)/(double)r_points;
	
	if(pars->calcPars.isRhoAvailable_2D==0) {
	    // Initialize random number generator 
		int seed;    
		seed = 10000;
		srand(seed);
		 
		// Generate random points accross the volume
		ptsGenerated = simcylinder_generatePoints(pars->calcPars.points_2D, volume_points, pars->radius, pars->length);
		
		// Calculate correlation function
		// TODO: Check memory leaks
		printf("A\n");
		pars->calcPars.rho_2D = (float*) malloc(r_points*r_points*r_points*sizeof(float));
		if(pars->calcPars.rho_2D==NULL){
			printf("Problem allocating memory for 2D correlations points\n");
			return -1.0;
		}
		printf("B\n");
		if(modelcalculations_calculatePairCorrelation_2D_3Darray(pars->calcPars.points_2D, 
			volume_points, pars->calcPars.rho_2D, r_points, r_step)<0){
			return 0;
		};
		printf("C\n");
		pars->calcPars.isRhoAvailable_2D=1;
	} 
	// Calculate I(q,phi) and return that value
	vol = acos(-1.0)*pars->radius*pars->radius*pars->length;
	
	printf("in ana_2D %f %f\n",q, phi);
	return modelcalculations_calculateIq_2D_3Darray(pars->calcPars.rho_2D, r_points, r_step, q, phi)*vol;
	
	
}


/**
 * Generate points randomly accross the volume
 * @param points [SpacePoint*] Array of 3D points to be filled
 * @param n [int] Number of points to generat
 * @param radius [double] Radius of the sphere
 * @return Number of points generated
 */
int simcylinder_generatePoints(SpacePoint * points, int n, double radius, double length) {
	int i;
	int testcounter;
	double x, y, z;
	
	// Create points	
	// To have a uniform density, you want to generate
	// random points in a box and keep only those that are
	// within the volume.
	
	// Initialize random number generator
	int seed;    
	time_t now;
	
	time(&now);
	//seed = 10000;
	
	seed = (int)floor(fmod(now,10000));
	//seed = 10009;
	srand(seed);	
	printf("Seed = %i\n", seed);
	
	testcounter = 0;
		
	memset(points,0,n*sizeof(SpacePoint));
	for(i=0;i<n;i++) {
		// Generate in a box centered around zero
		x = (2.0*((double)rand())/((double)(RAND_MAX)+(double)(1))-1.0) * radius;
		y = (2.0*((double)rand())/((double)(RAND_MAX)+(double)(1))-1.0) * radius;
		z = (2.0*((double)rand())/((double)(RAND_MAX)+(double)(1))-1.0) * length/2.0;
		
		// reject those that are not within the volume
		if( sqrt(x*x+y*y) < radius && fabs(z)<length/2.0) {
			points[i].x =  x;
			points[i].y =  y;
			points[i].z =  z;
			testcounter++;
		} else {
			i--;
		}
	}
	//printf("test counter = %d\n", testcounter);
	
	// Consistency check
	if(testcounter != n) {
		return -1;
	}
		
	return testcounter;
}
