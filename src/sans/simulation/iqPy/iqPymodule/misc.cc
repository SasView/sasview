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
#include "iq.h"


// copyright

char pyiqPy_copyright__doc__[] = "";
char pyiqPy_copyright__name__[] = "copyright";

static char pyiqPy_copyright_note[] = 
    "iqPy python module: Copyright (c) 1998-2005 Michael A.G. Aivazis";


PyObject * pyiqPy_copyright(PyObject *, PyObject *)
{
    return Py_BuildValue("s", pyiqPy_copyright_note);
}
    
// iq(int numI,double qmin,double qmax)
char pyiqPy_new_iq__doc__[] = "wrap class iq in C++";
char pyiqPy_new_iq__name__[] = "new_iq";

PyObject * pyiqPy_new_iq(PyObject *, PyObject *args)
{
  int py_numI;
  double py_qmin, py_qmax;
  int ok = PyArg_ParseTuple(args,"idd",&py_numI, &py_qmin, &py_qmax);
  if(!ok) return 0;

  IQ *iq = new IQ(py_numI,py_qmin,py_qmax);
  
  return PyCObject_FromVoidPtr(iq, NULL);
}

//output iq to file
extern char pyiqPy_OutputIQ__name__[] = "OutputIQ";
extern char pyiqPy_OutputIQ__doc__[] = "";

PyObject * pyiqPy_OutputIQ(PyObject *, PyObject *args){
  PyObject *pyiq = 0;
  char *outfile;
  int ok = PyArg_ParseTuple(args,"Os", &pyiq, &outfile);
  if(!ok) return NULL;

  void *temp = PyCObject_AsVoidPtr(pyiq);

  IQ * thisiq = static_cast<IQ *>(temp);

  thisiq->OutputIQ(outfile);

  return Py_BuildValue("i",0);
}

//release the iq object
static void PyDeliq(void *ptr)
{
  std::cout<<"Called PyDeliq()\n"; //Good to see once
  IQ * oldiq = static_cast<IQ *>(ptr);
  delete oldiq;
  return;
}
    
// version
// $Id$

// End of file
