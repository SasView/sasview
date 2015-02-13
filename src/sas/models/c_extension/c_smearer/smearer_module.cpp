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
 * Create a SlitSmearer as a python object by supplying a q array
 */
PyObject * new_slit_smearer_with_q(PyObject *, PyObject *args) {
	PyObject *qvalues_obj;
	Py_ssize_t n_q;
	double* qvalues;
	double width;
	double height;

	if (!PyArg_ParseTuple(args, "ddO", &width, &height, &qvalues_obj)) return NULL;
	OUTVECTOR(qvalues_obj, qvalues, n_q);
	SlitSmearer* smearer = new SlitSmearer(width, height, qvalues, n_q);
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
 * Create a QSmearer as a python object by supplying a q array
 */
PyObject * new_q_smearer_with_q(PyObject *, PyObject *args) {
	PyObject *width_obj;
	Py_ssize_t n_w;
	double* width;
	PyObject *qvalues_obj;
	Py_ssize_t n_q;
	double* qvalues;

	if (!PyArg_ParseTuple(args, "OO", &width_obj, &qvalues_obj)) return NULL;
	OUTVECTOR(width_obj, width, n_w);
	OUTVECTOR(qvalues_obj, qvalues, n_q);
	QSmearer* smearer = new QSmearer(width, qvalues, n_q);
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
 * Get the q-value of a given bin
 */
PyObject * get_q(PyObject *, PyObject *args) {
	PyObject *smear_obj;
	int bin;

	if (!PyArg_ParseTuple(args, "Oi", &smear_obj, &bin)) return NULL;

	// Set the array pointers
	void *temp = PyCObject_AsVoidPtr(smear_obj);
	BaseSmearer* s = static_cast<BaseSmearer *>(temp);

	if(s->get_nbins()<=0 || s->get_nbins()<=bin) {
		return NULL;
	}

	double q, q_min, q_max;
	if (s->get_bin_range(bin, &q, &q_min, &q_max)<0) {
		return NULL;
	}
	return Py_BuildValue("d", q);
}


/**
 * Define module methods
 */
static PyMethodDef module_methods[] = {
	{"new_slit_smearer", (PyCFunction)new_slit_smearer, METH_VARARGS,
		  "Create a new Slit Smearer object"},
	{"new_slit_smearer_with_q", (PyCFunction)new_slit_smearer_with_q, METH_VARARGS,
		  "Create a new Slit Smearer object by supplying an array of Q values"},
	{"new_q_smearer", (PyCFunction)new_q_smearer, METH_VARARGS,
		  "Create a new Q Smearer object"},
	{"new_q_smearer_with_q", (PyCFunction)new_q_smearer_with_q, METH_VARARGS,
		  "Create a new Q Smearer object by supplying an array of Q values"},
	{"smear",(PyCFunction)smear_input, METH_VARARGS,
		  "Smear the given input array"},
	{"get_q",(PyCFunction)get_q, METH_VARARGS,
		  "Get the q-value of a given bin"},
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
