// -*- C++ -*-

#include <Python.h>


#include "exceptions.h"
#include "bindings.h"
#include "myutil.h"


char pygeoshapespy_module__doc__[] = "";

// Initialization function for the module (*must* be called initgeoshapespy)
extern "C"
void
initgeoshapespy()
{
    // create the module and add the functions
    PyObject * m = Py_InitModule4(
        "geoshapespy", pygeoshapespy_methods,
        pygeoshapespy_module__doc__, 0, PYTHON_API_VERSION);

    // get its dictionary
    PyObject * d = PyModule_GetDict(m);

    // check for errors
    if (PyErr_Occurred()) {
        Py_FatalError("can't initialize module geoshapespy");
    }

    // install the module exceptions
    pygeoshapespy_runtimeError = PyErr_NewException("geoshapespy.runtime", 0, 0);
    PyDict_SetItemString(d, "RuntimeException", pygeoshapespy_runtimeError);

	// Seed the random number generator
	seed_rnd();

    return;
}

// version
// $Id$

// End of file
