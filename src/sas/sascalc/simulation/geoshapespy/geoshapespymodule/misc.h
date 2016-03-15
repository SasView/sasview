// -*- C++ -*-
// 
//  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
// 
//                               Michael A.G. Aivazis
//                        California Institute of Technology
//                        (C) 1998-2005  All Rights Reserved
// 
//  <LicenseText>
// 
//  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
// 

#if !defined(pygeoshapespy_misc_h)
#define pygeoshapespy_misc_h

// copyright
extern char pygeoshapespy_copyright__name__[];
extern char pygeoshapespy_copyright__doc__[];
extern "C"
PyObject * pygeoshapespy_copyright(PyObject *, PyObject *);

//GeoShape methods
extern char pygeoshapespy_set_orientation__name__[];
extern char pygeoshapespy_set_orientation__doc__[];
extern "C"
PyObject * pygeoshapespy_set_orientation(PyObject *, PyObject *);

extern char pygeoshapespy_set_center__name__[];
extern char pygeoshapespy_set_center__doc__[];
extern "C"
PyObject * pygeoshapespy_set_center(PyObject *, PyObject *);

//Sphere constructor & methods
extern char pyanalmodelpy_new_sphere__name__[];
extern char pyanalmodelpy_new_sphere__doc__[];
extern "C"
PyObject * pyanalmodelpy_new_sphere(PyObject *, PyObject *);

static void PyDelSphere(void *);

//Cylinder constructor & methods
extern char pyanalmodelpy_new_cylinder__name__[];
extern char pyanalmodelpy_new_cylinder__doc__[];
extern "C"
PyObject * pyanalmodelpy_new_cylinder(PyObject *, PyObject *);

static void PyDelCylinder(void *);

//Ellipsoid constructor & method
extern char pyanalmodelpy_new_ellipsoid__name__[];
extern char pyanalmodelpy_new_ellipsoid__doc__[];
extern "C"
PyObject * pyanalmodelpy_new_ellipsoid(PyObject *, PyObject *);

static void PyDelEllipsoid(void *);

//Hollow Sphere constructor & methods
extern char pyanalmodelpy_new_hollowsphere__name__[];
extern char pyanalmodelpy_new_hollowsphere__doc__[];
extern "C"
PyObject * pyanalmodelpy_new_hollowsphere(PyObject *, PyObject *);

static void PyDelHollowSphere(void *);

//Single Helix constructor & methods
extern char pyanalmodelpy_new_singlehelix__name__[];
extern char pyanalmodelpy_new_singlehelix__doc__[];
extern "C"
PyObject * pyanalmodelpy_new_singlehelix(PyObject *, PyObject *);

static void PyDelSingleHelix(void *);

#endif

// version
// $Id$

// End of file
