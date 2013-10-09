/**
  Smearer module to perform point and slit smearing calculations

	This software was developed by the University of Tennessee as part of the
	Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
	project funded by the US National Science Foundation.

	See the license text in license.txt

	copyright 2009, University of Tennessee
 */
#include <Python.h>
#include <stdio.h>
#include <smearer2d_helper.hh>

// Utilities
#define INVECTOR(obj,buf,len)										\
    do { \
        int err = PyObject_AsReadBuffer(obj, (const void **)(&buf), &len); \
        if (err < 0) return NULL; \
        len /= sizeof(*buf); \
    } while (0)

#define OUTVECTOR(obj,buf,len) \
    do { \
        int err = PyObject_AsWriteBuffer(obj, (void **)(&buf), &len); \
        if (err < 0) return NULL; \
        len /= sizeof(*buf); \
    } while (0)


/**
 * Delete a Smearer2d object
 */
void del_smearer2d_helper(void *ptr){
	Smearer_helper* smearer2d_helper = static_cast<Smearer_helper *>(ptr);
	delete smearer2d_helper;
	return;
}

/**
 * Create a QSmearer as a python object by supplying a q array
 */
PyObject * new_Smearer_helper(PyObject *, PyObject *args) {
	PyObject *qx_values_obj;
	PyObject *qy_values_obj;
	PyObject *dqx_values_obj;
	PyObject *dqy_values_obj;
	Py_ssize_t n_q;
	//PyObject rlimit_obj;
	//PyObject npoints_obj;
	//PyObject nrbins_obj;
	//PyObject nphibins_obj;
	double* qx_values;
	double* qy_values;
	double* dqx_values;
	double* dqy_values;
	double rlimit;
	int npoints;
	int nrbins;
	int nphibins;


	if (!PyArg_ParseTuple(args, "OOOOdiii", &qx_values_obj, &qy_values_obj, &dqx_values_obj, &dqy_values_obj, &rlimit, &nrbins, &nphibins, &npoints)) return NULL;
	OUTVECTOR(qx_values_obj, qx_values, n_q);
	OUTVECTOR(qy_values_obj, qy_values, n_q);
	OUTVECTOR(dqx_values_obj, dqx_values, n_q);
	OUTVECTOR(dqy_values_obj, dqy_values, n_q);
	Smearer_helper* smearer2d_helper = new Smearer_helper(npoints,qx_values,qy_values,dqx_values,dqy_values, rlimit, nrbins, nphibins);
	return PyCObject_FromVoidPtr(smearer2d_helper, del_smearer2d_helper);
}

/**
 * Smear the given input according to a given smearer object
 */
PyObject * smear2d_input(PyObject *, PyObject *args) {
	PyObject *weights_obj;
	Py_ssize_t w_out;
	double *weights;
	PyObject *qx_out_obj;
	Py_ssize_t n_out;
	double *qx_out;
	PyObject *qy_out_obj;
	//Py_ssize_t n_out;
	double *qy_out;
	PyObject *smear_obj;

	if (!PyArg_ParseTuple(args, "OOOO",  &smear_obj, &weights_obj, &qx_out_obj, &qy_out_obj)) return NULL;
	OUTVECTOR(weights_obj, weights, w_out);
	OUTVECTOR(qx_out_obj, qx_out, n_out);
	OUTVECTOR(qy_out_obj, qy_out, n_out);

	// Sanity check
	//if(n_in!=n_out) return Py_BuildValue("i",-1);

	// Set the array pointers
	void *temp = PyCObject_AsVoidPtr(smear_obj);
	Smearer_helper* s = static_cast<Smearer_helper *>(temp);

	s->smear2d(weights, qx_out, qy_out);
	//return PyCObject_FromVoidPtr(s, del_smearer2d_helper);
	return Py_BuildValue("i",1);
}


/**
 * Define module methods
 */
static PyMethodDef module_methods[] = {
	{"new_Smearer_helper", (PyCFunction)new_Smearer_helper, METH_VARARGS,
		  "Create a new Q Smearer object"},
	{"smearer2d_helper",(PyCFunction)smear2d_input, METH_VARARGS,
		  "Smear the given input array"},
    {NULL}
};


#ifndef PyMODINIT_FUNC	/* declarations for DLL import/export */
#define PyMODINIT_FUNC void
#endif
PyMODINIT_FUNC
initsmearer2d_helper(void)
{
    PyObject* m;

    m = Py_InitModule3("smearer2d_helper", module_methods,
                       "Smearer2d_helper module");
}
