#include "modelCalculations.h"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <memory.h>
#include <time.h>

/**
 * Initialization function for simulation structure
 */
void modelcalculations_init(CalcParameters *pars) {
        pars->isRhoAvailable         = 0;
        pars->isPointMemAllocated    = 0;
        pars->isRhoAvailable_2D      = 0;
        pars->isPointMemAllocated_2D = 0;
       
       	pars->volume_points = 0;
       	pars->r_points = 0;
       
		pars->timePr_1D = 0;
    	pars->timePr_2D = 0;
    	pars->timeIq_1D = 0;
    	pars->timeIq_2D = 0;
    
    	pars->errorOccured = 0;
    	
}

/**
 * Reset function for simulation structure
 */
void modelcalculations_reset(CalcParameters *pars) {
       modelcalculations_dealloc(pars);
       modelcalculations_init(pars);
}

/**
 * Deallocate memory of simullation structure
 */
void modelcalculations_dealloc(CalcParameters *pars) {
	free(pars->rho);
	free(pars->points);
	free(pars->rho_2D);
	free(pars->points_2D);
}

/**
 * Calculate pair correlation for 1D simulation
 */
int modelcalculations_calculatePairCorrelation_1D(SpacePoint * points, int volume_points, double * rho, int r_points, double bin_width) {
	int i,j;
	double dx,dy,dz,dist;
	int i_bin;
	//double bin_width;
	double delta_t;
	double average;
	double closest;
	time_t start_time;
	clock_t start;
	clock_t finish;
	//struct tm *timeStruct;
	
	
	// Allocate memory
	/*
	rho = (double*) malloc(r_points*sizeof(double));
	if(rho==NULL){
		printf("Problem allocating memory for 1D correlation points\n");
		return -1;
	}
	*/
	
	// Clear vector
	memset(rho,0,r_points*sizeof(double));

	// R bin width
    //bin_width = 2.0*size/r_points;
    
		time(&start_time);
		start = clock();
		
		
	average = 0;
	for(i=0;i<volume_points-1;i++) {
		closest = -1;
		for(j=i+1;j<volume_points;j++) {
            dx = (points[i].x-points[j].x);
            dy = (points[i].y-points[j].y);
            dz = (points[i].z-points[j].z);
			dist = sqrt(dx*dx + dy*dy + dz*dz);
			
			if(closest<0 || dist<closest) {
				closest = dist;
			}
			
			//i_bin = (int)dist/bin_width;
			i_bin = (int)floor(dist/bin_width);
            
            //rho[i_bin] = rho[i_bin] + 1.0/9000000.0;
            if(i_bin >= r_points) {
            	printf("problem! %i > %i\n", i_bin, r_points);
            } else {
            	rho[i_bin] = rho[i_bin] + 1.0;
            }
		}
		average += closest;
	}
	average = average/(double)volume_points;
	printf("average distance %f\n",average);
	
		finish = clock();
        //time(&end_time);
        //delta_t = difftime(end_time,start_time);
        delta_t = ((double)(finish-start))/CLOCKS_PER_SEC;
        printf("------------->PR calc time = %f\n", delta_t);
    return 1;
}

/**
 * Calculate I(q) for 1D simulation 
 */
double modelcalculations_calculateIq_1D(double * rho, int r_points, double r_step, double q) {
	int i;
	double value;
	//double r_step;
	//double vol;
	double sum;
	double qr;
	clock_t start;
	clock_t finish;
	double delta_t;
	
	start = clock();
	
    //vol = 4.0*acos(-1.0)/3.0*radius*radius*radius;
	//r_step = 2.0*radius/((double)(r_points));
	
	value = 0.0;
	sum = 0.0;
	for(i=1; i<r_points; i++) {
		qr = q*r_step*(double)i;
		value = value + rho[i] * sin(qr) / qr;
		sum = sum + rho[i];
	}
	
	
	value = value/sum;
	
	finish = clock();
    delta_t = ((double)(finish-start))/CLOCKS_PER_SEC;
    //printf("------------->IQ calc time = %f\n", delta_t);
	
	
	return value;
}

/**
 * Calculate pair correlation function for 2D simulation using
 * a 3D array to store P(r)
 */
int modelcalculations_calculatePairCorrelation_2D_3Darray(SpacePoint * points, int volume_points, float * rho, int r_points, double bin_width) {
	int i,j;
	int ix_bin, iy_bin, iz_bin;
	
	clock_t start;
	clock_t finish;
	
	// Clear vector
	memset(rho,0,r_points*r_points*r_points*sizeof(float));

    start = clock();
	for(i=0;i<volume_points-1;i++) {
		for(j=i+1;j<volume_points;j++) {
			
            // Add entry to the matrix
            ix_bin = (int)floor(fabs(points[i].x-points[j].x)/bin_width);
            iy_bin = (int)floor(fabs(points[i].y-points[j].y)/bin_width);
            iz_bin = (int)floor(fabs(points[i].z-points[j].z)/bin_width);
            
            if(ix_bin < r_points && iy_bin < r_points && iz_bin < r_points) {
            	rho[(ix_bin*r_points+iy_bin)*r_points+iz_bin] += 1.0;
            } else {
            	printf("Bad point! %i %i %i\n", ix_bin, iy_bin, iz_bin);
            }
			
		}
	}
	
	finish = clock();
    printf("-------------> Pair Correlation time = %f\n", ((double)(finish-start))/CLOCKS_PER_SEC);
    return 0;
}

/**
 * Calculate pair correlation function for 2D simulation by storing P(r) in a 2D array.
 * Allows for rotation of object in space by specifying theta, phi, omage of the beam
 */
int modelcalculations_calculatePairCorrelation_2D_vector(SpacePoint * points, int volume_points, float * rho, 
			int r_points, double bin_width, double theta_beam, double phi_beam, double omega_beam) {
	int i,j;
	int ix_bin, iy_bin;
	SpacePoint p1, p2;
	
	clock_t start;
	clock_t finish;
	
	// Clear vector
	memset(rho,0,r_points*r_points*sizeof(float));
	//printf("P(r) with theta=%g phi=%g\n", theta_beam, phi_beam);
    start = clock();
	for(i=0;i<volume_points-1;i++) {
		// Rotate point
		p1 = modelcalculations_rotate(points[i], theta_beam, phi_beam, omega_beam);
		//printf("p = %g %g %g -> %g %g %g\n", points[i].x,points[i].y,points[i].z, p1.x,p1.y,p1.z);
		for(j=i+1;j<volume_points;j++) {
			// Rotate point
			p2 = modelcalculations_rotate(points[j], theta_beam, phi_beam, omega_beam);
			
			
			// Calculate distance in plane perpendicular to beam (z)
            ix_bin = (int)floor(fabs(p1.x-p2.x)/bin_width);
            iy_bin = (int)floor(fabs(p1.y-p2.y)/bin_width);
            //iz_bin = (int)floor((points[i].z-points[j].z)/bin_width+r_points/2);
            
            rho[ix_bin*r_points+iy_bin] += 1.0;
			
		}
	}
	
	finish = clock();
    printf("-------------> 2D (v) Pair Correlation time = %f\n", ((double)(finish-start))/CLOCKS_PER_SEC);
    return 1;
}

/**
 * Calculate pair correlation function for 2D simulation by storing P(r) in a 2D array
 */
int modelcalculations_calculatePairCorrelation_2D(SpacePoint * points, int volume_points, float * rho, int r_points, double bin_width) {
	int i,j;
	int ix_bin, iy_bin;
	
	clock_t start;
	clock_t finish;
	
	// Clear vector
	memset(rho,0,r_points*r_points*sizeof(float));

	//return 1;
	
    start = clock();
	for(i=0;i<volume_points-1;i++) {
		for(j=i+1;j<volume_points;j++) {
			
			// Calculate distance in plane perpendicular to beam (z)
            ix_bin = (int)floor(fabs(points[i].x-points[j].x)/bin_width);
            iy_bin = (int)floor(fabs(points[i].y-points[j].y)/bin_width);
            //iz_bin = (int)floor(fabs(points[i].z-points[j].z)/bin_width);
            
            rho[ix_bin*r_points+iy_bin] += 1.0;
            //rho[ix_bin*r_points+iy_bin] += fabs(points[i].z-points[j].z);
		}
	}
	
	finish = clock();
    printf("-------------> Pair Correlation time = %f\n", ((double)(finish-start))/CLOCKS_PER_SEC);
    
    /*
     * for(i=0;i<r_points;i++) {
    	for(j=0;j<r_points;j++) {
    		printf("Pr(%i, %i) = %g\n", i, j, rho[i*r_points+j]);
    	}	
    	
    }
    */
	return 0;
}

/**
 * Calculate I(q) for 2D simulation from 3D array
 */
double modelcalculations_calculateIq_2D_3Darray(float * rho, int r_points, double r_step, double q, double phi) {
	//TODO: make rho an array of ints.
	
	int ix,iy,iz;
	
	// This should be a parameter
	double lambda = 1.6;
	double theta;
	double value;
	double sum;
	// This should also be a parameter, about value of radius
	double r_max = 1;
	//double r_step =1;
	
	double c1;
	double c2;
	double c3;
	int r2;
	double f3;
	double iz_c;
	clock_t start; 
	clock_t finish;
	
	theta = 2*asin(q*lambda/(4*acos(-1.0)));
	
	value = 0.0;
	sum = 0.0;
	//c1 = lambda*(cos(theta)-1)*r_step;
	//c2 = lambda*sin(theta)*cos(phi)*r_step;
	//c3 = lambda*sin(theta)*sin(phi)*r_step;
	
	c1 = 0;
	c2 = q*cos(phi)*r_step;
	c3 = q*sin(phi)*r_step;
	
	start = clock();
	
	// TODO: sum(rho) should be equal to the number of points^2 !
	
	for(ix=0; ix<r_points; ix++) {
		for(iy=0; iy<r_points; iy++) {
			r2 = ix*r_points*r_points+iy*r_points;
			f3 = c2*(ix-r_points/2) + c3*(iy-r_points/2);
			for(iz=0; iz<r_points; iz++) {
				iz_c = (double)iz-r_points/2; 
				value = value + rho[r2+iz] * cos( c1*iz_c + f3 );
				sum = sum + rho[r2+iz];
			}
		}
	}
	finish = clock();
    //printf("-------------> I(Q) time = %f, (%f %f %f)\n", ((double)(finish-start))/CLOCKS_PER_SEC, q, phi,value/sum);
	
	
	value = value /sum;
	return value;
}

/**
 * Pair correlation function for a sphere
 * 	@param r: distance value
 */
double pair_corr_sphere(double r) {
	
	return r*r*(1.0 - 0.75*r + r*r*r/16.0);	
}

/** 
 * Calculate I(q) for 2D simulation from 2D array P(r)
 */
double modelcalculations_calculateIq_2D(float * rho, int r_points, double r_step, double q, double phi) {
	//TODO: make rho an array of ints.
	
	int ix,iy;
	
	// This should be a parameter
	double lambda = 1.0;
	double value;
	double sum;
	// This should also be a parameter, about value of radius
	double r_max = 1;
	//double r_step =1;
	
	double c2;
	double c3;
	int ibin;
	clock_t start; 
	clock_t finish;
	
	//theta = 2*asin(q*lambda/(4*acos(-1.0)));
	value = 0.0;
	sum = 0.0;
	c2 = q*cos(phi)*r_step;
	c3 = q*sin(phi)*r_step;
	//printf("phi = %g, c2=%g, c3=%g, q=%g, r_step=%g\n",phi, c2, c3,q,r_step);
	
	start = clock();
	
	for(ix=-r_points+1; ix<r_points; ix++) {
		for(iy=-r_points+1; iy<r_points; iy++) {
			
			//value += rho[ix*r_points+iy] * cos( c2*((double)ix+0.5) + c3*((double)iy+0.5) );
			//sum += rho[ix*r_points+iy];
			
			ibin = (int)(floor(sqrt(1.0*ix*ix)))*r_points+(int)(floor(sqrt(1.0*iy*iy)));
			
			if (ibin<r_points*r_points) {
			
				//value += rho[ibin] * cos( c2*((double)ix+0.5) + c3*((double)iy+0.5) );
			
				value += rho[ibin] * cos( c2*((double)ix) + c3*((double)iy) );
				
				sum += rho[ibin];
			} else {
				printf("Error computing IQ %i >= %i (%i %i)\n", ibin, r_points*r_points,ix, iy);
			};
			
			
			//dx = r_step*((double)ix+0.5);
			//dy = r_step*((double)iy+0.5);
			
			// Only works for sphere of radius = 20
			//f3 = pair_corr_sphere(sqrt(dx*dx+dy*dy)/20.0);
			
			//value += f3 * cos( c2*(dx) + c3*(dy) );
			//sum += f3;		
		}
	}
	finish = clock();
	
	value = value /sum;
	return value;
}


/**
 *  Rotation of a space point
 */
SpacePoint modelcalculations_rotate(SpacePoint p, double theta, double phi, double omega) {
	SpacePoint new_point;
	double x_1, x_2;
	double y_1, y_2;
	double z_1, z_2;
	// P(r) assumes beam along z-axis. Rotate point accordingly
	
	
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
 
 