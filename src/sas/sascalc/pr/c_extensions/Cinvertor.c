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
PyObject * CinvertorError;

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

    Py_TYPE(self)->tp_free((PyObject*)self);

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
	self->params.npoints = (int)ndata;
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
	self->params.ny = (int)ndata;
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
	self->params.nerr = (int)ndata;
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

const char set_est_bck_doc[] =
	"Sets background flag\n";

/**
 * Sets the maximum distance
 */
static PyObject * set_est_bck(Cinvertor *self, PyObject *args) {
	int est_bck;

	if (!PyArg_ParseTuple(args, "i", &est_bck)) return NULL;
	self->params.est_bck = est_bck;
	return Py_BuildValue("i", self->params.est_bck);
}

const char get_est_bck_doc[] =
	"Gets background flag\n";

/**
 * Gets the maximum distance
 */
static PyObject * get_est_bck(Cinvertor *self, PyObject *args) {
	return Py_BuildValue("i", self->params.est_bck);
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

const char set_slit_height_doc[] =
	"Sets the slit height in units of q [A-1]\n";

/**
 * Sets the slit height
 */
static PyObject * set_slit_height(Cinvertor *self, PyObject *args) {
	double slit_height;

	if (!PyArg_ParseTuple(args, "d", &slit_height)) return NULL;
	self->params.slit_height = slit_height;
	return Py_BuildValue("d", self->params.slit_height);
}

const char get_slit_height_doc[] =
	"Gets the slit height\n";

/**
 * Gets the slit height
 */
static PyObject * get_slit_height(Cinvertor *self, PyObject *args) {
	return Py_BuildValue("d", self->params.slit_height);
}

const char set_slit_width_doc[] =
	"Sets the slit width in units of q [A-1]\n";

/**
 * Sets the slit width
 */
static PyObject * set_slit_width(Cinvertor *self, PyObject *args) {
	double slit_width;

	if (!PyArg_ParseTuple(args, "d", &slit_width)) return NULL;
	self->params.slit_width = slit_width;
	return Py_BuildValue("d", self->params.slit_width);
}

const char get_slit_width_doc[] =
	"Gets the slit width\n";

/**
 * Gets the slit width
 */
static PyObject * get_slit_width(Cinvertor *self, PyObject *args) {
	return Py_BuildValue("d", self->params.slit_width);
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
	int i;
	double residual, diff;
	// Regularization factor
	double regterm = 0.0;
	// Number of slices in regularization term estimate
	int nslice = 25;

	PyObject *data_obj;
	Py_ssize_t npars;

	if (!PyArg_ParseTuple(args, "O", &data_obj)) return NULL;

	OUTVECTOR(data_obj,pars,npars);

    // PyList of residuals
	// Should create this list only once and refill it
    residuals = PyList_New(self->params.npoints);

    regterm = reg_term(pars, self->params.d_max, (int)npars, nslice);

    for(i=0; i<self->params.npoints; i++) {
    	diff = self->params.y[i] - iq(pars, self->params.d_max, (int)npars, self->params.x[i]);
    	residual = diff*diff / (self->params.err[i]*self->params.err[i]);

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
	int i;
	double residual, diff;
	// Regularization factor
	double regterm = 0.0;
	// Number of slices in regularization term estimate
	int nslice = 25;

	PyObject *data_obj;
	Py_ssize_t npars;

	if (!PyArg_ParseTuple(args, "O", &data_obj)) return NULL;

	OUTVECTOR(data_obj,pars,npars);

	// Should create this list only once and refill it
    residuals = PyList_New(self->params.npoints);

    regterm = reg_term(pars, self->params.d_max, (int)npars, nslice);


    for(i=0; i<self->params.npoints; i++) {
    	diff = self->params.y[i] - pr(pars, self->params.d_max, (int)npars, self->params.x[i]);
    	residual = diff*diff / (self->params.err[i]*self->params.err[i]);

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

	iq_value = iq(pars, self->params.d_max, (int)npars, q);
	return Py_BuildValue("f", iq_value);
}

const char get_iq_smeared_doc[] =
	"Function to call to evaluate the scattering intensity.\n"
	"The scattering intensity is slit-smeared."
	" @param args: c-parameters, and q\n"
	" @return: I(q)";

/**
 * Function to call to evaluate the scattering intensity
 * The scattering intensity is slit-smeared.
 * @param args: c-parameters, and q
 * @return: I(q)
 */
static PyObject * get_iq_smeared(Cinvertor *self, PyObject *args) {
	double *pars;
	double q, iq_value;
	PyObject *data_obj;
	Py_ssize_t npars;

	if (!PyArg_ParseTuple(args, "Od", &data_obj, &q)) return NULL;
	OUTVECTOR(data_obj,pars,npars);

	iq_value = iq_smeared(pars, self->params.d_max, (int)npars,
							self->params.slit_height, self->params.slit_width,
							q, 21);
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

	pr_value = pr(pars, self->params.d_max, (int)npars, r);
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

	if (!PyArg_ParseTuple(args, "OOd", &data_obj, &err_obj, &r)) return NULL;
	OUTVECTOR(data_obj,pars,npars);

	if (err_obj == Py_None) {
		pr_value = pr(pars, self->params.d_max, (int)npars, r);
		pr_err_value = 0.0;
	} else {
		OUTVECTOR(err_obj,pars_err,npars2);
		pr_err(pars, pars_err, self->params.d_max, (int)npars, r, &pr_value, &pr_err_value);
	}
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

	oscill = reg_term(pars, self->params.d_max, (int)npars, 100);
	norm   = int_p2(pars, self->params.d_max, (int)npars, 100);
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

	count = npeaks(pars, self->params.d_max, (int)npars, 100);

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

	fraction = positive_integral(pars, self->params.d_max, (int)npars, 100);

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

	fraction = positive_errors(pars, pars_err, self->params.d_max, (int)npars, 51);

	return Py_BuildValue("f", fraction );

}

const char get_rg_doc[] =
	"Returns the value of the radius of gyration Rg.\n"
	" @param args: c-parameters\n"
	" @return: Rg";

static PyObject * get_rg(Cinvertor *self, PyObject *args) {
	double *pars;
	PyObject *data_obj;
	Py_ssize_t npars;
	double value;

	if (!PyArg_ParseTuple(args, "O", &data_obj)) return NULL;
	OUTVECTOR(data_obj,pars,npars);

	value = rg(pars, self->params.d_max, (int)npars, 101);

	return Py_BuildValue("f", value );

}

const char get_iq0_doc[] =
	"Returns the value of I(q=0).\n"
	" @param args: c-parameters\n"
	" @return: I(q=0)";

static PyObject * get_iq0(Cinvertor *self, PyObject *args) {
	double *pars;
	PyObject *data_obj;
	Py_ssize_t npars;
	double value;

	if (!PyArg_ParseTuple(args, "O", &data_obj)) return NULL;
	OUTVECTOR(data_obj,pars,npars);

	value = 4.0*acos(-1.0)*int_pr(pars, self->params.d_max, (int)npars, 101);

	return Py_BuildValue("f", value );

}

/**
 * Check whether a q-value is within acceptabel limits
 * Return 1 if accepted, 0 if rejected.
 */
int accept_q(Cinvertor *self, double q) {
    if (self->params.q_min>0 && q<self->params.q_min) return 0;
    if (self->params.q_max>0 && q>self->params.q_max) return 0;
    return 1;
}

const char get_matrix_doc[] =
	"Returns A matrix and b vector for least square problem.\n"
	" @param nfunc: number of base functions\n"
	" @param nr: number of r-points used when evaluating reg term.\n"
	" @param a: A array to fill\n"
	" @param b: b vector to fill\n"
	" @return: 0";

static PyObject * get_matrix(Cinvertor *self, PyObject *args) {
	double *a;
	double *b;
	PyObject *a_obj;
	PyObject *b_obj;
	Py_ssize_t n_a;
	Py_ssize_t n_b;
	// Number of bins for regularization term evaluation
	int nr, nfunc;
	int i, j, i_r;
	double r, sqrt_alpha, pi;
	double tmp;
	int offset;

	if (!PyArg_ParseTuple(args, "iiOO", &nfunc, &nr, &a_obj, &b_obj)) return NULL;
	OUTVECTOR(a_obj,a,n_a);
	OUTVECTOR(b_obj,b,n_b);

	assert(n_b>=nfunc);
	assert(n_a>=nfunc*(nr+self->params.npoints));

	sqrt_alpha = sqrt(self->params.alpha);
	pi = acos(-1.0);
	offset = (self->params.est_bck==1) ? 0 : 1;

    for (j=0; j<nfunc; j++) {
        for (i=0; i<self->params.npoints; i++) {
            if (self->params.err[i]==0.0) {
              PyErr_SetString(CinvertorError,
                "Cinvertor.get_matrix: Some I(Q) points have no error.");
              return NULL;
            }
            if (accept_q(self, self->params.x[i])){
                if (self->params.est_bck==1 && j==0) {
                    a[i*nfunc+j] = 1.0/self->params.err[i];
                } else {
                	if (self->params.slit_width>0 || self->params.slit_height>0) {
                		a[i*nfunc+j] = ortho_transformed_smeared(self->params.d_max,
                				j+offset, self->params.slit_height, self->params.slit_width,
                				self->params.x[i], 21)/self->params.err[i];
                	} else {
                		a[i*nfunc+j] = ortho_transformed(self->params.d_max, j+offset, self->params.x[i])/self->params.err[i];
                	}
            	}
            }
        }
        for (i_r=0; i_r<nr; i_r++){
            if (self->params.est_bck==1 && j==0) {
                a[(i_r+self->params.npoints)*nfunc+j] = 0.0;
            } else {
	            r = self->params.d_max/nr*i_r;
	            tmp = pi*(j+offset)/self->params.d_max;
	            a[(i_r+self->params.npoints)*nfunc+j] = sqrt_alpha * 1.0/nr*self->params.d_max*2.0*
	            (2.0*pi*(j+offset)/self->params.d_max*cos(pi*(j+offset)*r/self->params.d_max) +
	            tmp*tmp*r * sin(pi*(j+offset)*r/self->params.d_max));
	        }
        }
    }

    for (i=0; i<self->params.npoints; i++) {
        if (accept_q(self, self->params.x[i])){
            b[i] = self->params.y[i]/self->params.err[i];
         }
	}

	return Py_BuildValue("i", 0);

}

const char get_invcov_matrix_doc[] =
	" Compute the inverse covariance matrix, defined as inv_cov = a_transposed x a.\n"
	" @param nfunc: number of base functions\n"
	" @param nr: number of r-points used when evaluating reg term.\n"
	" @param a: A array to fill\n"
	" @param inv_cov: inverse covariance array to be filled\n"
	" @return: 0";

static PyObject * get_invcov_matrix(Cinvertor *self, PyObject *args) {
	double *a;
	PyObject *a_obj;
	Py_ssize_t n_a;
	double *inv_cov;
	PyObject *cov_obj;
	Py_ssize_t n_cov;
	int nr, nfunc;
	int i, j, k;

	if (!PyArg_ParseTuple(args, "iiOO", &nfunc, &nr, &a_obj, &cov_obj)) return NULL;
	OUTVECTOR(a_obj,a,n_a);
	OUTVECTOR(cov_obj,inv_cov,n_cov);

	assert(n_cov>=nfunc*nfunc);
	assert(n_a>=nfunc*(nr+self->params.npoints));

	for (i=0; i<nfunc; i++) {
		for (j=0; j<nfunc; j++) {
			inv_cov[i*nfunc+j] = 0.0;
			for (k=0; k<nr+self->params.npoints; k++) {
				inv_cov[i*nfunc+j] += a[k*nfunc+i]*a[k*nfunc+j];
			}
		}
	}
	return Py_BuildValue("i", 0);
}

const char get_reg_size_doc[] =
	" Compute the covariance matrix, defined as inv_cov = a_transposed x a.\n"
	" @param nfunc: number of base functions\n"
	" @param nr: number of r-points used when evaluating reg term.\n"
	" @param a: A array to fill\n"
	" @param inv_cov: inverse covariance array to be filled\n"
	" @return: 0";

static PyObject * get_reg_size(Cinvertor *self, PyObject *args) {
	double *a;
	PyObject *a_obj;
	Py_ssize_t n_a;
	int nr, nfunc;
	int i, j;
	double sum_sig, sum_reg;

	if (!PyArg_ParseTuple(args, "iiO", &nfunc, &nr, &a_obj)) return NULL;
	OUTVECTOR(a_obj,a,n_a);

	assert(n_a>=nfunc*(nr+self->params.npoints));

    sum_sig = 0.0;
    sum_reg = 0.0;
    for (j=0; j<nfunc; j++){
        for (i=0; i<self->params.npoints; i++){
            if (accept_q(self, self->params.x[i])==1)
                sum_sig += (a[i*nfunc+j])*(a[i*nfunc+j]);
        }
        for (i=0; i<nr; i++){
            sum_reg += (a[(i+self->params.npoints)*nfunc+j])*(a[(i+self->params.npoints)*nfunc+j]);
        }
    }
    return Py_BuildValue("ff", sum_sig, sum_reg);
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
		   {"set_slit_width", (PyCFunction)set_slit_width, METH_VARARGS, set_slit_width_doc},
		   {"get_slit_width", (PyCFunction)get_slit_width, METH_VARARGS, get_slit_width_doc},
		   {"set_slit_height", (PyCFunction)set_slit_height, METH_VARARGS, set_slit_height_doc},
		   {"get_slit_height", (PyCFunction)get_slit_height, METH_VARARGS, get_slit_height_doc},
		   {"set_est_bck", (PyCFunction)set_est_bck, METH_VARARGS, set_est_bck_doc},
		   {"get_est_bck", (PyCFunction)get_est_bck, METH_VARARGS, get_est_bck_doc},
		   {"get_nx", (PyCFunction)get_nx, METH_VARARGS, get_nx_doc},
		   {"get_ny", (PyCFunction)get_ny, METH_VARARGS, get_ny_doc},
		   {"get_nerr", (PyCFunction)get_nerr, METH_VARARGS, get_nerr_doc},
		   {"iq", (PyCFunction)get_iq, METH_VARARGS, get_iq_doc},
		   {"iq_smeared", (PyCFunction)get_iq_smeared, METH_VARARGS, get_iq_smeared_doc},
		   {"pr", (PyCFunction)get_pr, METH_VARARGS, get_pr_doc},
		   {"get_pr_err", (PyCFunction)get_pr_err, METH_VARARGS, get_pr_err_doc},
		   {"is_valid", (PyCFunction)is_valid, METH_VARARGS, is_valid_doc},
		   {"basefunc_ft", (PyCFunction)basefunc_ft, METH_VARARGS, basefunc_ft_doc},
		   {"oscillations", (PyCFunction)oscillations, METH_VARARGS, oscillations_doc},
		   {"get_peaks", (PyCFunction)get_peaks, METH_VARARGS, get_peaks_doc},
		   {"get_positive", (PyCFunction)get_positive, METH_VARARGS, get_positive_doc},
		   {"get_pos_err", (PyCFunction)get_pos_err, METH_VARARGS, get_pos_err_doc},
		   {"rg", (PyCFunction)get_rg, METH_VARARGS, get_rg_doc},
		   {"iq0", (PyCFunction)get_iq0, METH_VARARGS, get_iq0_doc},
		   {"_get_matrix", (PyCFunction)get_matrix, METH_VARARGS, get_matrix_doc},
		   {"_get_invcov_matrix", (PyCFunction)get_invcov_matrix, METH_VARARGS, get_invcov_matrix_doc},
		   {"_get_reg_size", (PyCFunction)get_reg_size, METH_VARARGS, get_reg_size_doc},

   {NULL}
};

static PyTypeObject CinvertorType = {
    //PyObject_HEAD_INIT(NULL)
    //0,                         /*ob_size*/
    PyVarObject_HEAD_INIT(NULL, 0)
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
    CinvertorError = PyErr_NewException("sas.sascalc.pr.invertor.Cinvertor.InvertorError", PyExc_RuntimeError, NULL);
    PyDict_SetItemString(d, "CinvertorError", CinvertorError);
}


#define MODULE_DOC "C extension module for inversion to P(r)."
#define MODULE_NAME "pr_inversion"
#define MODULE_INIT2 initpr_inversion
#define MODULE_INIT3 PyInit_pr_inversion
#define MODULE_METHODS module_methods

/* ==== boilerplate python 2/3 interface bootstrap ==== */


#if defined(WIN32) && !defined(__MINGW32__)
    #define DLL_EXPORT __declspec(dllexport)
#else
    #define DLL_EXPORT
#endif

#if PY_MAJOR_VERSION >= 3

  DLL_EXPORT PyMODINIT_FUNC MODULE_INIT3(void)
  {
    static struct PyModuleDef moduledef = {
      PyModuleDef_HEAD_INIT,
      MODULE_NAME,         /* m_name */
      MODULE_DOC,          /* m_doc */
      -1,                  /* m_size */
      MODULE_METHODS,      /* m_methods */
      NULL,                /* m_reload */
      NULL,                /* m_traverse */
      NULL,                /* m_clear */
      NULL,                /* m_free */
    };
	PyObject* m = PyModule_Create(&moduledef);
	addCinvertor(m);
	return m;
  }

#else /* !PY_MAJOR_VERSION >= 3 */

  DLL_EXPORT PyMODINIT_FUNC MODULE_INIT2(void)
  {
    PyObject* m = Py_InitModule4(MODULE_NAME,
		 MODULE_METHODS,
		 MODULE_DOC,
		 0,
		 PYTHON_API_VERSION
		 );
	addCinvertor(m);
  }

#endif /* !PY_MAJOR_VERSION >= 3 */