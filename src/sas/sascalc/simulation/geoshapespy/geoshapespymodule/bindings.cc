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

struct PyMethodDef pygeoshapespy_methods[] = {

   //geoshapes methods: set_orientation; set_center
   {pygeoshapespy_set_orientation__name__, pygeoshapespy_set_orientation,
    METH_VARARGS, pygeoshapespy_set_orientation__doc__},

   {pygeoshapespy_set_center__name__, pygeoshapespy_set_center,
    METH_VARARGS, pygeoshapespy_set_center__doc__},

   // new sphere
   {pyanalmodelpy_new_sphere__name__, pyanalmodelpy_new_sphere,
    METH_VARARGS, pyanalmodelpy_new_sphere__doc__},

   // new cylinder
   {pyanalmodelpy_new_cylinder__name__, pyanalmodelpy_new_cylinder,
    METH_VARARGS, pyanalmodelpy_new_cylinder__doc__},

   // new ellipsoid
   {pyanalmodelpy_new_ellipsoid__name__, pyanalmodelpy_new_ellipsoid,
    METH_VARARGS, pyanalmodelpy_new_ellipsoid__doc__},

   // new hollowsphere
   {pyanalmodelpy_new_hollowsphere__name__, pyanalmodelpy_new_hollowsphere,
    METH_VARARGS, pyanalmodelpy_new_hollowsphere__doc__},

   // new singlehelix
   {pyanalmodelpy_new_singlehelix__name__, pyanalmodelpy_new_singlehelix,
    METH_VARARGS, pyanalmodelpy_new_singlehelix__doc__},

   {pygeoshapespy_copyright__name__, pygeoshapespy_copyright,
    METH_VARARGS, pygeoshapespy_copyright__doc__},


// Sentinel
    {0, 0}
};

// version
// $Id$

// End of file
