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

struct PyMethodDef pyanalmodelpy_methods[] = {

    // new analmodel
    {pyanalmodelpy_new_analmodel__name__, pyanalmodelpy_new_analmodel,
     METH_VARARGS, pyanalmodelpy_new_analmodel__doc__},

    //analmodel method: CalculateIQ
    {pyanalmodelpy_CalculateIQ__name__, pyanalmodelpy_CalculateIQ,
     METH_VARARGS, pyanalmodelpy_CalculateIQ__doc__},

    {pyanalmodelpy_copyright__name__, pyanalmodelpy_copyright,
     METH_VARARGS, pyanalmodelpy_copyright__doc__},


// Sentinel
    {0, 0}
};

// version
// $Id$

// End of file
