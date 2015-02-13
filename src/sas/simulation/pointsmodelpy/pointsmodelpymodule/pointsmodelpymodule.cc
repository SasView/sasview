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

#include "exceptions.h"
#include "bindings.h"


char pypointsmodelpy_module__doc__[] = "";

// Initialization function for the module (*must* be called initpointsmodelpy)
extern "C"
void
initpointsmodelpy()
{
    // create the module and add the functions
    PyObject * m = Py_InitModule4(
        "pointsmodelpy", pypointsmodelpy_methods,
        pypointsmodelpy_module__doc__, 0, PYTHON_API_VERSION);

    // get its dictionary
    PyObject * d = PyModule_GetDict(m);

    // check for errors
    if (PyErr_Occurred()) {
        Py_FatalError("can't initialize module pointsmodelpy");
    }

    // install the module exceptions
    pypointsmodelpy_runtimeError = PyErr_NewException("pointsmodelpy.runtime", 0, 0);
    PyDict_SetItemString(d, "RuntimeException", pypointsmodelpy_runtimeError);

    return;
}

// version
// $Id$

// End of file
