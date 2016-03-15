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

#include "bindings.h"

#include "misc.h"          // miscellaneous methods

// the method table

struct PyMethodDef pyiqPy_methods[] = {

    // new_iq
    {pyiqPy_new_iq__name__, pyiqPy_new_iq,
     METH_VARARGS, "iq(int numI,double qmin, double qmax)->new IQ object"},

    //OutputIQ
    {pyiqPy_OutputIQ__name__, pyiqPy_OutputIQ,
     METH_VARARGS, pyiqPy_OutputIQ__doc__},

    {pyiqPy_copyright__name__, pyiqPy_copyright,
     METH_VARARGS, pyiqPy_copyright__doc__},


// Sentinel
    {0, 0}
};

// version
// $Id$

// End of file
