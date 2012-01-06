/** 
 * Disperser
 * 
 * Python class that takes a model and averages its output
 * for a distribution of its parameters.
 * 
 * The parameters to be varied are specified at instantiation time.
 * The distributions are Gaussian, with std deviations specified for
 * each parameter at instantiation time.
 * 
 * @author   M.Doucet / UTK 
 */

#include <Python.h>
#include "structmember.h"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

/// Error object for raised exceptions
static PyObject * DisperserError = NULL;

// Class definition
typedef struct {
  PyObject_HEAD
  /// Dictionary of parameters for this class
  PyObject * params;
  /// Model object to disperse
  PyObject * model;
  /// Array of original values
  double * centers;
  /// Number of parameters to disperse
  int n_pars;
  /// Coordinate system flag
  int cylindrical;
} Disperser;

// Function definitions
double disperseParam(Disperser *self, int iPar, PyObject * pars);
double Disperser_readDouble(PyObject *p);

/**
 * Function to deallocate memory for the object
 */
static void
Disperser_dealloc(Disperser * self) {
  free(self->centers);
  self->ob_type->tp_free((PyObject*)self);
}

/**
 * Function to create a new Disperser object
 */
static PyObject *
Disperser_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
  Disperser *self;

  self = (Disperser *)type->tp_alloc(type, 0);

  return (PyObject *)self;
}

/**
 * Initialization of the object (__init__)
 */
static int
Disperser_init(Disperser *self, PyObject *args, PyObject *kwds)
{
  PyObject * model;
  PyObject * paramList;
  PyObject * sigmaList;

  if (self != NULL) {

    // Create parameters
    self->params = PyDict_New();

    // Get input
    if ( !PyArg_ParseTuple(args,"OOO",&model, &paramList, &sigmaList) ) {
      PyErr_SetString(DisperserError,
          "Disperser: could not parse to initialize. Need Disperser(model, paramList, sigmaList)");
      return -1;
    }

    // Check that the lists are of the right type
    if( PyList_Check(paramList)!=1 || PyList_Check(sigmaList)!=1 ) {
      PyErr_SetString(DisperserError,
          "Disperser: bad input parameters; did not find lists.");
      return -1;
    }

    // Check that the list lengths are compatible
    if( PyList_GET_SIZE(paramList) != PyList_GET_SIZE(sigmaList) ) {
      PyErr_SetString(DisperserError,
          "Disperser: supplied lists are not of the same length.");
      return -1;
    }

    // Set the data members
    self->model = model;

    // Number of parameters to disperse
    // Let run() find out since values can change
    self->n_pars = 0;

    // Set default coordinate system as cartesian
    self->cylindrical = 0;

    // Initialize parameter dictionary
    // Store the list of parameter names (strings)
    PyDict_SetItemString(self->params,"paramList", paramList);

    // Store the list of std deviations (floats)
    PyDict_SetItemString(self->params,"sigmaList", sigmaList);

    // Set the default number of points to average over
    PyDict_SetItemString(self->params,"n_pts",Py_BuildValue("i",25));
  }
  return 0;
}

/**
 * List of member to make public
 * Only the parameters and the model are available to python users
 */
static PyMemberDef Disperser_members[] = {
    {"params", T_OBJECT, offsetof(Disperser, params), 0,
        "Parameters"},
        {"model", T_OBJECT, offsetof(Disperser, model), 0,
            "Model to disperse"},
            {NULL}  /* Sentinel */
};

/** Read double from PyObject
 *	TODO: THIS SHOULD REALLY BE ELSEWHERE!
 *   @param p PyObject
 *   @return double
 */
double Disperser_readDouble(PyObject *p) {
  double value = 0.0;

  if (PyFloat_Check(p)==1) {
    value = (double)(((PyFloatObject *)(p))->ob_fval);
    //Py_DECREF(p);
    return value;
  } else if (PyInt_Check(p)==1) {
    value = (double)(((PyIntObject *)(p))->ob_ival);
    //Py_DECREF(p);
    return value;
  } else if (PyLong_Check(p)==1) {
    value = (double)PyLong_AsLong(p);
    //Py_DECREF(p);
    return value;
  } else {
    //Py_DECREF(p);
    return 0.0;
  }
}


/**
 * Function to call to evaluate model
 * @param args: input q or [qx,qy]
 * @return: function value
 */
static PyObject * runXY(Disperser *self, PyObject *args) {
  PyObject* pars;
  int n_pts;
  int i;
  double value;
  PyObject * result;
  PyObject * temp;

  // Get parameters

  // Check that the lists are of the right type
  if( PyList_Check(PyDict_GetItemString(self->params, "paramList"))!=1
      || PyList_Check(PyDict_GetItemString(self->params, "sigmaList"))!=1 ) {
    PyErr_SetString(DisperserError,
        "Disperser: bad input parameters; did not find lists.");
    return NULL;
  }

  // Reader parameter dictionary
  n_pts = PyInt_AsLong( PyDict_GetItemString(self->params, "n_pts") );

  // Check that the list lengths are compatible
  if( PyList_GET_SIZE(PyDict_GetItemString(self->params, "paramList"))
      != PyList_GET_SIZE(PyDict_GetItemString(self->params, "sigmaList")) ) {
    PyErr_SetString(DisperserError,
        "Disperser: supplied lists are not of the same length.");
    return NULL;
  }

  // Number of parameters to disperse
  self->n_pars = PyList_GET_SIZE(PyDict_GetItemString(self->params, "paramList"));

  // Allocate memory for centers
  free(self->centers);
  self->centers = (double *)malloc(self->n_pars * sizeof(double));
  if(self->centers==NULL) {
    PyErr_SetString(DisperserError,
        "Disperser.run could not allocate memory.");
    return NULL;
  }

  // Store initial values of those parameters
  for( i=0; i<self->n_pars; i++ ) {
    result = PyObject_CallMethod(self->model, "getParam", "(O)",
        PyList_GetItem( PyDict_GetItemString(self->params, "paramList"), i ));

    if( result == NULL ) {
      PyErr_SetString(DisperserError,
          "Disperser.run could not get current parameter values.");
      return NULL;
    } else {
      self->centers[i] = Disperser_readDouble(result);
      Py_DECREF(result);
    };
  }

  // Get input and determine whether we have to supply a 1D or 2D return value.
  if ( !PyArg_ParseTuple(args,"O",&pars) ) {
    PyErr_SetString(DisperserError,
        "Disperser.run expects a q value.");
    return NULL;
  }

  // Evaluate or calculate average
  if( self->n_pars > 0 ) {
    value = disperseParam(self, 0, pars);
  } else {
    if (self->cylindrical==1) {
      result = PyObject_CallMethod(self->model, "run", "(O)",pars);
    } else {
      result = PyObject_CallMethod(self->model, "runXY", "(O)",pars);
    }

    if( result == NULL ) {
      PyErr_SetString(DisperserError,
          "Disperser.run failed.");
      return NULL;
    } else {
      Py_DECREF(result);
      return result;
    }
  }

  // Put back the original model parameter values
  for( i=0; i<self->n_pars; i++ ) {
    // Maybe we need to decref the double here?
    temp = Py_BuildValue("d", self->centers[i]);
    result = PyObject_CallMethod(self->model, "setParam", "(OO)",
        PyList_GetItem( PyDict_GetItemString(self->params, "paramList"), i ),
        temp );
    Py_DECREF(temp);

    if( result == NULL ) {
      PyErr_SetString(DisperserError,
          "Disperser.run could not set back original parameter values.");
      return NULL;
    } else {
      Py_DECREF(result);
    };
  }

  return Py_BuildValue("d",value);

}

/**
 * Function to call to evaluate model
 * @param args: input q or [q,phi]
 * @return: function value
 */
static PyObject * run(Disperser *self, PyObject *args) {
  PyObject * output;
  self->cylindrical = 1;
  output = runXY(self, args);
  self->cylindrical = 0;
  return output;
}




/**
 * Gaussian weight
 * @param mean: mean value of the Gaussian
 * @param sigma: standard deviation of the Gaussian
 * @param x: value at which the Gaussian is evaluated
 * @return: value of the Gaussian
 */
double gaussian_weight(double mean, double sigma, double x) {
  double vary, expo_value;
  vary = x-mean;
  expo_value = -vary*vary/(2*sigma*sigma);
  //return 1.0;
  return exp(expo_value);
}

/**
 * @param iPar: ID of parameter to disperse
 * @param pars: input parameter to the evaluation function
 */
double disperseParam(Disperser *self, int iPar, PyObject * pars) {
  double sigma;
  double min_value, max_value;
  double step;
  double prev_value;
  double value_sum;
  double gauss_sum;
  double gauss_value;
  double func_value;
  double error_sys;
  double value;
  int i, n_pts;
  PyObject *result;
  PyObject *temp;

  step = 0.0;
  n_pts = PyInt_AsLong( PyDict_GetItemString(self->params, "n_pts") );

  // If we exhausted the parameter array, simply evaluate
  // the model
  if( iPar < self->n_pars ) {

    // Average over Gaussian distribution (2 sigmas)
    value_sum = 0.0;
    gauss_sum = 0.0;

    // Get the standard deviation for this parameter
    sigma = Disperser_readDouble(PyList_GetItem( PyDict_GetItemString(self->params, "sigmaList"), iPar ));

    // Average over 4 sigmas wide
    min_value = self->centers[iPar] - 2*sigma;
    max_value = self->centers[iPar] + 2*sigma;

    // Calculate step size
    step = (max_value - min_value)/(n_pts-1);

    // If we are not changing the parameter, just return the
    // value of the function
    if (step == 0.0) {
      return disperseParam(self, iPar+1, pars);
    }

    // Compute average
    prev_value = 0.0;
    error_sys  = 0.0;
    for( i=0; i<n_pts; i++ ) {
      // Set the parameter value
      value = min_value + (double)i*step;

      temp = Py_BuildValue("d", value);
      result = PyObject_CallMethod(self->model, "setParam", "(OO)",
          PyList_GetItem( PyDict_GetItemString(self->params, "paramList"), iPar ),
          temp);
      Py_DECREF(temp);

      if( result == NULL ) {
        printf("Could not set param %i\n", iPar);
        // return a value that will create an NAN
        return 0.0/(step-step);
      } else {
        Py_DECREF(result);
      }

      gauss_value = gaussian_weight(self->centers[iPar], sigma, value);
      func_value = disperseParam(self, iPar+1, pars);

      value_sum += gauss_value * func_value;
      gauss_sum += gauss_value;
    }
    return value_sum/gauss_sum;

  } else {
    if (self->cylindrical==1) {
      result = PyObject_CallMethod(self->model, "run", "(O)",pars);
    } else {
      result = PyObject_CallMethod(self->model, "runXY", "(O)",pars);
    }
    if( result == NULL ) {
      printf("Model.run() could not return\n");
      // return a value that will create an NAN
      return 0.0/(step-step);
    } else {
      value = Disperser_readDouble(result);
      Py_DECREF(result);
      return value;
    }
  }

}

static PyMethodDef Disperser_methods[] = {
    {"run",      (PyCFunction)run     , METH_VARARGS,
        "Evaluate the model at a given input value"},
        {"runXY",      (PyCFunction)runXY     , METH_VARARGS,
            "Evaluate the model at a given input value"},
            {NULL}
};

static PyTypeObject DisperserType = {
    PyObject_HEAD_INIT(NULL)
    0,                         /*ob_size*/
    "Disperser",             /*tp_name*/
    sizeof(Disperser),             /*tp_basicsize*/
    0,                         /*tp_itemsize*/
    (destructor)Disperser_dealloc, /*tp_dealloc*/
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
    "Disperser objects",           /* tp_doc */
    0,		               /* tp_traverse */
    0,		               /* tp_clear */
    0,		               /* tp_richcompare */
    0,		               /* tp_weaklistoffset */
    0,		               /* tp_iter */
    0,		               /* tp_iternext */
    Disperser_methods,             /* tp_methods */
    Disperser_members,             /* tp_members */
    0,                         /* tp_getset */
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    (initproc)Disperser_init,      /* tp_init */
    0,                         /* tp_alloc */
    Disperser_new,                 /* tp_new */
};


//static PyMethodDef module_methods[] = {
//    {NULL}
//};

/**
 * Function used to add the model class to a module
 * @param module: module to add the class to
 */ 
void addDisperser(PyObject *module) {
  PyObject *d;

  if (PyType_Ready(&DisperserType) < 0)
    return;

  Py_INCREF(&DisperserType);
  PyModule_AddObject(module, "Disperser", (PyObject *)&DisperserType);

  d = PyModule_GetDict(module);
  DisperserError = PyErr_NewException("Disperser.error", NULL, NULL);
  PyDict_SetItemString(d, "DisperserError", DisperserError);
}

