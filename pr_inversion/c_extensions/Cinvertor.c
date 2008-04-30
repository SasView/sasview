
#include <Python.h>
#include "structmember.h"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

#include "invertor.h"


/// Error object for raised exceptions
static PyObject * CinvertorError = NULL;

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


// Class definition
typedef struct {
    PyObject_HEAD    
    Invertor_params params; 
} Cinvertor;


static void
Cinvertor_dealloc(Cinvertor* self)
{
    invertor_dealloc(&(self->params));
     
    self->ob_type->tp_free((PyObject*)self);

}

static PyObject *
Cinvertor_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    Cinvertor *self;
    
    self = (Cinvertor *)type->tp_alloc(type, 0);
   
    return (PyObject *)self;
}

static int
Cinvertor_init(Cinvertor *self, PyObject *args, PyObject *kwds)
{
    if (self != NULL) {    	
    	// Create parameters
    	invertor_init(&(self->params));
    }
    return 0;
}

static PyMemberDef Cinvertor_members[] = {
    //{"params", T_OBJECT, offsetof(Cinvertor, params), 0,
    // "Parameters"},
    {NULL}  /* Sentinel */
};


/**
 * Function to set the x data
 * Takes an array of doubles as input
 * Returns the number of entries found
 */
static PyObject * set_x(Cinvertor *self, PyObject *args) {
	PyObject *data_obj;
	Py_ssize_t ndata;
	double *data;
  
	if (!PyArg_ParseTuple(args, "O", &data_obj)) return NULL;
	OUTVECTOR(data_obj,data,ndata);
	self->params.x = data;
	self->params.npoints = ndata;
	return Py_BuildValue("i", self->params.npoints);	
}

static PyObject * get_x(Cinvertor *self, PyObject *args) {
	PyObject *data_obj;
	Py_ssize_t ndata;
	double *data;
    int i;
    
	if (!PyArg_ParseTuple(args, "O", &data_obj)) return NULL;
	INVECTOR(data_obj, data, ndata);
	
	// Check that the input array is large enough
	if (ndata < self->params.npoints) {
	    PyErr_SetString(CinvertorError, 
	    	"Cinvertor.get_x: input array too short for data.");
		return NULL;		
	}
	
	for(i=0; i<self->params.npoints; i++){
		data[i] = self->params.x[i];
	}
	
	return Py_BuildValue("i", self->params.npoints);	
}

/**
 * Function to set the y data
 * Takes an array of doubles as input
 * Returns the number of entries found
 */
static PyObject * set_y(Cinvertor *self, PyObject *args) {
	PyObject *data_obj;
	Py_ssize_t ndata;
	double *data;
  
	if (!PyArg_ParseTuple(args, "O", &data_obj)) return NULL;
	OUTVECTOR(data_obj,data,ndata);
	self->params.y = data;
	self->params.ny = ndata;
	return Py_BuildValue("i", self->params.ny);	
}

static PyObject * get_y(Cinvertor *self, PyObject *args) {
	PyObject *data_obj;
	Py_ssize_t ndata;
	double *data;
    int i;
    
	if (!PyArg_ParseTuple(args, "O", &data_obj)) return NULL;
	INVECTOR(data_obj, data, ndata);
	
	// Check that the input array is large enough
	if (ndata < self->params.ny) {
	    PyErr_SetString(CinvertorError, 
	    	"Cinvertor.get_y: input array too short for data.");
		return NULL;		
	}
	
	for(i=0; i<self->params.ny; i++){
		data[i] = self->params.y[i];
	}
	
	return Py_BuildValue("i", self->params.npoints);	
}

/**
 * Function to set the x data
 * Takes an array of doubles as input
 * Returns the number of entries found
 */
static PyObject * set_err(Cinvertor *self, PyObject *args) {
	PyObject *data_obj;
	Py_ssize_t ndata;
	double *data;
  
	if (!PyArg_ParseTuple(args, "O", &data_obj)) return NULL;
	OUTVECTOR(data_obj,data,ndata);
	self->params.err = data;
	self->params.nerr = ndata;
	return Py_BuildValue("i", self->params.nerr);	
}

static PyObject * get_err(Cinvertor *self, PyObject *args) {
	PyObject *data_obj;
	Py_ssize_t ndata;
	double *data;
    int i;
    
	if (!PyArg_ParseTuple(args, "O", &data_obj)) return NULL;
	INVECTOR(data_obj, data, ndata);
	
	// Check that the input array is large enough
	if (ndata < self->params.nerr) {
	    PyErr_SetString(CinvertorError, 
	    	"Cinvertor.get_err: input array too short for data.");
		return NULL;		
	}
	
	for(i=0; i<self->params.nerr; i++){
		data[i] = self->params.err[i];
	}
	
	return Py_BuildValue("i", self->params.npoints);	
}

/**
 * Check the validity of the stored data
 * Returns the number of points if it's all good, -1 otherwise
 */
static PyObject * is_valid(Cinvertor *self, PyObject *args) {
	if(self->params.npoints==self->params.ny &&
			self->params.npoints==self->params.nerr) {
		return Py_BuildValue("i", self->params.npoints);
	} else {
		return Py_BuildValue("i", -1);
	}	
}

/**
 * Sets the maximum distance
 */
static PyObject * set_dmax(Cinvertor *self, PyObject *args) {
	double d_max;
  
	if (!PyArg_ParseTuple(args, "d", &d_max)) return NULL;
	self->params.d_max = d_max;
	return Py_BuildValue("d", self->params.d_max);	
}

/**
 * Gets the maximum distance
 */
static PyObject * get_dmax(Cinvertor *self, PyObject *args) {
	return Py_BuildValue("d", self->params.d_max);	
}

static PyObject * set_alpha(Cinvertor *self, PyObject *args) {
	double alpha;
  
	if (!PyArg_ParseTuple(args, "d", &alpha)) return NULL;
	self->params.alpha = alpha;
	return Py_BuildValue("d", self->params.alpha);	
}

/**
 * Gets the maximum distance
 */
static PyObject * get_alpha(Cinvertor *self, PyObject *args) {
	return Py_BuildValue("d", self->params.alpha);	
}

/**
 * Gets the number of x points
 */
static PyObject * get_nx(Cinvertor *self, PyObject *args) {
	return Py_BuildValue("i", self->params.npoints);	
}

/**
 * Gets the number of y points
 */
static PyObject * get_ny(Cinvertor *self, PyObject *args) {
	return Py_BuildValue("i", self->params.ny);	
}

/**
 * Gets the number of error points
 */
static PyObject * get_nerr(Cinvertor *self, PyObject *args) {
	return Py_BuildValue("i", self->params.nerr);	
}


/**
 * Function to call to evaluate the residuals
 * @param args: input parameters
 * @return: list of residuals
 */
static PyObject * residuals(Cinvertor *self, PyObject *args) {
	double *pars;
	PyObject* residuals;
	PyObject* temp;
	double *res;
	int i;
	double residual, diff;
	// Regularization factor
	double regterm = 0.0;
	double tmp = 0.0;
	
	PyObject *data_obj;
	Py_ssize_t npars;
	  
	if (!PyArg_ParseTuple(args, "O", &data_obj)) return NULL;
	
	OUTVECTOR(data_obj,pars,npars);
		
    // PyList of residuals
	// Should create this list only once and refill it
    residuals = PyList_New(self->params.npoints);

    regterm = reg_term(pars, self->params.d_max, npars);
    
    for(i=0; i<self->params.npoints; i++) {
    	diff = self->params.y[i] - iq(pars, self->params.d_max, npars, self->params.x[i]);
    	residual = diff*diff / (self->params.err[i]*self->params.err[i]);
    	tmp = residual;
    	
    	// regularization term
    	residual += self->params.alpha * regterm;
    	
    	if (PyList_SetItem(residuals, i, Py_BuildValue("d",residual) ) < 0){
    	    PyErr_SetString(CinvertorError, 
    	    	"Cinvertor.residuals: error setting residual.");
    		return NULL;
    	};
    		
    }
    
	return residuals;
}
/**
 * Function to call to evaluate the residuals
 * for P(r) minimization (for testing purposes)
 * @param args: input parameters
 * @return: list of residuals
 */
static PyObject * pr_residuals(Cinvertor *self, PyObject *args) {
	double *pars;
	PyObject* residuals;
	PyObject* temp;
	double *res;
	int i;
	double residual, diff;
	// Regularization factor
	double regterm = 0.0;
	double tmp = 0.0;
	
	PyObject *data_obj;
	Py_ssize_t npars;
	  
	if (!PyArg_ParseTuple(args, "O", &data_obj)) return NULL;
	
	OUTVECTOR(data_obj,pars,npars);
		
	// Should create this list only once and refill it
    residuals = PyList_New(self->params.npoints);

    regterm = reg_term(pars, self->params.d_max, npars);

    
    for(i=0; i<self->params.npoints; i++) {
    	diff = self->params.y[i] - pr(pars, self->params.d_max, npars, self->params.x[i]);
    	residual = diff*diff / (self->params.err[i]*self->params.err[i]);
    	tmp = residual;
    	
    	// regularization term
    	residual += self->params.alpha * regterm;
    	
    	if (PyList_SetItem(residuals, i, Py_BuildValue("d",residual) ) < 0){
    	    PyErr_SetString(CinvertorError, 
    	    	"Cinvertor.residuals: error setting residual.");
    		return NULL;
    	};
    		
    }
    
	return residuals;
}

/**
 * Function to call to evaluate the scattering intensity
 * @param args: c-parameters, and q
 * @return: I(q)
 */
static PyObject * get_iq(Cinvertor *self, PyObject *args) {
	double *pars;
	double q, iq_value;
	PyObject *data_obj;
	Py_ssize_t npars;
	  
	if (!PyArg_ParseTuple(args, "Od", &data_obj, &q)) return NULL;
	OUTVECTOR(data_obj,pars,npars);
		
	iq_value = iq(pars, self->params.d_max, npars, q);
	return Py_BuildValue("f", iq_value);	
}

/**
 * Function to call to evaluate P(r)
 * @param args: c-parameters and r
 * @return: P(r)
 */
static PyObject * get_pr(Cinvertor *self, PyObject *args) {
	double *pars;
	double r, pr_value;
	PyObject *data_obj;
	Py_ssize_t npars;
	  
	if (!PyArg_ParseTuple(args, "Od", &data_obj, &r)) return NULL;
	OUTVECTOR(data_obj,pars,npars);
		
	pr_value = pr(pars, self->params.d_max, npars, r);
	return Py_BuildValue("f", pr_value);	
}

/**
 * Function to call to evaluate P(r) with errors
 * @param args: c-parameters and r
 * @return: P(r)
 */
static PyObject * get_pr_err(Cinvertor *self, PyObject *args) {
	double *pars;
	double *pars_err;
	double pr_err_value;
	double r, pr_value;
	PyObject *data_obj;
	Py_ssize_t npars;
	PyObject *err_obj;
	Py_ssize_t npars2;
	  
	if (!PyArg_ParseTuple(args, "OOd", &data_obj, &err_obj, &r)) return NULL;
	OUTVECTOR(data_obj,pars,npars);
	OUTVECTOR(err_obj,pars_err,npars2);
		
	pr_err(pars, pars_err, self->params.d_max, npars, r, &pr_value, &pr_err_value);
	return Py_BuildValue("ff", pr_value, pr_err_value);	
}


static PyMethodDef Cinvertor_methods[] = {
		   {"residuals", (PyCFunction)residuals, METH_VARARGS, "Get the list of residuals"},
		   {"pr_residuals", (PyCFunction)pr_residuals, METH_VARARGS, "Get the list of residuals"},
		   {"set_x", (PyCFunction)set_x, METH_VARARGS, ""},
		   {"get_x", (PyCFunction)get_x, METH_VARARGS, ""},
		   {"set_y", (PyCFunction)set_y, METH_VARARGS, ""},
		   {"get_y", (PyCFunction)get_y, METH_VARARGS, ""},
		   {"set_err", (PyCFunction)set_err, METH_VARARGS, ""},
		   {"get_err", (PyCFunction)get_err, METH_VARARGS, ""},
		   {"set_dmax", (PyCFunction)set_dmax, METH_VARARGS, ""},
		   {"get_dmax", (PyCFunction)get_dmax, METH_VARARGS, ""},
		   {"set_alpha", (PyCFunction)set_alpha, METH_VARARGS, ""},
		   {"get_alpha", (PyCFunction)get_alpha, METH_VARARGS, ""},
		   {"get_nx", (PyCFunction)get_nx, METH_VARARGS, ""},
		   {"get_ny", (PyCFunction)get_ny, METH_VARARGS, ""},
		   {"get_nerr", (PyCFunction)get_nerr, METH_VARARGS, ""},
		   {"iq", (PyCFunction)get_iq, METH_VARARGS, ""},
		   {"pr", (PyCFunction)get_pr, METH_VARARGS, ""},
		   {"get_pr_err", (PyCFunction)get_pr_err, METH_VARARGS, ""},
		   {"is_valid", (PyCFunction)is_valid, METH_VARARGS, ""},
   
   {NULL}
};

static PyTypeObject CinvertorType = {
    PyObject_HEAD_INIT(NULL)
    0,                         /*ob_size*/
    "Cinvertor",             /*tp_name*/
    sizeof(Cinvertor),             /*tp_basicsize*/
    0,                         /*tp_itemsize*/
    (destructor)Cinvertor_dealloc, /*tp_dealloc*/
    0,                         /*tp_print*/
    0,                         /*tp_getattr*/
    0,                         /*tp_setattr*/
    0,                         /*tp_compare*/
    0,                         /*tp_repr*/
    0,                         /*tp_as_number*/
    0,                         /*tp_as_sequence*/
    0,                         /*tp_as_mapping*/
    0,                         /*tp_hash */
    0,                         /*tp_call*/
    0,                         /*tp_str*/
    0,                         /*tp_getattro*/
    0,                         /*tp_setattro*/
    0,                         /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /*tp_flags*/
    "Cinvertor objects",           /* tp_doc */
    0,		               /* tp_traverse */
    0,		               /* tp_clear */
    0,		               /* tp_richcompare */
    0,		               /* tp_weaklistoffset */
    0,		               /* tp_iter */
    0,		               /* tp_iternext */
    Cinvertor_methods,             /* tp_methods */
    Cinvertor_members,             /* tp_members */
    0,                         /* tp_getset */
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    (initproc)Cinvertor_init,      /* tp_init */
    0,                         /* tp_alloc */
    Cinvertor_new,                 /* tp_new */
};


static PyMethodDef module_methods[] = {
    {NULL} 
};

/**
 * Function used to add the model class to a module
 * @param module: module to add the class to
 */ 
void addCinvertor(PyObject *module) {
	PyObject *d;
	
    if (PyType_Ready(&CinvertorType) < 0)
        return;

    Py_INCREF(&CinvertorType);
    PyModule_AddObject(module, "Cinvertor", (PyObject *)&CinvertorType);
    
    d = PyModule_GetDict(module);
    CinvertorError = PyErr_NewException("Cinvertor.error", NULL, NULL);
    PyDict_SetItemString(d, "CinvertorError", CinvertorError);
}


#ifndef PyMODINIT_FUNC	/* declarations for DLL import/export */
#define PyMODINIT_FUNC void
#endif
PyMODINIT_FUNC
initpr_inversion(void) 
{
    PyObject* m;

    m = Py_InitModule3("pr_inversion", module_methods,
                       "C extension module for inversion to P(r).");
                       
    addCinvertor(m);
}
