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

#if !defined(pyanalmodelpy_misc_h)
#define pyanalmodelpy_misc_h

// copyright
extern char pyanalmodelpy_copyright__name__[];
extern char pyanalmodelpy_copyright__doc__[];
extern "C"
PyObject * pyanalmodelpy_copyright(PyObject *, PyObject *);

extern char pyanalmodelpy_GetRadius__name__[];
extern char pyanalmodelpy_GetRadius__doc__[];
extern "C"
PyObject * pyanalmodelpy_GetRadius(PyObject *, PyObject *);


// Analytical Model constructor
extern char pyanalmodelpy_new_analmodel__name__[];
extern char pyanalmodelpy_new_analmodel__doc__[];
extern "C"
PyObject * pyanalmodelpy_new_analmodel(PyObject *, PyObject *);

// AnalyticalModel method: CalculateIQ(IQ *)
extern char pyanalmodelpy_CalculateIQ__name__[];
extern char pyanalmodelpy_CalculateIQ__doc__[];
extern "C"
PyObject * pyanalmodelpy_CalculateIQ(PyObject *, PyObject *);


#endif

// version
// $Id$

// End of file
