/**
 *  Smearer module to perform point and slit smearing calculations

	This software was developed by the University of Tennessee as part of the
	Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
	project funded by the US National Science Foundation.

	See the license text in license.txt

	copyright 2009, University of Tennessee
 */
#include <Python.h>
#include <stdio.h>
#include <smearer.hh>

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
 * Delete a SlitSmearer object
 */
void del_slit_smearer(void *ptr){
	SlitSmearer* smearer = static_cast<SlitSmearer *>(ptr);
	delete smearer;
	return;
}

/**
 * Create a SlitSmearer as a python object
 */
PyObject * new_slit_smearer(PyObject *, PyObject *args) {
	double width;
	double height;
	double qmin;
	double qmax;
	int nbins;

	if (!PyArg_ParseTuple(args, "ddddi", &width, &height, &qmin, &qmax, &nbins)) return NULL;
	SlitSmearer* smearer = new SlitSmearer(width, height, qmin, qmax, nbins);
	return PyCObject_FromVoidPtr(smearer, del_slit_smearer);
}

/**
 * Delete a QSmearer object
 */
void del_q_smearer(void *ptr){
	QSmearer* smearer = static_cast<QSmearer *>(ptr);
	delete smearer;
	return;
}

/**
 * Create a QSmearer as a python object
 */
PyObject * new_q_smearer(PyObject *, PyObject *args) {
	PyObject *width_obj;
	Py_ssize_t n_w;
	double* width;
	double qmin;
	double qmax;
	int nbins;

	if (!PyArg_ParseTuple(args, "Oddi", &width_obj, &qmin, &qmax, &nbins)) return NULL;
	OUTVECTOR(width_obj, width, n_w);
	QSmearer* smearer = new QSmearer(width, qmin, qmax, nbins);
	return PyCObject_FromVoidPtr(smearer, del_q_smearer);
}

/**
 * Smear the given input according to a given smearer object
 */
PyObject * smear_input(PyObject *, PyObject *args) {
	PyObject *input_iq_obj;
	PyObject *output_iq_obj;
	PyObject *smear_obj;
	Py_ssize_t n_in;
	Py_ssize_t n_out;
	double *input_iq;
	double *output_iq;
	int first_bin;
	int last_bin;


	if (!PyArg_ParseTuple(args, "OOOii", &smear_obj, &input_iq_obj, &output_iq_obj, &first_bin, &last_bin)) return NULL;
	OUTVECTOR(input_iq_obj, input_iq, n_in);
	OUTVECTOR(output_iq_obj, output_iq, n_out);

	// Sanity check
	if(n_in!=n_out) return Py_BuildValue("i",-1);

	// Set the array pointers
	void *temp = PyCObject_AsVoidPtr(smear_obj);
	BaseSmearer* s = static_cast<BaseSmearer *>(temp);

	if(n_in!=s->get_nbins()) {
		return Py_BuildValue("i",-2);
	}

	s->smear(input_iq, output_iq, first_bin, last_bin);

	return Py_BuildValue("i",1);
}


/**
 * Define module methods
 */
static PyMethodDef module_methods[] = {
	{"new_slit_smearer", (PyCFunction)new_slit_smearer, METH_VARARGS,
		  "Create a new Slit Smearer object"},
	{"new_q_smearer", (PyCFunction)new_q_smearer, METH_VARARGS,
		  "Create a new Q Smearer object"},
	{"smear",(PyCFunction)smear_input, METH_VARARGS,
		  "Smear the given input array"},
    {NULL}
};


#ifndef PyMODINIT_FUNC	/* declarations for DLL import/export */
#define PyMODINIT_FUNC void
#endif
PyMODINIT_FUNC
initsmearer(void)
{
    PyObject* m;

    m = Py_InitModule3("smearer", module_methods,
                       "Q Smearing module");
}
