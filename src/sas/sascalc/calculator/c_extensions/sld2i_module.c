/**
  SLD2I module to perform point and I calculations
 */
#include <stdio.h>

//#define Py_LIMITED_API 0x03020000
#include <Python.h>

#include "sld2i.h"

#if PY_MAJOR_VERSION < 3
typedef void (*PyCapsule_Destructor)(PyObject *);
typedef void (*PyCObject_Destructor)(void *);
#define PyCapsule_New(pointer, name, destructor) (PyCObject_FromVoidPtr(pointer, (PyCObject_Destructor)destructor))
#define PyCapsule_GetPointer(capsule, name) (PyCObject_AsVoidPtr(capsule))
#endif

// Vector binding glue
#if (PY_VERSION_HEX > 0x03000000) && !defined(Py_LIMITED_API)
  // Assuming that a view into a writable vector points to a 
  // non-changing pointer for the duration of the C call, capture 
  // the view pointer and immediately free the view.
  #define VECTOR(VEC_obj, VEC_buf, VEC_len) do { \
    Py_buffer VEC_view; \
    int VEC_err = PyObject_GetBuffer(VEC_obj, &VEC_view, PyBUF_WRITABLE|PyBUF_FORMAT); \
    if (VEC_err < 0 || sizeof(*VEC_buf) != VEC_view.itemsize) return NULL; \
    VEC_buf = (typeof(VEC_buf))VEC_view.buf; \
    VEC_len = VEC_view.len/sizeof(*VEC_buf); \
    PyBuffer_Release(&VEC_view); \
  } while (0)
#else
  #define VECTOR(VEC_obj, VEC_buf, VEC_len) do { \
    int VEC_err = PyObject_AsWriteBuffer(VEC_obj, (void **)(&VEC_buf), &VEC_len); \
    if (VEC_err < 0) return NULL; \
    VEC_len /= sizeof(*VEC_buf); \
  } while (0)
#endif

/**
 * Delete a GenI object
 */
void
del_sld2i(PyObject *obj){
#if PY_MAJOR_VERSION < 3
	GenI* sld2i = (GenI *)obj;
#else
	GenI* sld2i = (GenI *)(PyCapsule_GetPointer(obj, "GenI"));
#endif
	PyMem_Free((void *)sld2i);
}

/**
 * Create a GenI as a python object by supplying arrays
 */
PyObject * new_GenI(PyObject *self, PyObject *args) {
	PyObject *x_val_obj;
	PyObject *y_val_obj;
	PyObject *z_val_obj;
	PyObject *sldn_val_obj;
	PyObject *mx_val_obj;
	PyObject *my_val_obj;
	PyObject *mz_val_obj;
	PyObject *vol_pix_obj;
	Py_ssize_t n_x, n_y, n_z, n_sld, n_mx, n_my, n_mz, n_vol_pix;
	int is_avg;
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
	PyObject *obj;
	GenI* sld2i;

	//printf("new GenI\n");
	if (!PyArg_ParseTuple(args, "iOOOOOOOOddd", &is_avg, &x_val_obj, &y_val_obj, &z_val_obj, &sldn_val_obj, &mx_val_obj, &my_val_obj, &mz_val_obj, &vol_pix_obj, &inspin, &outspin, &stheta)) return NULL;
	VECTOR(x_val_obj, x_val, n_x);
	VECTOR(y_val_obj, y_val, n_y);
	VECTOR(z_val_obj, z_val, n_z);
	VECTOR(sldn_val_obj, sldn_val, n_sld);
	VECTOR(mx_val_obj, mx_val, n_mx);
	VECTOR(my_val_obj, my_val, n_my);
	VECTOR(mz_val_obj, mz_val, n_mz);
	VECTOR(vol_pix_obj, vol_pix, n_vol_pix);
	sld2i = PyMem_Malloc(sizeof(GenI));
	//printf("sldi:%p\n", sld2i);
	if (sld2i != NULL) {
		initGenI(sld2i,is_avg,(int)n_x,x_val,y_val,z_val,sldn_val,mx_val,my_val,mz_val,vol_pix,inspin,outspin,stheta);
	}
	obj = PyCapsule_New(sld2i, "GenI", del_sld2i);
	//printf("constructed %p\n", obj);
	return obj;
}

/**
 * GenI the given input (2D) according to a given object
 */
PyObject * genicom_inputXY(PyObject *self, PyObject *args) {
	PyObject *gen_obj;
	PyObject *qx_obj;
	PyObject *qy_obj;
	PyObject *I_out_obj;
	Py_ssize_t n_qx, n_qy, n_out;
	double *qx;
	double *qy;
	double *I_out;
	GenI* sld2i;

	//printf("in genicom_inputXY\n");
	if (!PyArg_ParseTuple(args, "OOOO",  &gen_obj, &qx_obj, &qy_obj, &I_out_obj)) return NULL;
	sld2i = (GenI *)PyCapsule_GetPointer(gen_obj, "GenI");
	VECTOR(qx_obj, qx, n_qx);
	VECTOR(qy_obj, qy, n_qy);
	VECTOR(I_out_obj, I_out, n_out);
	//printf("qx, qy, I_out: %d %d %d, %d %d %d\n", qx, qy, I_out, n_qx, n_qy, n_out);

	// Sanity check
	//if(n_q!=n_out) return Py_BuildValue("i",-1);

	genicomXY(sld2i, (int)n_qx, qx, qy, I_out);
	//printf("done calc\n");
	//return PyCObject_FromVoidPtr(s, del_genicom);
	return Py_BuildValue("i",1);
}

/**
 * GenI the given 1D input according to a given object
 */
PyObject * genicom_input(PyObject *self, PyObject *args) {
	PyObject *gen_obj;
	PyObject *q_obj;
	PyObject *I_out_obj;
	Py_ssize_t n_q, n_out;
	double *q;
	double *I_out;
	GenI *sld2i;

	if (!PyArg_ParseTuple(args, "OOO",  &gen_obj, &q_obj, &I_out_obj)) return NULL;
	sld2i = (GenI *)PyCapsule_GetPointer(gen_obj, "GenI");
	VECTOR(q_obj, q, n_q);
	VECTOR(I_out_obj, I_out, n_out);

	// Sanity check
	//if (n_q!=n_out) return Py_BuildValue("i",-1);

	genicom(sld2i, (int)n_q, q, I_out);
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
#define MODULE_NAME "_sld2i"
#define MODULE_INIT2 init_sld2i
#define MODULE_INIT3 PyInit__sld2i
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
