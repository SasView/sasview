/**
  SLD2I module to perform point and I calculations
 */
#include <Python.h>
#include <stdio.h>
#include <sld2i.hh>

#if PY_MAJOR_VERSION < 3
typedef void (*PyCapsule_Destructor)(PyObject *);
typedef void (*PyCObject_Destructor)(void *);
#define PyCapsule_New(pointer, name, destructor) (PyCObject_FromVoidPtr(pointer, (PyCObject_Destructor)destructor))
#define PyCapsule_GetPointer(capsule, name) (PyCObject_AsVoidPtr(capsule))
#endif


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
 * Delete a GenI object
 */
void
del_sld2i(PyObject *obj){
	GenI* sld2i = static_cast<GenI *>(PyCapsule_GetPointer(obj, "GenI"));
	delete sld2i;
	return;
}

/**
 * Create a GenI as a python object by supplying arrays
 */
PyObject * new_GenI(PyObject *, PyObject *args) {
	PyObject *x_val_obj;
	PyObject *y_val_obj;
	PyObject *z_val_obj;
	PyObject *sldn_val_obj;
	PyObject *mx_val_obj;
	PyObject *my_val_obj;
	PyObject *mz_val_obj;
	PyObject *vol_pix_obj;
	Py_ssize_t n_x;
	//PyObject rlimit_obj;
	//PyObject npoints_obj;
	//PyObject nrbins_obj;
	//PyObject nphibins_obj;
	int n_pix;
	double* x_val;
	double* y_val;
	double* z_val;
	double* sldn_val;
	double* mx_val;
	double* my_val;
	double* mz_val;
	double* vol_pix;
	double inspin;
	double outspin;
	double stheta;

	if (!PyArg_ParseTuple(args, "iOOOOOOOOddd", &n_pix, &x_val_obj, &y_val_obj, &z_val_obj, &sldn_val_obj, &mx_val_obj, &my_val_obj, &mz_val_obj, &vol_pix_obj, &inspin, &outspin, &stheta)) return NULL;
	OUTVECTOR(x_val_obj, x_val, n_x);
	OUTVECTOR(y_val_obj, y_val, n_x);
	OUTVECTOR(z_val_obj, z_val, n_x);
	OUTVECTOR(sldn_val_obj, sldn_val, n_x);
	OUTVECTOR(mx_val_obj, mx_val, n_x);
	OUTVECTOR(my_val_obj, my_val, n_x);
	OUTVECTOR(mz_val_obj, mz_val, n_x);
	OUTVECTOR(vol_pix_obj, vol_pix, n_x);
	GenI* sld2i = new GenI(n_pix,x_val,y_val,z_val,sldn_val,mx_val,my_val,mz_val,vol_pix,inspin,outspin,stheta);
	return PyCapsule_New(sld2i, "GenI", del_sld2i);
}

/**
 * GenI the given input (2D) according to a given object
 */
PyObject * genicom_inputXY(PyObject *, PyObject *args) {
	int npoints;
	PyObject *qx_obj;
	double *qx;
	PyObject *qy_obj;
	double *qy;
	PyObject *I_out_obj;
	Py_ssize_t n_out;
	double *I_out;
	PyObject *gen_obj;

	if (!PyArg_ParseTuple(args, "OiOOO",  &gen_obj, &npoints, &qx_obj, &qy_obj, &I_out_obj)) return NULL;
	OUTVECTOR(qx_obj, qx, n_out);
	OUTVECTOR(qy_obj, qy, n_out);
	OUTVECTOR(I_out_obj, I_out, n_out);

	// Sanity check
	//if(n_in!=n_out) return Py_BuildValue("i",-1);

	// Set the array pointers
	void *temp = PyCapsule_GetPointer(gen_obj, "GenI");
	GenI* s = static_cast<GenI *>(temp);

	s->genicomXY(npoints, qx, qy, I_out);
	//return PyCObject_FromVoidPtr(s, del_genicom);
	return Py_BuildValue("i",1);
}

/**
 * GenI the given 1D input according to a given object
 */
PyObject * genicom_input(PyObject *, PyObject *args) {
	int npoints;
	PyObject *q_obj;
	double *q;
	PyObject *I_out_obj;
	Py_ssize_t n_out;
	double *I_out;
	PyObject *gen_obj;

	if (!PyArg_ParseTuple(args, "OiOO",  &gen_obj, &npoints, &q_obj, &I_out_obj)) return NULL;
	OUTVECTOR(q_obj, q, n_out);
	OUTVECTOR(I_out_obj, I_out, n_out);

	// Sanity check
	//if(n_in!=n_out) return Py_BuildValue("i",-1);

	// Set the array pointers
	void *temp = PyCapsule_GetPointer(gen_obj, "GenI");
	GenI* s = static_cast<GenI *>(temp);

	s->genicom(npoints, q, I_out);
	//return PyCObject_FromVoidPtr(s, del_genicom);
	return Py_BuildValue("i",1);
}

/**
 * Define module methods
 */
static PyMethodDef module_methods[] = {
	{"new_GenI", (PyCFunction)new_GenI, METH_VARARGS,
		  "Create a new GenI object"},
	{"genicom",(PyCFunction)genicom_input, METH_VARARGS,
		  "genicom the given 1d input arrays"},
	{"genicomXY",(PyCFunction)genicom_inputXY, METH_VARARGS,
		  "genicomXY the given 2d input arrays"},
    {NULL}
};

#define MODULE_DOC "Sld2i C Library"
#define MODULE_NAME "sld2i"
#define MODULE_INIT2 initsld2i
#define MODULE_INIT3 PyInit_sld2i
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
    return PyModule_Create(&moduledef);
  }

#else /* !PY_MAJOR_VERSION >= 3 */

  DLL_EXPORT PyMODINIT_FUNC MODULE_INIT2(void)
  {
    Py_InitModule4(MODULE_NAME,
		 MODULE_METHODS,
		 MODULE_DOC,
		 0,
		 PYTHON_API_VERSION
		 );
  }

#endif /* !PY_MAJOR_VERSION >= 3 */