#include "modelCalculations.h"
#include "canvas.h"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <memory.h>
#include <time.h>

/**
 * Initialization function for simulation structure
 */
int canvas_init(CanvasParams *pars) {
	int i;
	
	pars->n_shapes = 0;
	pars->max_shapes = 3; 
	
	// Allocate memory
	pars->shapes = (SpaceObject*) malloc(pars->max_shapes*sizeof(SpaceObject));
	
	if(pars->shapes==NULL) {
		printf("canvas_init: Problem allocating memory for space objects\n");
		return -1;
	}
	
	return 0;
}

int canvas_dealloc(CanvasParams *self) {
	int i;
	printf("dealloc\n");
	/*
	//for(i=0; i<self->n_shapes; i++) {
	for(i=0; i<self->max_shapes; i++) {
		free(self->shapes[i].points);
		free(self->shapes[i].params);
		//free(self->shapes[i].generate);
	}
	*/
	free(self->shapes);
	printf("deallocated\n");
	return 0;
}

int canvas_add(CanvasParams *self, int objectCode) {
	int id;
	id = self->n_shapes;
	
	if(objectCode==REALSPACE_SPHERE) {
		initSphereObject( &(self->shapes[id]) );
	}
	
	self->shapes[id].layer = id;
	self->n_shapes++;
	
	return id;
}

int canvas_setParam(CanvasParams *self, int shapeID, int paramID, double value) {
	self->shapes[shapeID].params[paramID]=value;
	self->shapes[shapeID].points_available = 0;
	
	// update volume
	self->shapes[shapeID].volume = (*self->shapes[shapeID].getVolume)(&(self->shapes[shapeID].params));
	
	return 0;
}

double canvas_intensity(CanvasParams *self, double q, double phi) {
	double phase, cos_term, sin_term;
	double qx, qy, vol;
	int i, j, npts;
	double pars[4];
	
	double cos_shape, sin_shape;
	
	double vol_core, vol_shell, vol_sum;
	
	pars[0] = 1.0;
	pars[1] = 40.0;
	
	cos_term = 0.0;
	sin_term = 0.0;
	
	vol_sum = 0.0;
	
	vol = self->shapes[0].volume;
	vol_core = self->shapes[1].volume;
	vol_shell = vol-vol_core;

	npts = 0;
	
	qx = q*cos(phi);
	qy = q*sin(phi);
	
	for(i=0; i<self->n_shapes; i++) {
		if (self->shapes[i].points_available==0) {
			(*self->shapes[i].generate)( self->shapes[i].points, self->shapes[i].params, self->shapes[i].npts);
			self->shapes[i].points_available=1;
		}
		npts = 0;
		cos_shape = 0;
		sin_shape = 0;
		for(j=0; j<self->shapes[i].npts; j++) {
			
			if(canvas_PointAllowed(self, i, j)==1) {
				npts++;
				
				phase = qx*self->shapes[i].points[j].x + qy*self->shapes[i].points[j].y;
				//phase = 0.0;
				
				cos_shape += cos(phase);
				sin_shape += sin(phase);
			}   			
		}

		//printf("ID %i: cos=%g sin=%g fac=%g\n",i,cos_shape, sin_shape, self->shapes[i].volume /self->shapes[i].npts  * self->shapes[i].params[2]);


		
		
		// TODO: must find an efficient way to get the exact volume of each SLD regions.
		// For instance, if a volume is completely included in another (and it has a higher layer
		// number, we can simply subtract the two "theoretical" volumes instead of using the 
		// ratio of the points.

		// The following are the three lines we would like to write:
		
		//cos_term += cos_shape * self->shapes[i].volume /npts  * self->shapes[i].params[2];
		//sin_term += sin_shape * self->shapes[i].volume /npts  * self->shapes[i].params[2];
		//vol_sum += self->shapes[i].volume;
		
		// In that case, the volume is approx
		//     vol = (full volume) - sum(volume parts overlapping with other objects)
		// That can easily be done for object completely contained by others.

		cos_term += cos_shape * self->shapes[i].volume /self->shapes[i].npts  * self->shapes[i].params[2];
		sin_term += sin_shape * self->shapes[i].volume /self->shapes[i].npts  * self->shapes[i].params[2];
		vol_sum += self->shapes[i].volume*npts/self->shapes[i].npts;
		
		
		//vol_sum += self->shapes[i].volume;

		// The following is more precise (but implies better investigation of the topology)
		/*
		if(i==0){
			cos_term += cos_shape * vol_shell/npts  * self->shapes[i].params[2];
			sin_term += sin_shape * vol_shell/npts  * self->shapes[i].params[2];
			vol_sum += vol_shell;
		} else {
			cos_term += cos_shape * vol_core/npts  * self->shapes[i].params[2];
			sin_term += sin_shape * vol_core/npts  * self->shapes[i].params[2];
			vol_sum += vol_core;
		}
		*/
	}
	
	return 1.0e8*(cos_term*cos_term + sin_term*sin_term)/vol_sum;	
} 

int canvas_PointAllowed(CanvasParams *self, int object_id, int i_pt) {
	// Check whether space point i_pt is already covered by another object
	int i;
	
	for(i=0; i<self->n_shapes; i++) {
		// Check the object object_id is underneath
		if(self->shapes[object_id].layer < self->shapes[i].layer) {
			// Is the point overlapping, if so skip it.
			if(self->shapes[i].isContained(&self->shapes[object_id].points[i_pt], 
				self->shapes[i].params) == 1) {
				return 0;
			}
		} 
	}
	return 1;
} 



// SPHERE object ----------------------------------------------------------------------


int initSphereObject(SpaceObject *pars) {
	
	pars->x = 0.0;
	pars->y = 0.0;
	pars->z = 0.0;
	
	pars->o1 = 0.0;
	pars->o2 = 0.0;
	pars->o3 = 0.0;
	
	/*
	free(pars->params);
	
	printf("allocating parameters\n");
	pars->params = (double*) malloc(5*sizeof(double));
	if(pars->params==NULL) {
		printf("initSphereObject: Problem allocating memory\n");
		return -1;	
	}
	*/

	// Scale
	pars->params[0] = 1.0;
	// Radius
	pars->params[1] = 40.0;
	// Contrast
	pars->params[2] = 1.0;
	 
	pars->points_available = 0;
	
	pars->npts = 150000;
	free(pars->points);
	
	// Generation function
	pars->generate = &generateSphereObject;
	// isContained function
	pars->isContained = &sphere_IsContained;
	pars->getVolume = &sphere_getVolume;
	
	pars->volume = acos(-1.0)*4.0/3.0*pars->params[1]*pars->params[1]*pars->params[1];
	
	pars->layer = 0;
	
	return 0;
	
}

int sphere_IsContained(SpacePoint *point, double *params) {
	if( sqrt(point->x*point->x + point->y*point->y + point->z*point->z) < params[1]) {
	  return 1;
	}
	return 0;
}

double sphere_getVolume(double *params) {
	printf("radius=%g\n",params[1]);
	return acos(-1.0)*4.0/3.0*params[1]*params[1]*params[1];
}


int generateSphereObject(SpacePoint *points, double *params, int npts) {
	int i, testcounter;
	double x, y, z;
	SpacePoint tmp;
	
	printf("radius=%g, npts=%i\n", params[1], npts);
	
	testcounter = 0;
	
	/*
	free(points);
	printf("allocating points\n");
	points = (SpacePoint*) malloc(npts*sizeof(SpacePoint));
	if(points==NULL) {
		printf("generateSphereObject: Problem allocating memory\n");
		return -1;	
	}
	*/
	memset(points,0,npts*sizeof(SpacePoint));

	for(i=0;i<npts;i++) {
		// Generate in a box centered around zero
		x = (2.0*((double)rand())/((double)(RAND_MAX)+(double)(1))-1.0) * params[1];
		y = (2.0*((double)rand())/((double)(RAND_MAX)+(double)(1))-1.0) * params[1];
		z = (2.0*((double)rand())/((double)(RAND_MAX)+(double)(1))-1.0) * params[1];
		
		// reject those that are not within the volume
//		if( sqrt(x*x+y*y+z*z) < params[1]) {
		tmp.x = x;
		tmp.y = y;
		tmp.z = z;
		if( sphere_IsContained(&tmp, params) == 1 ) {
			points[i].x =  x;
			points[i].y =  y;
			points[i].z =  z;
			testcounter++;
		} else {
			i--;
		}
	}
	
	// Consistency check
	if(testcounter != npts) {
		return -1;
	}
	
	return testcounter;
	
}