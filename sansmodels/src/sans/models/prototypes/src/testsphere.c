#include "testsphere.h"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#include <memory.h>
#include "modelCalculations.h"


/// 1D scattering function
double testsphere_analytical_1D(TestSphereParameters *pars, double q) {
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
		
	// These should be parameters
	vol = 4.0*acos(-1.0)/3.0*pars->radius*pars->radius*pars->radius;
	
	
	r_points      = pars->calcPars.r_points;
	volume_points = pars->calcPars.volume_points;
	
	if(pars->calcPars.isPointMemAllocated==0) {
		
		// Call modelCalc function here to init_volume
		
		twopiq        = (2*acos(-1.0)*pars->qmax);
		tmp           = twopiq*twopiq*twopiq*vol;
		volume_points = (int) floor(tmp);
		//r_points = (int) floor(10.0*pow(tmp,0.3333));
		r_points      = (int) floor(pow(tmp,0.3333));
		printf("v, r = %d, %d\n",volume_points, r_points); 
		
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
	
	if(pars->calcPars.isRhoAvailable==0) {
		// Generate random points accross the volume
		ptsGenerated = testsphere_generatePoints(pars->calcPars.points, volume_points, pars->radius);
		
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
		
		
		// Lump all this in modelCalc function
		
		bin_width = 2.0*pars->radius/r_points;
		
		if(modelcalculations_calculatePairCorrelation_1D(pars->calcPars.points, volume_points, pars->calcPars.rho, r_points, bin_width)<=0){
			printf("Error occured!\n");
			return 0;
		};
		pars->calcPars.isRhoAvailable=1;
	} 
	
	// Calculate I(q,phi) and return that value
	r_step = 2.0*pars->radius/((double)(r_points));
	
	return modelcalculations_calculateIq_1D(pars->calcPars.rho, r_points, r_step, q) * vol;

}
/// 1D scattering function
double testsphere_analytical_2D_3Darray(TestSphereParameters *pars, double q, double phi) {
	// Check if Rho array is available
	int volume_points;
	int r_points;
	int ptsGenerated;
	double bin_width;
	double r_step;
	double vol;
	
	// These should be parameters
	volume_points = 1000;
	r_points = 10;
	
	if(pars->calcPars.isPointMemAllocated_2D==0) {
		pars->calcPars.points_2D = (SpacePoint*)malloc(volume_points*sizeof(SpacePoint));
		if(pars->calcPars.points_2D==NULL) {
			printf("Problem allocating memory for 2D volume points\n");
			return -1.0;
		}
		pars->calcPars.isPointMemAllocated_2D=1;
	}
		  
	//r_step = 2.0*pars->radius/((double)(r_points));
	// Allow negative values....
	r_step = 4.0*pars->radius/((double)(r_points));
	
	if(pars->calcPars.isRhoAvailable_2D==0) {
	    // Initialize random number generator 
		int seed;    
		seed = 10000;
		srand(seed);
		 
		// Generate random points accross the volume
		ptsGenerated = testsphere_generatePoints(pars->calcPars.points_2D, volume_points, pars->radius);
		
		// Calculate correlation function
		pars->calcPars.rho_2D = (float*) malloc(r_points*r_points*r_points*sizeof(float));
		if(pars->calcPars.rho_2D==NULL){
			printf("Problem allocating memory for 2D correlations points\n");
			return -1.0;
		}
		if(modelcalculations_calculatePairCorrelation_2D_3Darray(pars->calcPars.points_2D, volume_points, pars->calcPars.rho_2D, r_points, r_step)==NULL){
			return 0;
		};
		pars->calcPars.isRhoAvailable_2D=1;
	} 
	// Calculate I(q,phi) and return that value
	vol = 4.0*acos(-1.0)/3.0*pars->radius*pars->radius*pars->radius;
	
	//printf("in ana_2D %f %f\n",q, phi);
	return modelcalculations_calculateIq_2D_3Darray(pars->calcPars.rho_2D, r_points, r_step, q, phi)*vol;
	
	
}

/// 1D scattering function
double testsphere_analytical_2D(TestSphereParameters *pars, double q, double phi) {
	// Check if Rho array is available
	int volume_points;
	int r_points;
	int ptsGenerated;
	double bin_width;
	double r_step;
	double vol;
	
	// These should be parameters
	//r_points      = pars->calcPars.r_points;
	//volume_points = pars->calcPars.volume_points;
	volume_points = 5000;
	r_points = 100;
	
	if(pars->calcPars.isPointMemAllocated_2D==0) {
		//volume_points = 2000;
		//r_points = 100;
		//pars->calcPars.volume_points = volume_points;
		//pars->calcPars.r_points      = r_points;
		pars->calcPars.points_2D = (SpacePoint*)malloc(volume_points*sizeof(SpacePoint));
		if(pars->calcPars.points_2D==NULL) {
			printf("Problem allocating memory for 2D volume points\n");
			return -1.0;
		}
		pars->calcPars.isPointMemAllocated_2D=1;
	}
		  
	r_step = 2.0*pars->radius/((double)(r_points));
	
	if(pars->calcPars.isRhoAvailable_2D==0) {
	    // Initialize random number generator 
		int seed;    
		seed = 10000;
		srand(seed);
		
		// Generate random points accross the volume
		ptsGenerated = testsphere_generatePoints(pars->calcPars.points_2D, volume_points, pars->radius);
		
		// Calculate correlation function
		pars->calcPars.rho_2D = (float*) malloc(r_points*r_points*sizeof(float));
		if(pars->calcPars.rho_2D==NULL){
			printf("Problem allocating memory for 2D correlations points\n");
			return -1.0;
		}
		if(modelcalculations_calculatePairCorrelation_2D(pars->calcPars.points_2D, volume_points, pars->calcPars.rho_2D, r_points, r_step)==NULL){
		//if(modelcalculations_calculatePairCorrelation_2D_vector(pars->calcPars.points_2D, volume_points, pars->calcPars.rho_2D, r_points, r_step,0.0,0.0,0.0)==NULL){
			return 0;
		};
		pars->calcPars.isRhoAvailable_2D=1;
	} 
	// Calculate I(q,phi) and return that value
	vol = 4.0*acos(-1.0)/3.0*pars->radius*pars->radius*pars->radius;
	
	//printf("in ana_2D %f %f\n",q, phi);
	return modelcalculations_calculateIq_2D(pars->calcPars.rho_2D, r_points, r_step, q, phi)*vol;	
	
}

/// 1D scattering function
double testsphere_numerical_1D(TestSphereParameters *pars, int *array, double q) { return 0;}

/// 2D scattering function
double testsphere_numerical_2D(TestSphereParameters *pars, int *array, double q, double phi) {return 0;}

/**
 * Generate points randomly accross the volume
 * @param points [SpacePoint*] Array of 3D points to be filled
 * @param n [int] Number of points to generat
 * @param radius [double] Radius of the sphere
 * @return Number of points generated
 */
int testsphere_generatePoints(SpacePoint * points, int n, double radius) {
	int i;
	int testcounter;
	double x, y, z;
	
	// Create points	
	// To have a uniform density, you want to generate
	// random points in a box and keep only those that are
	// within the volume.
	
	// Initialize random number generator
	int seed;    
	seed = 10000;
	srand(seed);	
	
	testcounter = 0;
		
	memset(points,0,n*sizeof(SpacePoint));
	for(i=0;i<n;i++) {
		// Generate in a box centered around zero
		x = (2.0*((double)rand())/((double)(RAND_MAX)+(double)(1))-1.0) * radius;
		y = (2.0*((double)rand())/((double)(RAND_MAX)+(double)(1))-1.0) * radius;
		z = (2.0*((double)rand())/((double)(RAND_MAX)+(double)(1))-1.0) * radius;
		
		// reject those that are not within the volume
		if( sqrt(x*x+y*y+z*z) <= radius ) {
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
