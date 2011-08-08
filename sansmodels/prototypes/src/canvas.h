#if !defined(simcanvas_h)
#define simcanvas_h

#include "modelCalculations.h"

#define REALSPACE_SPHERE 1

typedef struct {
	// Position
	double x;
	double y;
	double z;
	// Orientation
	double o1;
	double o2;
	double o3;
	// Vector of parameters
	double params[15];
	
	// Pointer to function to generate space points
	int (*generate)(SpacePoint *points, double *params, int npts);
	// Pointer to function to check whether a point is contained by an object
	int (*isContained)(SpacePoint *point, double *params);
	// Pointer to function to calculate the object's volume
	double (*getVolume)(double *params);
	
	
	// Points available
	int points_available;
	// Space points
	SpacePoint points[151000];
	//SpacePoint *points;
	// Number of space points
	int npts;
	double volume;
	int layer;
	
} SpaceObject;


typedef struct {
	// Maximum number of shapes
	int max_shapes;
	// List of real-space objects
	SpaceObject *shapes;
	int n_shapes;
} CanvasParams;


int canvas_dealloc(CanvasParams *self);
int canvas_add(CanvasParams *pars, SpaceObject *shape);
double canvas_intensity(CanvasParams *self, double q, double phi);
int canvas_init(CanvasParams *pars);
int canvas_add(CanvasParams *self, int objectCode);
int canvas_setParam(CanvasParams *self, int shapeID, int paramID, double value);
int canvas_PointAllowed(CanvasParams *self, int object_id, int i_pt);


// SPHERE object ----------------------------------------------------------------------
int initSphereObject(SpaceObject *pars);
int generateSphereObject(SpacePoint *points, double *params, int npts);
int sphere_IsContained(SpacePoint *point, double *params);
double sphere_getVolume(double *params);

#endif