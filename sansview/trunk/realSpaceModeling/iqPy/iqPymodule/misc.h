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

#if !defined(pyiqPy_misc_h)
#define pyiqPy_misc_h

// copyright
extern char pyiqPy_copyright__name__[];
extern char pyiqPy_copyright__doc__[];
extern "C"
PyObject * pyiqPy_copyright(PyObject *, PyObject *);

// iq constructor, iq(int, double, double)
extern char pyiqPy_new_iq__name__[];
extern char pyiqPy_new_iq__doc__[];
extern "C"
PyObject * pyiqPy_new_iq(PyObject *, PyObject *);

//output iq to file
extern char pyiqPy_OutputIQ__name__[];
extern char pyiqPy_OutputIQ__doc__[];
extern "C"
PyObject * pyiqPy_OutputIQ(PyObject *, PyObject *);

//release the iq object
static void PyDeliq(void *ptr);

#endif

// version
// $Id$

// End of file
