#include "simcylinder_fast.h"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#include <memory.h>


double simcylinder_fast_analytical_1D_test(SimCylinderFParameters *pars, double q) {
	/***
	 * Things to keep here:
	 * 	- volume calc
	 *  - point generation
	 *  
	 */
		// Check if Rho array is available
	int volume_points;
	int ptsGenerated, npts;
	double vol;
	
	int i, j, k, m;
	SpacePoint *p1;
	
	double sum;
	double theta_cyl, phi;
	double phase;
	
	double cos_term;
	double sin_term;
	double qx, qy;
	double pi_step;
	
	
	volume_points = (int)floor(pars->npoints);
	
		
	// Generate random points accross the volume
	if(pars->calcPars.isPointMemAllocated_2D==0) {
		pars->calcPars.points_2D = (SpacePoint*)malloc(volume_points*sizeof(SpacePoint));
		if(pars->calcPars.points_2D==NULL) {
			printf("Problem allocating memory for 2D volume points\n");
			return -1.0;
		}
		
		ptsGenerated = simcylinder_fast_generatePoints(pars->calcPars.points_2D, 
			volume_points, pars->radius, pars->length, (int)floor(pars->seed));
		
		pars->calcPars.isPointMemAllocated_2D=1;
	}
		  
	// Loop over theta_cyl
	
			
	sum = 0;
	npts = 21;
	// Allocate temporary memory
	p1 = (SpacePoint*)malloc(volume_points*sizeof(SpacePoint));
	
	pi_step =  acos(-1.0)/npts;
	for(i=0; i<npts; i++) {
		theta_cyl = pi_step * i;
		// Rotate the points
		
		for(k=0; k<volume_points; k++) { 
			p1[k] = fast_rotate(pars->calcPars.points_2D[k], theta_cyl, 0.0, 0.0);
		}
		
		// Loop over phi_cyl
		// Equivalent to looping over phi (detector)		
		for(j=0; j<npts; j++) {
			phi = 2*pi_step * j;
			
			cos_term = 0.0;
			sin_term = 0.0;
			
			qx = q*cos(phi);
			qy = q*sin(phi);
		
			for(m=0;m<volume_points;m++) {
				phase = qx*p1[m].x + qy*p1[m].y;
				cos_term += cos(phase);
				sin_term += sin(phase);
			}
		
		    sum += sin(theta_cyl)* (cos_term*cos_term + sin_term*sin_term);
		}
		
	}
	free(p1);
	// Calculate I(q,phi) and return that value
	vol = acos(-1.0)*pars->radius*pars->radius*pars->length;
	sum = 1.0e8/volume_points/volume_points*vol*sum*acos(-1.0)/2;
	return sum/npts/npts;
}

/// 1D scattering function
double simcylinder_fast_analytical_1D(SimCylinderFParameters *pars, double q) {
	int i, j, npts, volume_points;
	double sum, vol, psi;
	
	//return simcylinder_fast_analytical_1D_test(pars, q);
	
	
	sum = 0;
	npts = 51;
	volume_points = (int)floor(pars->npoints);
	
	for(i=0; i<npts; i++) {
		psi = 2*acos(-1.0)/npts * i;
		pars->phi = psi;
		
		for(j=0; j<npts; j++) {
			pars->theta = acos(-1.0)/npts * j;
			sum += sin(pars->theta)*simcylinder_simple_analytical_2D(pars, q, 0.0);
		}
	}
	// Calculate I(q,phi) and return that value
	vol = acos(-1.0)*pars->radius*pars->radius*pars->length;
	sum = 1.0e8/volume_points/volume_points*vol*sum*acos(-1.0)/2;
	return sum/npts/npts;
}


/// 2D scattering function
double simcylinder_fast_analytical_2D(SimCylinderFParameters *pars, double q, double phi) {
	int volume_points;
	int ptsGenerated;
	double vol;
	
	int i;
	SpacePoint p1;
	
	double cos_term;
	double sin_term;
	double qx, qy, qz;
	double phase;

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
		
	    ptsGenerated = simcylinder_fast_generatePoints(pars->calcPars.points_2D, 
			volume_points, pars->radius, pars->length, (int)floor(pars->seed));
		
		for(i=0;i<volume_points;i++) {
			p1 = fast_rotate(pars->calcPars.points_2D[i], pars->theta, pars->phi, 0.0);
			pars->calcPars.points_2D[i] = p1;
		}
				
		pars->calcPars.isPointMemAllocated_2D=1;
	}
		  
			
	for(i=0;i<volume_points-1;i++) {
		p1 = pars->calcPars.points_2D[i];
		phase = qx*p1.x + qy*p1.y;
		cos_term += cos(phase);
		sin_term += sin(phase);
		    
	}
	
	// Calculate I(q,phi) and return that value
	vol = acos(-1.0)*pars->radius*pars->radius*pars->length;
	return 1.0e8/volume_points/volume_points*vol*acos(-1)/2*(cos_term*cos_term + sin_term*sin_term);	
}

double simcylinder_simple_analytical_2D(SimCylinderFParameters *pars, double q, double phi) {
	int ptsGenerated;
	
	int i;
	SpacePoint p1;
	
	double cos_term;
	double sin_term;
	double qx, qy, qz;
	double phase;
	int volume_points;
	
	cos_term = 0.0;
	sin_term = 0.0;
	
	qx = q*cos(phi);
	qy = q*sin(phi);
	qz = 0.0;

	volume_points = (int)floor(pars->npoints);
	
	// Generate random points accross the volume
	if(pars->calcPars.isPointMemAllocated_2D==0) {
		pars->calcPars.points_2D = (SpacePoint*)malloc(volume_points*sizeof(SpacePoint));
		if(pars->calcPars.points_2D==NULL) {
			printf("Problem allocating memory for 2D volume points\n");
			return -1.0;
		}
		
	    ptsGenerated = simcylinder_fast_generatePoints(pars->calcPars.points_2D, 
			volume_points, pars->radius, pars->length, (int)floor(pars->seed));
		
		for(i=0;i<volume_points;i++) {
			p1 = fast_rotate(pars->calcPars.points_2D[i], pars->theta, pars->phi, 0.0);
			pars->calcPars.points_2D[i] = p1;
		}
		
		pars->calcPars.isPointMemAllocated_2D=1;
	}
			
	for(i=0;i<volume_points;i++) {
		p1 = fast_rotate(pars->calcPars.points_2D[i], pars->theta, pars->phi, 0.0);
		phase = qx*p1.x + qy*p1.y;
		cos_term += cos(phase);
		sin_term += sin(phase);
	}

    return (cos_term*cos_term + sin_term*sin_term);
}

/**
 *  Rotation of pair correlation function
 */
SpacePoint fast_rotate(SpacePoint p, double theta, double phi, double omega) {
	SpacePoint new_point;
	double x_1, x_2;
	double y_1, y_2;
	double z_1, z_2;
	
	
	// Omega, around z-axis (doesn't change anything for cylindrical symmetry
	x_1 = p.x*cos(omega) - p.y*sin(omega);
	y_1 = p.x*sin(omega) + p.y*cos(omega);
	z_1 = p.z;	
	
	// Theta, around y-axis
	x_2 = x_1*cos(theta) + z_1*sin(theta);
	y_2 = y_1;
	z_2 = -x_1*sin(theta) + z_1*cos(theta);
	
	// Phi, around z-axis
	new_point.x = x_2*cos(phi) - y_2*sin(phi);
	new_point.y = x_2*sin(phi) + y_2*cos(phi);
	new_point.z = z_2;
	
	return new_point;
	
	
}
 


/**
 * Generate points randomly accross the volume
 * @param points [SpacePoint*] Array of 3D points to be filled
 * @param n [int] Number of points to generat
 * @param radius [double] Radius of the sphere
 * @return Number of points generated
 */
int simcylinder_fast_generatePoints(SpacePoint * points, int n, double radius, double length, int seed) {
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
	
	// Consistency check
	if(testcounter != n) {
		return -1;
	}
		
	return testcounter;
}
