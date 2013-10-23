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
#include "analytical_model.h"
#include "geo_shape.h"
#include "iq.h"

// copyright

char pyanalmodelpy_copyright__doc__[] = "";
char pyanalmodelpy_copyright__name__[] = "copyright";

static char pyanalmodelpy_copyright_note[] = 
    "analmodelpy python module: Copyright (c) 1998-2005 Michael A.G. Aivazis";


PyObject * pyanalmodelpy_copyright(PyObject *, PyObject *)
{
    return Py_BuildValue("s", pyanalmodelpy_copyright_note);
}

//extern char pyanalmodelpy_GetRadius__name__[] = "";
//extern char pyanalmodelpy_GetRadius__doc__[] = "GetRadius";
//PyObject * pyanalmodelpy_GetRadius(PyObject *, PyObject *args){
//  double r = Sphere::GetRadius();
//  
//  return PyBuildValue("d", r);
//}


    
// analytical_model class constructor  AnalyticalModel(Sphere &)

char pyanalmodelpy_new_analmodel__doc__[] = "";
char pyanalmodelpy_new_analmodel__name__[] = "new_analmodel";

PyObject * pyanalmodelpy_new_analmodel(PyObject *, PyObject *args)
{
  PyObject *pyshape = 0;
  int ok = PyArg_ParseTuple(args, "O", &pyshape);
  if(!ok) return NULL;

  void *temp = PyCObject_AsVoidPtr(pyshape);

  GeoShape *shape = static_cast<GeoShape *>(temp);

  AnalyticalModel *newanal = new AnalyticalModel(*shape);

  return PyCObject_FromVoidPtr(newanal, NULL);
}

//AnalyticalModel method: CalculateIQ(IQ *)
char pyanalmodelpy_CalculateIQ__doc__[] = "";
char pyanalmodelpy_CalculateIQ__name__[] = "CalculateIQ";

PyObject * pyanalmodelpy_CalculateIQ(PyObject *, PyObject *args)
{
  PyObject *pyanal = 0, *pyiq = 0;
  int ok = PyArg_ParseTuple(args, "OO", &pyanal, &pyiq);
  if(!ok) return NULL;
                                                                 
  void *temp = PyCObject_AsVoidPtr(pyanal);
  void *temp2 = PyCObject_AsVoidPtr(pyiq);
                                         
  AnalyticalModel * thisanal = static_cast<AnalyticalModel *>(temp);
  IQ * thisiq = static_cast<IQ *>(temp2);

  thisanal->CalculateIQ(thisiq);
                        
  return Py_BuildValue("i",0);

}
    
// version
// $Id$

// End of file
