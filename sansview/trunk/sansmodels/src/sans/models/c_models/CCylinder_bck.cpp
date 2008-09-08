/**
	This software was developed by the University of Tennessee as part of the
	Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
	project funded by the US National Science Foundation.

	If you use DANSE applications to do scientific research that leads to
	publication, we ask that you acknowledge the use of the software with the
	following sentence:

	"This work benefited from DANSE software developed under NSF award DMR-0520547."

	copyright 2008, University of Tennessee
 */

/** CCylinderModel
 *
 * Base python class for cylinder model
 *
 */
extern "C" {
#include <Python.h>
#include "structmember.h"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#include "cylinder.h"
}


#include "models.hh"
#include "dispersion_visitor.hh"

/// Error object for raised exceptions
static PyObject * CCylinderModelError = NULL;


// Class definition
typedef struct {
    PyObject_HEAD
    /// Parameters
    PyObject * params;
    PyObject * dispersion;
    CylinderModel * model;
    /// Log for unit testing
    PyObject * log;
} CCylinderModel;


static void
CCylinderModel_dealloc(CCylinderModel* self)
{
    self->ob_type->tp_free((PyObject*)self);


}

static PyObject *
CCylinderModel_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    CCylinderModel *self;

    self = (CCylinderModel *)type->tp_alloc(type, 0);

    return (PyObject *)self;
}

static int
CCylinderModel_init(CCylinderModel *self, PyObject *args, PyObject *kwds)
{
    if (self != NULL) {
    	printf("Hello cylinder\n");
    	// Create parameters
        self->params = PyDict_New();
        self->dispersion = PyDict_New();
        self->model = new CylinderModel();

        // Initialize parameter dictionary
        PyDict_SetItemString(self->params,"scale",     Py_BuildValue("d", self->model->scale()));
        PyDict_SetItemString(self->params,"length",    Py_BuildValue("d", self->model->length()));
        PyDict_SetItemString(self->params,"cyl_theta", Py_BuildValue("d", self->model->cyl_theta()));
        PyDict_SetItemString(self->params,"background",Py_BuildValue("d", self->model->background()));
        PyDict_SetItemString(self->params,"radius",    Py_BuildValue("d", self->model->radius()));
        PyDict_SetItemString(self->params,"contrast",  Py_BuildValue("d", self->model->contrast()));
        PyDict_SetItemString(self->params,"cyl_phi",   Py_BuildValue("d", self->model->cyl_phi()));

        // Initialize dispersion / averaging parameter dict
        DispersionVisitor* visitor = new DispersionVisitor();
        PyObject * disp_dict = PyDict_New();
        self->model->radius.dispersion->accept_as_source(visitor, self->model->radius.dispersion, disp_dict);
        PyDict_SetItemString(self->dispersion, "radius", disp_dict);

        disp_dict = PyDict_New();
        self->model->length.dispersion->accept_as_source(visitor, self->model->length.dispersion, disp_dict);
        PyDict_SetItemString(self->dispersion, "length", disp_dict);

        disp_dict = PyDict_New();
        self->model->cyl_phi.dispersion->accept_as_source(visitor, self->model->cyl_phi.dispersion, disp_dict);
        PyDict_SetItemString(self->dispersion, "cyl_phi", disp_dict);

        disp_dict = PyDict_New();
        self->model->cyl_theta.dispersion->accept_as_source(visitor, self->model->cyl_theta.dispersion, disp_dict);
        PyDict_SetItemString(self->dispersion, "cyl_theta", disp_dict);

        // Create empty log
        self->log = PyDict_New();

    }
    return 0;
}

static PyMemberDef CCylinderModel_members[] = {
	{"params", T_OBJECT, offsetof(CCylinderModel, params), 0,
	 "Parameters"},
	{"dispersion", T_OBJECT, offsetof(CCylinderModel, dispersion), 0,
	  "Dispersion parameters"},
    {"log", T_OBJECT, offsetof(CCylinderModel, log), 0,
     "Log"},
    {NULL}  /* Sentinel */
};

/** Read double from PyObject
    @param p PyObject
    @return double
*/
double CCylinderModel_readDouble(PyObject *p) {
    if (PyFloat_Check(p)==1) {
        return (double)(((PyFloatObject *)(p))->ob_fval);
    } else if (PyInt_Check(p)==1) {
        return (double)(((PyIntObject *)(p))->ob_ival);
    } else if (PyLong_Check(p)==1) {
        return (double)PyLong_AsLong(p);
    } else {
        return 0.0;
    }
}

/**
 * Method to set the dispersion model for a parameter.
 * We need to update the dispersion object of the parameter
 * on the C++ side and update the dispersion dictionary on the python side.
 *
 * TODO: define read-only integers that will be data members of this
 * class and allow the user to specify which model is needed with a code name.
 *
 * This method should take in a code name (FLAT, GAUSSIAN) and a string
 * that represent the parameter to attach the dispersion model to.
 *
 */
static PyObject * set_dispersion_model(CCylinderModel *self, PyObject *args) {

}

/**
 * Function to call to evaluate model
 * @param args: input q or [q,phi]
 * @return: function value
 */
static PyObject * run(CCylinderModel *self, PyObject *args) {
	double q_value, phi_value;
	PyObject* pars;
	int npars;

	// Get parameters

	// Reader parameter dictionary
    self->model->scale = PyFloat_AsDouble( PyDict_GetItemString(self->params, "scale") );
    self->model->length = PyFloat_AsDouble( PyDict_GetItemString(self->params, "length") );
    self->model->cyl_theta = PyFloat_AsDouble( PyDict_GetItemString(self->params, "cyl_theta") );
    self->model->background = PyFloat_AsDouble( PyDict_GetItemString(self->params, "background") );
    self->model->radius = PyFloat_AsDouble( PyDict_GetItemString(self->params, "radius") );
    self->model->contrast = PyFloat_AsDouble( PyDict_GetItemString(self->params, "contrast") );
    self->model->cyl_phi = PyFloat_AsDouble( PyDict_GetItemString(self->params, "cyl_phi") );

    // Read in dispersion parameters
    PyObject* disp_dict;

    DispersionVisitor* visitor = new DispersionVisitor();
    disp_dict = PyDict_GetItemString(self->dispersion, "radius");
    self->model->radius.dispersion->accept_as_destination(visitor, self->model->radius.dispersion, disp_dict);

    disp_dict = PyDict_GetItemString(self->dispersion, "length");
    self->model->length.dispersion->accept_as_destination(visitor, self->model->length.dispersion, disp_dict);

    disp_dict = PyDict_GetItemString(self->dispersion, "cyl_theta");
    self->model->cyl_theta.dispersion->accept_as_destination(visitor, self->model->cyl_theta.dispersion, disp_dict);

    disp_dict = PyDict_GetItemString(self->dispersion, "cyl_phi");
    self->model->cyl_phi.dispersion->accept_as_destination(visitor, self->model->cyl_phi.dispersion, disp_dict);


	// Get input and determine whether we have to supply a 1D or 2D return value.
	if ( !PyArg_ParseTuple(args,"O",&pars) ) {
	    PyErr_SetString(CCylinderModelError,
	    	"CCylinderModel.run expects a q value.");
		return NULL;
	}

	// Check params
	if( PyList_Check(pars)==1) {

		// Length of list should be 2 for I(q,phi)
	    npars = PyList_GET_SIZE(pars);
	    if(npars!=2) {
	    	PyErr_SetString(CCylinderModelError,
	    		"CCylinderModel.run expects a double or a list of dimension 2.");
	    	return NULL;
	    }
	    // We have a vector q, get the q and phi values at which
	    // to evaluate I(q,phi)
	    q_value = CCylinderModel_readDouble(PyList_GET_ITEM(pars,0));
	    phi_value = CCylinderModel_readDouble(PyList_GET_ITEM(pars,1));
	    // Skip zero
	    if (q_value==0) {
	    	return Py_BuildValue("d",0.0);
	    }
		return Py_BuildValue("d",(*(self->model)).evaluate_rphi(q_value,phi_value));

	} else {

		// We have a scalar q, we will evaluate I(q)
		q_value = CCylinderModel_readDouble(pars);

		return Py_BuildValue("d",(*(self->model))(q_value));
	}
}

/**
 * Function to call to evaluate model in cartesian coordinates
 * @param args: input q or [qx, qy]]
 * @return: function value
 */
static PyObject * runXY(CCylinderModel *self, PyObject *args) {
	double qx_value, qy_value;
	PyObject* pars;
	int npars;

	// Get parameters

	// Reader parameter dictionary
    self->model->scale = PyFloat_AsDouble( PyDict_GetItemString(self->params, "scale") );
    self->model->length = PyFloat_AsDouble( PyDict_GetItemString(self->params, "length") );
    self->model->cyl_theta = PyFloat_AsDouble( PyDict_GetItemString(self->params, "cyl_theta") );
    self->model->background = PyFloat_AsDouble( PyDict_GetItemString(self->params, "background") );
    self->model->radius = PyFloat_AsDouble( PyDict_GetItemString(self->params, "radius") );
    self->model->contrast = PyFloat_AsDouble( PyDict_GetItemString(self->params, "contrast") );
    self->model->cyl_phi = PyFloat_AsDouble( PyDict_GetItemString(self->params, "cyl_phi") );

    // Read in dispersion parameters
    DispersionVisitor* visitor = new DispersionVisitor();
    PyObject* disp_dict = PyDict_New();
    disp_dict = PyDict_GetItemString(self->dispersion, "radius");
    self->model->radius.dispersion->accept_as_destination(visitor, self->model->radius.dispersion, disp_dict);

    disp_dict = PyDict_GetItemString(self->dispersion, "length");
    self->model->length.dispersion->accept_as_destination(visitor, self->model->length.dispersion, disp_dict);

    disp_dict = PyDict_GetItemString(self->dispersion, "cyl_theta");
    self->model->cyl_theta.dispersion->accept_as_destination(visitor, self->model->cyl_theta.dispersion, disp_dict);

    disp_dict = PyDict_GetItemString(self->dispersion, "cyl_phi");
    self->model->cyl_phi.dispersion->accept_as_destination(visitor, self->model->cyl_phi.dispersion, disp_dict);

	// Get input and determine whether we have to supply a 1D or 2D return value.
	if ( !PyArg_ParseTuple(args,"O",&pars) ) {
	    PyErr_SetString(CCylinderModelError,
	    	"CCylinderModel.run expects a q value.");
		return NULL;
	}

	// Check params
	if( PyList_Check(pars)==1) {

		// Length of list should be 2 for I(qx, qy))
	    npars = PyList_GET_SIZE(pars);
	    if(npars!=2) {
	    	PyErr_SetString(CCylinderModelError,
	    		"CCylinderModel.run expects a double or a list of dimension 2.");
	    	return NULL;
	    }
	    // We have a vector q, get the qx and qy values at which
	    // to evaluate I(qx,qy)
	    qx_value = CCylinderModel_readDouble(PyList_GET_ITEM(pars,0));
	    qy_value = CCylinderModel_readDouble(PyList_GET_ITEM(pars,1));
	    return Py_BuildValue("d",(*(self->model))(qx_value,qy_value));

	} else {

		// We have a scalar q, we will evaluate I(q)
		qx_value = CCylinderModel_readDouble(pars);
		return Py_BuildValue("d",(*(self->model))(qx_value));
	}
}

static PyObject * reset(CCylinderModel *self, PyObject *args) {


    return Py_BuildValue("d",0.0);
}

static PyObject * set_dispersion(CCylinderModel *self, PyObject *args) {
	PyObject * disp;
	const char * par_name;

	if ( !PyArg_ParseTuple(args,"sO", &par_name, &disp) ) {
	    PyErr_SetString(CCylinderModelError,
	    	"CCylinderModel.set_dispersion expects a DispersionModel object.");
		return NULL;
	}
	void *temp = PyCObject_AsVoidPtr(disp);
	DispersionModel * dispersion = static_cast<DispersionModel *>(temp);


	// Ugliness necessary to go from python to C
	if (!strcmp(par_name, "radius")) {
		self->model->radius.dispersion = dispersion;
	} else if (!strcmp(par_name, "length")) {
		self->model->length.dispersion = dispersion;
	} else if (!strcmp(par_name, "cyl_theta")) {
		self->model->cyl_theta.dispersion = dispersion;
	} else if (!strcmp(par_name, "cyl_phi")) {
		self->model->cyl_phi.dispersion = dispersion;
	} else {
	    PyErr_SetString(CCylinderModelError,
	    	"CCylinderModel.set_dispersion expects a valid parameter name.");
		return NULL;
	}

	DispersionVisitor* visitor = new DispersionVisitor();
	PyObject * disp_dict = PyDict_New();
	dispersion->accept_as_source(visitor, dispersion, disp_dict);
	PyDict_SetItemString(self->dispersion, par_name, disp_dict);
    return Py_BuildValue("i",1);
}


static PyMethodDef CCylinderModel_methods[] = {
    {"run",      (PyCFunction)run     , METH_VARARGS,
      "Evaluate the model at a given Q or Q, phi"},
    {"runXY",      (PyCFunction)runXY     , METH_VARARGS,
      "Evaluate the model at a given Q or Qx, Qy"},
    {"reset",    (PyCFunction)reset   , METH_VARARGS,
      "Reset pair correlation"},
    {"set_dispersion",      (PyCFunction)set_dispersion     , METH_VARARGS,
      "Set the dispersion model for a given parameter"},
   {NULL}
};

static PyTypeObject CCylinderModelType = {
    PyObject_HEAD_INIT(NULL)
    0,                         /*ob_size*/
    "CCylinderModel",             /*tp_name*/
    sizeof(CCylinderModel),             /*tp_basicsize*/
    0,                         /*tp_itemsize*/
    (destructor)CCylinderModel_dealloc, /*tp_dealloc*/
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
    "CCylinderModel objects",           /* tp_doc */
    0,		               /* tp_traverse */
    0,		               /* tp_clear */
    0,		               /* tp_richcompare */
    0,		               /* tp_weaklistoffset */
    0,		               /* tp_iter */
    0,		               /* tp_iternext */
    CCylinderModel_methods,             /* tp_methods */
    CCylinderModel_members,             /* tp_members */
    0,                         /* tp_getset */
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    (initproc)CCylinderModel_init,      /* tp_init */
    0,                         /* tp_alloc */
    CCylinderModel_new,                 /* tp_new */
};


static PyMethodDef module_methods[] = {
    {NULL}
};

/**
 * Function used to add the model class to a module
 * @param module: module to add the class to
 */
void addCCylinderModel(PyObject *module) {
	PyObject *d;

    if (PyType_Ready(&CCylinderModelType) < 0)
        return;

    Py_INCREF(&CCylinderModelType);
    PyModule_AddObject(module, "CCylinderModel", (PyObject *)&CCylinderModelType);

    d = PyModule_GetDict(module);
    CCylinderModelError = PyErr_NewException("CCylinderModel.error", NULL, NULL);
    PyDict_SetItemString(d, "CCylinderModelError", CCylinderModelError);
}

