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

//#include <portinfo>
#include <Python.h>

#include "misc.h"
#include "sphere.h"
#include "cylinder.h"
#include "ellipsoid.h"
#include "hollow_sphere.h"
#include "single_helix.h"

// copyright

char pygeoshapespy_copyright__doc__[] = "";
char pygeoshapespy_copyright__name__[] = "copyright";

static char pygeoshapespy_copyright_note[] = 
    "geoshapespy python module: Copyright (c) 1998-2005 Michael A.G. Aivazis";


PyObject * pygeoshapespy_copyright(PyObject *, PyObject *)
{
    return Py_BuildValue("s", pygeoshapespy_copyright_note);
}

//GeoShape methods
char pygeoshapespy_set_orientation__name__[] = "set_orientation";
char pygeoshapespy_set_orientation__doc__[] = "Set the rotation angles";

PyObject * pygeoshapespy_set_orientation(PyObject *, PyObject *args){
  PyObject *pyshape = 0;
  double angX=0,angY=0,angZ=0;
  
  int ok = PyArg_ParseTuple(args, "Oddd", &pyshape,&angX,&angY,&angZ); 
  if(!ok) return NULL;

  void *temp = PyCObject_AsVoidPtr(pyshape);

  GeoShape *shape = static_cast<GeoShape *>(temp);

  shape->SetOrientation(angX,angY,angZ);

  return Py_BuildValue("i", 0);
}

char pygeoshapespy_set_center__name__[] = "set_center";
char pygeoshapespy_set_center__doc__[] = "new center for points translation";

PyObject * pygeoshapespy_set_center(PyObject *, PyObject *args){

  PyObject *pyshape = 0;
  double tranX=0,tranY=0,tranZ=0;
  
  int ok = PyArg_ParseTuple(args, "Oddd", &pyshape,&tranX,&tranY,&tranZ); 
  if(!ok) return NULL;

  void *temp = PyCObject_AsVoidPtr(pyshape);

  GeoShape *shape = static_cast<GeoShape *>(temp);

  shape->SetCenter(tranX,tranY,tranZ);

  return Py_BuildValue("i", 0);
}

//Sphere constructor
char pyanalmodelpy_new_sphere__name__[] = "new_sphere";
char pyanalmodelpy_new_sphere__doc__[] = "sphere constructor";

PyObject * pyanalmodelpy_new_sphere(PyObject *, PyObject *args){
  double r;
  int ok = PyArg_ParseTuple(args,"d",&r);
  if(!ok) return 0;

  Sphere *newsph = new Sphere(r);

  return PyCObject_FromVoidPtr(newsph, PyDelSphere);
}

static void PyDelSphere(void *ptr){
  Sphere * oldsph = static_cast<Sphere *>(ptr);
  delete oldsph;

  return;
}

//Cylinder constructor
char pyanalmodelpy_new_cylinder__name__[] = "new_cylinder";
char pyanalmodelpy_new_cylinder__doc__[] = "cylinder constructor";

PyObject * pyanalmodelpy_new_cylinder(PyObject *, PyObject *args){
  double r,h;
  int ok = PyArg_ParseTuple(args,"dd",&r,&h);
  if(!ok) return 0;

  Cylinder *newcyl = new Cylinder(r,h);

  return PyCObject_FromVoidPtr(newcyl, PyDelCylinder);
}

static void PyDelCylinder(void *ptr){
  Cylinder * oldcyl = static_cast<Cylinder *>(ptr);
  delete oldcyl;

  return;
}

//Ellipsoid constructor
char pyanalmodelpy_new_ellipsoid__name__[] = "new_ellipsoid";
char pyanalmodelpy_new_ellipsoid__doc__[] = "ellipsoid constructor";

PyObject * pyanalmodelpy_new_ellipsoid(PyObject *, PyObject *args){
  double rx,ry,rz;
  int ok = PyArg_ParseTuple(args,"ddd",&rx,&ry,&rz);
  if(!ok) return 0;

  Ellipsoid *newelli = new Ellipsoid(rx,ry,rz);

  return PyCObject_FromVoidPtr(newelli, PyDelEllipsoid);
}

static void PyDelEllipsoid(void *ptr){
  Ellipsoid * oldelli = static_cast<Ellipsoid *>(ptr);
  delete oldelli;

  return;
}

//Hollow Sphere constructor & methods
char pyanalmodelpy_new_hollowsphere__name__[] = "new_hollowsphere";
char pyanalmodelpy_new_hollowsphere__doc__[] = "";

PyObject * pyanalmodelpy_new_hollowsphere(PyObject *, PyObject *args)
{
  double r, th;
  int ok = PyArg_ParseTuple(args,"dd",&r, &th);
  if(!ok) return 0;

  HollowSphere *newhosph = new HollowSphere(r,th);

  return PyCObject_FromVoidPtr(newhosph, PyDelHollowSphere);

}

static void PyDelHollowSphere(void *ptr)
{
  HollowSphere * oldhosph = static_cast<HollowSphere *>(ptr);
  delete oldhosph;
  return;
}

//Single Helix constructor & methods
char pyanalmodelpy_new_singlehelix__name__[] = "new_singlehelix";
char pyanalmodelpy_new_singlehelix__doc__[] = "";

PyObject * pyanalmodelpy_new_singlehelix(PyObject *, PyObject *args)
{
  double hr,tr,pitch,turns;
  int ok = PyArg_ParseTuple(args,"dddd",&hr,&tr,&pitch,&turns);
  if(!ok) return 0;

  SingleHelix *newsinhel = new SingleHelix(hr,tr,pitch,turns);

  return PyCObject_FromVoidPtr(newsinhel, PyDelSingleHelix);

}

static void PyDelSingleHelix(void *ptr)
{
  SingleHelix * oldsinhel = static_cast<SingleHelix *>(ptr);
  delete oldsinhel;
  return;
}
    
// version
// $Id$

// End of file
