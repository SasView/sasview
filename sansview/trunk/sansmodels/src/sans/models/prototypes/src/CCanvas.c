
#include <Python.h>
#include "structmember.h"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

#include "canvas.h"

/// Error object for raised exceptions
static PyObject * CCanvasError = NULL;


// Class definition
typedef struct {
    PyObject_HEAD
    /// Parameters
    PyObject * params;
    /// Model parameters
	CanvasParams canvas_pars;
} CCanvas;


static void
CCanvas_dealloc(CCanvas* self)
{
    canvas_dealloc(&(self->canvas_pars));
     
    self->ob_type->tp_free((PyObject*)self);

}

static PyObject *
CCanvas_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    CCanvas *self;
    
    self = (CCanvas *)type->tp_alloc(type, 0);
   
    return (PyObject *)self;
}

static int
CCanvas_init(CCanvas *self, PyObject *args, PyObject *kwds)
{
    if (self != NULL) {
		srand(1001);	
    	
    	// Create parameters
        self->params = PyDict_New();
  		canvas_init(&(self->canvas_pars));
    }
    return 0;
}

static PyMemberDef CCanvas_members[] = {
    {"params", T_OBJECT, offsetof(CCanvas, params), 0,
     "Parameters"},
    {NULL}  /* Sentinel */
};

/** Read double from PyObject
    @param p PyObject
    @return double
*/
double CCanvas_readDouble(PyObject *p) {
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
 * Function to call to evaluate model
 * @param args: input q or [q,phi]
 * @return: function value
 */
static PyObject * run(CCanvas *self, PyObject *args) {
	double q_value, phi_value;
	PyObject* pars;
	int npars;
	
	// Get input and determine whether we have to supply a 1D or 2D return value.
	if ( !PyArg_ParseTuple(args,"O",&pars) ) {
	    PyErr_SetString(CCanvasError, 
	    	"CCanvas.run expects a q value.");
		return NULL;
	}
	  
	// Check params
	if( PyList_Check(pars)==1) {
		
		// Length of list should be 2 for I(q,phi)
	    npars = PyList_GET_SIZE(pars); 
	    if(npars!=2) {
	    	PyErr_SetString(CCanvasError, 
	    		"CCanvas.run expects a double or a list of dimension 2.");
	    	return NULL;
	    }
	    // We have a vector q, get the q and phi values at which
	    // to evaluate I(q,phi)
	    q_value = CCanvas_readDouble(PyList_GET_ITEM(pars,0));
	    phi_value = CCanvas_readDouble(PyList_GET_ITEM(pars,1));
	    // Skip zero
	    if (q_value==0) {
	    	return Py_BuildValue("d",0.0);
	    }
		return Py_BuildValue("d",canvas_intensity(&(self->canvas_pars),q_value,phi_value));

	} else {

		// We have a scalar q, we will evaluate I(q)
		q_value = CCanvas_readDouble(pars);		
		
		return Py_BuildValue("d",0.0);
	}	
}

static PyObject * add(CCanvas *self, PyObject *args) {
	int id;
	
	id = canvas_add(&(self->canvas_pars),REALSPACE_SPHERE);
    return Py_BuildValue("i",id);
}

static PyObject * setParam(CCanvas *self, PyObject *args) {
	int id, par_id;
	double value;
	double radius;

	// Get input and determine whether we have to supply a 1D or 2D return value.
	if ( !PyArg_ParseTuple(args,"iid",&id, &par_id, &value) ) {
	    PyErr_SetString(CCanvasError, 
	    	"CCanvas.run expects a q value.");
		return NULL;
	}

	canvas_setParam(&(self->canvas_pars),id,par_id,value);
	
	return Py_BuildValue("i",id);
}


static PyMethodDef CCanvas_methods[] = {
    {"evaluate",      (PyCFunction)run     , METH_VARARGS,
      "Evaluate the model at a given Q"},
    {"add",    (PyCFunction)add   , METH_VARARGS, "Add a shape object"},
    {"setParam",    (PyCFunction)setParam   , METH_VARARGS, "Set a parameter"},
   {NULL}
};

static PyTypeObject CCanvasType = {
    PyObject_HEAD_INIT(NULL)
    0,                         /*ob_size*/
    "CCanvas",             /*tp_name*/
    sizeof(CCanvas),             /*tp_basicsize*/
    0,                         /*tp_itemsize*/
    (destructor)CCanvas_dealloc, /*tp_dealloc*/
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
    "CCanvas objects",           /* tp_doc */
    0,		               /* tp_traverse */
    0,		               /* tp_clear */
    0,		               /* tp_richcompare */
    0,		               /* tp_weaklistoffset */
    0,		               /* tp_iter */
    0,		               /* tp_iternext */
    CCanvas_methods,             /* tp_methods */
    CCanvas_members,             /* tp_members */
    0,                         /* tp_getset */
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    (initproc)CCanvas_init,      /* tp_init */
    0,                         /* tp_alloc */
    CCanvas_new,                 /* tp_new */
};


static PyMethodDef module_methods[] = {
    {NULL} 
};

/**
 * Function used to add the model class to a module
 * @param module: module to add the class to
 */ 
void addCCanvas(PyObject *module) {
	PyObject *d;
	
    if (PyType_Ready(&CCanvasType) < 0)
        return;

    Py_INCREF(&CCanvasType);
    PyModule_AddObject(module, "CCanvas", (PyObject *)&CCanvasType);
    
    d = PyModule_GetDict(module);
    CCanvasError = PyErr_NewException("CCanvas.error", NULL, NULL);
    PyDict_SetItemString(d, "CCanvasError", CCanvasError);
}

