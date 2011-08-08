#include "sphere_fast.h"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#include <memory.h>


/// 1D scattering function
double sphere_fast_analytical_1D(SimSphereFParameters *pars, double q) {
	int j, npts, volume_points;
	double sum, phi, vol;
	
	return simcylinder_fast_analytical_2D(pars, q, 0.0);
	
	//return simcylinder_fast_analytical_1D_average(pars, q);
	
	sum = 0;
	npts = 21;
	volume_points = (int)floor(pars->npoints);
	
	for(j=0; j<npts; j++) {
		phi = acos(-1.0)/npts * j;
		//sum += simcylinder_simple_analytical_2D(pars, q, phi, volume_points);
		sum += simcylinder_fast_analytical_2D(pars, q, phi);
	}

	// Calculate I(q,phi) and return that value
	vol = 4.0/3.0*acos(-1.0)*pars->radius*pars->radius*pars->radius;
	sum = 1.0e8/volume_points/volume_points*vol*sum*acos(-1.0)/2;
	return sum/npts;
}


/// 1D scattering function
double sphere_fast_analytical_2D(SimSphereFParameters *pars, double q, double phi) {
	// Check if Rho array is available
	int volume_points;
	int r_points;
	int ptsGenerated;
	double bin_width;
	double r_step;
	double vol;
	double retval;
	
	int i,j;
	int ix_bin, iy_bin;
	SpacePoint p1, p2;
	
	clock_t start;
	clock_t finish;
	double cos_term;
	double sin_term;
	double qx, qy, qz;
	double phase;
	double cyl_x, cyl_y, cyl_z;
	double q_x, q_y, q_z;
	double cos_val, alpha;
	
	
	volume_points = (int)floor(pars->npoints);
	cos_term = 0.0;
	sin_term = 0.0;
	
	qx = q*cos(phi);
	qy = q*sin(phi);
	qz = 0.0;
		
	// Generate random points accross the volume
	if(pars->calcPars.isPointMemAllocated_2D==0) {
		pars->calcPars.points_2D = (SpacePoint*)malloc(volume_points*sizeof(SpacePoint));
		if(pars->calcPars.points_2D==NULL) {
			printf("Problem allocating memory for 2D volume points\n");
			return -1.0;
		}
		
	    ptsGenerated = sphere_fast_generatePoints(pars->calcPars.points_2D, 
			volume_points, pars->radius, (int)floor(pars->seed));
		
		pars->calcPars.isPointMemAllocated_2D=1;
	}
		  
			
	for(i=0;i<volume_points-1;i++) {
		
		//p1 = fast_rotate(pars->calcPars.points_2D[i], pars->theta, pars->phi, 0.0);
		p1 = pars->calcPars.points_2D[i];
		phase = qx*p1.x + qy*p1.y;
		cos_term += cos(phase);
		sin_term += sin(phase);
		    
	}
	
	// Calculate I(q,phi) and return that value
	vol = 4.0/3.0*acos(-1.0)*pars->radius*pars->radius*pars->radius;
	
    return 1.0e8/volume_points/volume_points*vol*(cos_term*cos_term + sin_term*sin_term);	
    //return 1.0e8/volume_points/volume_points*vol*(cos_term*cos_term);	
}


 


/**
 * Generate points randomly accross the volume
 * @param points [SpacePoint*] Array of 3D points to be filled
 * @param n [int] Number of points to generat
 * @param radius [double] Radius of the sphere
 * @return Number of points generated
 */
int sphere_fast_generatePoints(SpacePoint * points, int n, double radius, int seed) {
	int i;
	int testcounter;
	double x, y, z;
	
	// Create points	
	// To have a uniform density, you want to generate
	// random points in a box and keep only those that are
	// within the volume.
	
	// Initialize random number generator
	//int seed;    
	time_t now;
	
	time(&now);
	//seed = 10000;
	
	//seed = (int)floor(fmod(now,10000));
	//seed = 10009; 
	srand(seed);	
	//printf("Seed = %i\n", seed);
	
	testcounter = 0;
		
	memset(points,0,n*sizeof(SpacePoint));
	for(i=0;i<n;i++) {
		// Generate in a box centered around zero
		x = (2.0*((double)rand())/((double)(RAND_MAX)+(double)(1))-1.0) * radius;
		y = (2.0*((double)rand())/((double)(RAND_MAX)+(double)(1))-1.0) * radius;
		z = (2.0*((double)rand())/((double)(RAND_MAX)+(double)(1))-1.0) * radius;
		
		// reject those that are not within the volume
		if( sqrt(x*x+y*y+z*z) < radius ) {
			points[i].x =  x;
			points[i].y =  y;
			points[i].z =  z;
			testcounter++;
		} else {
			i--;
		}
	}
	
	// Consistency check
	if(testcounter != n) {
		return -1;
	}
		
	return testcounter;
}
