/**
 * C implementation of the P(r) inversion
 * Cinvertor is the base class for the Invertor class
 * and provides the underlying computations.
 * 
 */
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
/**
 * C implementation of the P(r) inversion
 * Cinvertor is the base class for the Invertor class
 * and provides the underlying computations.
 * 
 */
typedef struct {
    PyObject_HEAD    
    /// Internal data structure
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

const char set_x_doc[] = 
	"Function to set the x data\n"
	"Takes an array of doubles as input.\n"
	" @return: number of entries found";

/**
 * Function to set the x data
 * Takes an array of doubles as input
 * Returns the number of entries found
 */
static PyObject * set_x(Cinvertor *self, PyObject *args) {
	PyObject *data_obj;
	Py_ssize_t ndata;
	double *data;
	int i;
  
	if (!PyArg_ParseTuple(args, "O", &data_obj)) return NULL;
	OUTVECTOR(data_obj,data,ndata);
	
	free(self->params.x);
	self->params.x = (double*) malloc(ndata*sizeof(double));
	
	if(self->params.x==NULL) {
	    PyErr_SetString(CinvertorError, 
	    	"Cinvertor.set_x: problem allocating memory.");
		return NULL;		
	}
	
	for (i=0; i<ndata; i++) {
		self->params.x[i] = data[i];
	}
	
	//self->params.x = data;
	self->params.npoints = ndata;
	return Py_BuildValue("i", self->params.npoints);	
}

const char get_x_doc[] = 
	"Function to get the x data\n"
	"Takes an array of doubles as input.\n"
	" @return: number of entries found";

static PyObject * get_x(Cinvertor *self, PyObject *args) {
	PyObject *data_obj;
	Py_ssize_t ndata;
	double *data;
    int i;
    
	if (!PyArg_ParseTuple(args, "O", &data_obj)) return NULL;
	OUTVECTOR(data_obj, data, ndata);
	
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

const char set_y_doc[] = 
	"Function to set the y data\n"
	"Takes an array of doubles as input.\n"
	" @return: number of entries found";

/**
 * Function to set the y data
 * Takes an array of doubles as input
 * Returns the number of entries found
 */
static PyObject * set_y(Cinvertor *self, PyObject *args) {
	PyObject *data_obj;
	Py_ssize_t ndata;
	double *data;
	int i;
  
	if (!PyArg_ParseTuple(args, "O", &data_obj)) return NULL;
	OUTVECTOR(data_obj,data,ndata);
	
	free(self->params.y);
	self->params.y = (double*) malloc(ndata*sizeof(double));
	
	if(self->params.y==NULL) {
	    PyErr_SetString(CinvertorError, 
	    	"Cinvertor.set_y: problem allocating memory.");
		return NULL;		
	}
	
	for (i=0; i<ndata; i++) {
		self->params.y[i] = data[i];
	}	
	
	//self->params.y = data;
	self->params.ny = ndata;
	return Py_BuildValue("i", self->params.ny);	
}

const char get_y_doc[] = 
	"Function to get the y data\n"
	"Takes an array of doubles as input.\n"
	" @return: number of entries found";

static PyObject * get_y(Cinvertor *self, PyObject *args) {
	PyObject *data_obj;
	Py_ssize_t ndata;
	double *data;
    int i;
    
	if (!PyArg_ParseTuple(args, "O", &data_obj)) return NULL;
	OUTVECTOR(data_obj, data, ndata);
	
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

const char set_err_doc[] = 
	"Function to set the err data\n"
	"Takes an array of doubles as input.\n"
	" @return: number of entries found";

/**
 * Function to set the x data
 * Takes an array of doubles as input
 * Returns the number of entries found
 */
static PyObject * set_err(Cinvertor *self, PyObject *args) {
	PyObject *data_obj;
	Py_ssize_t ndata;
	double *data;
	int i;
  
	if (!PyArg_ParseTuple(args, "O", &data_obj)) return NULL;
	OUTVECTOR(data_obj,data,ndata);
	
	free(self->params.err);
	self->params.err = (double*) malloc(ndata*sizeof(double));
	
	if(self->params.err==NULL) {
	    PyErr_SetString(CinvertorError, 
	    	"Cinvertor.set_err: problem allocating memory.");
		return NULL;		
	}
	
	for (i=0; i<ndata; i++) {
		self->params.err[i] = data[i];
	}
	
	//self->params.err = data;
	self->params.nerr = ndata;
	return Py_BuildValue("i", self->params.nerr);	
}

const char get_err_doc[] = 
	"Function to get the err data\n"
	"Takes an array of doubles as input.\n"
	" @return: number of entries found";

static PyObject * get_err(Cinvertor *self, PyObject *args) {
	PyObject *data_obj;
	Py_ssize_t ndata;
	double *data;
    int i;
    
	if (!PyArg_ParseTuple(args, "O", &data_obj)) return NULL;
	OUTVECTOR(data_obj, data, ndata);
	
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

const char is_valid_doc[] = 
	"Check the validity of the stored data\n"
	" @return: Returns the number of points if it's all good, -1 otherwise";

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

const char set_dmax_doc[] = 
	"Sets the maximum distance\n";

/**
 * Sets the maximum distance
 */
static PyObject * set_dmax(Cinvertor *self, PyObject *args) {
	double d_max;
  
	if (!PyArg_ParseTuple(args, "d", &d_max)) return NULL;
	self->params.d_max = d_max;
	return Py_BuildValue("d", self->params.d_max);	
}

const char get_dmax_doc[] = 
	"Gets the maximum distance\n";

/**
 * Gets the maximum distance
 */
static PyObject * get_dmax(Cinvertor *self, PyObject *args) {
	return Py_BuildValue("d", self->params.d_max);	
}

const char set_qmin_doc[] = 
	"Sets the minimum q\n";

/**
 * Sets the minimum q
 */
static PyObject * set_qmin(Cinvertor *self, PyObject *args) {
	double q_min;
  
	if (!PyArg_ParseTuple(args, "d", &q_min)) return NULL;
	self->params.q_min = q_min;
	return Py_BuildValue("d", self->params.q_min);	
}

const char get_qmin_doc[] = 
	"Gets the minimum q\n";

/**
 * Gets the minimum q
 */
static PyObject * get_qmin(Cinvertor *self, PyObject *args) {
	return Py_BuildValue("d", self->params.q_min);	
}

const char set_qmax_doc[] = 
	"Sets the maximum q\n";

/**
 * Sets the maximum q
 */
static PyObject * set_qmax(Cinvertor *self, PyObject *args) {
	double q_max;
  
	if (!PyArg_ParseTuple(args, "d", &q_max)) return NULL;
	self->params.q_max = q_max;
	return Py_BuildValue("d", self->params.q_max);	
}

const char get_qmax_doc[] = 
	"Gets the maximum q\n";

/**
 * Gets the maximum q
 */
static PyObject * get_qmax(Cinvertor *self, PyObject *args) {
	return Py_BuildValue("d", self->params.q_max);	
}

const char set_alpha_doc[] = 
	"Sets the alpha parameter\n";

static PyObject * set_alpha(Cinvertor *self, PyObject *args) {
	double alpha;
  
	if (!PyArg_ParseTuple(args, "d", &alpha)) return NULL;
	self->params.alpha = alpha;
	return Py_BuildValue("d", self->params.alpha);	
}

const char get_alpha_doc[] = 
	"Gets the alpha parameter\n";

/**
 * Gets the maximum distance
 */
static PyObject * get_alpha(Cinvertor *self, PyObject *args) {
	return Py_BuildValue("d", self->params.alpha);	
}

const char get_nx_doc[] = 
	"Gets the number of x points\n";

/**
 * Gets the number of x points
 */
static PyObject * get_nx(Cinvertor *self, PyObject *args) {
	return Py_BuildValue("i", self->params.npoints);	
}

const char get_ny_doc[] = 
	"Gets the number of y points\n";

/**
 * Gets the number of y points
 */
static PyObject * get_ny(Cinvertor *self, PyObject *args) {
	return Py_BuildValue("i", self->params.ny);	
}

const char get_nerr_doc[] = 
	"Gets the number of err points\n";

/**
 * Gets the number of error points
 */
static PyObject * get_nerr(Cinvertor *self, PyObject *args) {
	return Py_BuildValue("i", self->params.nerr);	
}


const char residuals_doc[] = 
	"Function to call to evaluate the residuals\n"
	"for P(r) inversion\n"
	" @param args: input parameters\n"
	" @return: list of residuals";

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
	// Number of slices in regularization term estimate
	int nslice = 25;
	
	PyObject *data_obj;
	Py_ssize_t npars;
	  
	if (!PyArg_ParseTuple(args, "O", &data_obj)) return NULL;
	
	OUTVECTOR(data_obj,pars,npars);
		
    // PyList of residuals
	// Should create this list only once and refill it
    residuals = PyList_New(self->params.npoints);

    regterm = reg_term(pars, self->params.d_max, npars, nslice);
    
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

const char pr_residuals_doc[] = 
	"Function to call to evaluate the residuals\n"
	"for P(r) minimization (for testing purposes)\n"
	" @param args: input parameters\n"
	" @return: list of residuals";

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
	// Number of slices in regularization term estimate
	int nslice = 25;
	
	PyObject *data_obj;
	Py_ssize_t npars;
	  
	if (!PyArg_ParseTuple(args, "O", &data_obj)) return NULL;
	
	OUTVECTOR(data_obj,pars,npars);
		
	// Should create this list only once and refill it
    residuals = PyList_New(self->params.npoints);

    regterm = reg_term(pars, self->params.d_max, npars, nslice);

    
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

const char get_iq_doc[] = 
	"Function to call to evaluate the scattering intensity\n"
	" @param args: c-parameters, and q\n"
	" @return: I(q)";

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

const char get_pr_doc[] = 
	"Function to call to evaluate P(r)\n"
	" @param args: c-parameters and r\n"
	" @return: P(r)";

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

const char get_pr_err_doc[] = 
	"Function to call to evaluate P(r) with errors\n"
	" @param args: c-parameters and r\n"
	" @return: (P(r),dP(r))";

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
	int i; 
	
	if (!PyArg_ParseTuple(args, "OOd", &data_obj, &err_obj, &r)) return NULL;
	OUTVECTOR(data_obj,pars,npars); 
	OUTVECTOR(err_obj,pars_err,npars2);

	pr_err(pars, pars_err, self->params.d_max, npars, r, &pr_value, &pr_err_value);
	return Py_BuildValue("ff", pr_value, pr_err_value);	
}

const char basefunc_ft_doc[] = 
	"Returns the value of the nth Fourier transofrmed base function\n"
	" @param args: c-parameters, n and q\n"
	" @return: nth Fourier transformed base function, evaluated at q";

static PyObject * basefunc_ft(Cinvertor *self, PyObject *args) {
	double d_max, q;
	int n;
	
	if (!PyArg_ParseTuple(args, "did", &d_max, &n, &q)) return NULL;
	return Py_BuildValue("f", ortho_transformed(d_max, n, q));	
	
}

const char oscillations_doc[] = 
	"Returns the value of the oscillation figure of merit for\n"
	"the given set of coefficients. For a sphere, the oscillation\n"
	"figure of merit is 1.1.\n"
	" @param args: c-parameters\n"
	" @return: oscillation figure of merit";

static PyObject * oscillations(Cinvertor *self, PyObject *args) {
	double *pars;
	PyObject *data_obj;
	Py_ssize_t npars;
	double oscill, norm;
	
	if (!PyArg_ParseTuple(args, "O", &data_obj)) return NULL;
	OUTVECTOR(data_obj,pars,npars);
	
	oscill = reg_term(pars, self->params.d_max, npars, 100);
	norm   = int_p2(pars, self->params.d_max, npars, 100);
	return Py_BuildValue("f", sqrt(oscill/norm)/acos(-1.0)*self->params.d_max );	
	
}

const char get_peaks_doc[] = 
	"Returns the number of peaks in the output P(r) distrubution\n"
	"for the given set of coefficients.\n"
	" @param args: c-parameters\n"
	" @return: number of P(r) peaks";

static PyObject * get_peaks(Cinvertor *self, PyObject *args) {
	double *pars;
	PyObject *data_obj;
	Py_ssize_t npars;
	int count;
	
	if (!PyArg_ParseTuple(args, "O", &data_obj)) return NULL;
	OUTVECTOR(data_obj,pars,npars);
	
	count = npeaks(pars, self->params.d_max, npars, 100);

	return Py_BuildValue("i", count );	
	
}

const char get_positive_doc[] = 
	"Returns the fraction of P(r) that is positive over\n"
	"the full range of r for the given set of coefficients.\n"
	" @param args: c-parameters\n"
	" @return: fraction of P(r) that is positive";

static PyObject * get_positive(Cinvertor *self, PyObject *args) {
	double *pars;
	PyObject *data_obj;
	Py_ssize_t npars;
	double fraction;
	 
	if (!PyArg_ParseTuple(args, "O", &data_obj)) return NULL;
	OUTVECTOR(data_obj,pars,npars);
	
	fraction = positive_integral(pars, self->params.d_max, npars, 100);

	return Py_BuildValue("f", fraction );	
	
}

const char get_pos_err_doc[] = 
	"Returns the fraction of P(r) that is 1 standard deviation\n"
	"above zero over the full range of r for the given set of coefficients.\n"
	" @param args: c-parameters\n"
	" @return: fraction of P(r) that is positive";

static PyObject * get_pos_err(Cinvertor *self, PyObject *args) {
	double *pars;
	double *pars_err;
	PyObject *data_obj;
	PyObject *err_obj;
	Py_ssize_t npars;
	Py_ssize_t npars2;
	double fraction;
	
	if (!PyArg_ParseTuple(args, "OO", &data_obj, &err_obj)) return NULL;
	OUTVECTOR(data_obj,pars,npars); 
	OUTVECTOR(err_obj,pars_err,npars2);
	
	fraction = positive_errors(pars, pars_err, self->params.d_max, npars, 51);

	return Py_BuildValue("f", fraction );	
	
}


const char eeeget_qmin_doc[] = "\
This is a multiline doc string.\n\
\n\
This is the second line.";
const char eeeset_qmin_doc[] = 
	"This is a multiline doc string.\n"
	"\n"
	"This is the second line.";

static PyMethodDef Cinvertor_methods[] = {
		   {"residuals", (PyCFunction)residuals, METH_VARARGS, residuals_doc},
		   {"pr_residuals", (PyCFunction)pr_residuals, METH_VARARGS, pr_residuals_doc},
		   {"set_x", (PyCFunction)set_x, METH_VARARGS, set_x_doc},
		   {"get_x", (PyCFunction)get_x, METH_VARARGS, get_x_doc},
		   {"set_y", (PyCFunction)set_y, METH_VARARGS, set_y_doc},
		   {"get_y", (PyCFunction)get_y, METH_VARARGS, get_y_doc},
		   {"set_err", (PyCFunction)set_err, METH_VARARGS, set_err_doc},
		   {"get_err", (PyCFunction)get_err, METH_VARARGS, get_err_doc},
		   {"set_dmax", (PyCFunction)set_dmax, METH_VARARGS, set_dmax_doc},
		   {"get_dmax", (PyCFunction)get_dmax, METH_VARARGS, get_dmax_doc},
		   {"set_qmin", (PyCFunction)set_qmin, METH_VARARGS, set_qmin_doc},
		   {"get_qmin", (PyCFunction)get_qmin, METH_VARARGS, get_qmin_doc},
		   {"set_qmax", (PyCFunction)set_qmax, METH_VARARGS, set_qmax_doc},
		   {"get_qmax", (PyCFunction)get_qmax, METH_VARARGS, get_qmax_doc},
		   {"set_alpha", (PyCFunction)set_alpha, METH_VARARGS, set_alpha_doc},
		   {"get_alpha", (PyCFunction)get_alpha, METH_VARARGS, get_alpha_doc},
		   {"get_nx", (PyCFunction)get_nx, METH_VARARGS, get_nx_doc},
		   {"get_ny", (PyCFunction)get_ny, METH_VARARGS, get_ny_doc},
		   {"get_nerr", (PyCFunction)get_nerr, METH_VARARGS, get_nerr_doc},
		   {"iq", (PyCFunction)get_iq, METH_VARARGS, get_iq_doc},
		   {"pr", (PyCFunction)get_pr, METH_VARARGS, get_pr_doc},
		   {"get_pr_err", (PyCFunction)get_pr_err, METH_VARARGS, get_pr_err_doc},
		   {"is_valid", (PyCFunction)is_valid, METH_VARARGS, is_valid_doc},
		   {"basefunc_ft", (PyCFunction)basefunc_ft, METH_VARARGS, basefunc_ft_doc},
		   {"oscillations", (PyCFunction)oscillations, METH_VARARGS, oscillations_doc},
		   {"get_peaks", (PyCFunction)get_peaks, METH_VARARGS, get_peaks_doc},
		   {"get_positive", (PyCFunction)get_positive, METH_VARARGS, get_positive_doc},
		   {"get_pos_err", (PyCFunction)get_pos_err, METH_VARARGS, get_pos_err_doc},
   
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
