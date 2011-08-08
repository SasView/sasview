/** c_models
 *
 * Module containing all SANS model extensions 
 *
 * @author   M.Doucet / UTK
 */
#include <Python.h>

/// CVS information
static char cvsid[] = "$Id: BaseCComponent.c,v 1.4 2007/03/23 20:50:58 doucet Exp $";


/**
 * Define empty module
 */
static PyMethodDef module_methods[] = {
    {NULL} 
};


#ifndef PyMODINIT_FUNC	/* declarations for DLL import/export */
#define PyMODINIT_FUNC void
#endif
PyMODINIT_FUNC
initc_models(void) 
{
    PyObject* m;

    m = Py_InitModule3("c_models", module_methods,
                       "C extension module for SANS scattering models.");
                       
	addCTestSphere2(m);
	addCSimCylinder(m);
	addCSmearCylinderModel(m);
	addCDispCylinderModel(m);
	addCSimCylinderF(m);
	addCSimSphereF(m);
	addCCanvas(m);
}
