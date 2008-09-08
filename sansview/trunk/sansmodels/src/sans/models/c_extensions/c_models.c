/** c_models
 *
 * Module containing all SANS model extensions
 *
 * @author   M.Doucet / UTK
 */
#include <Python.h>

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

	addCCylinderModel(m);
	addCCoreShellCylinderModel(m);
	addCCoreShellModel(m);
	addCEllipsoidModel(m);
	addCSphereModel(m);
	addCEllipticalCylinderModel(m);
	addDisperser(m);
	addCGaussian(m);
	addCLorentzian(m);

}
