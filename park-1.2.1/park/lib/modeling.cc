/* This program is public domain. */
#include <cstdio> // CRUFT: mingw-xy bug requires FILENAME_MAX for wchar.h to import
#include <iostream>
#include <iomanip>
#include <Python.h>

extern "C" void
resolution(int Nin, const double Qin[], const double Rin[],
           int N, const double Q[], const double dQ[], double R[]);

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

PyObject* Pconvolve(PyObject *obj, PyObject *args)
{
  PyObject *Qi_obj,*Ri_obj,*Q_obj,*dQ_obj,*R_obj;
  const double *Qi, *Ri, *Q, *dQ;
  double *R;
  Py_ssize_t nQi, nRi, nQ, ndQ, nR;
  
  if (!PyArg_ParseTuple(args, "OOOOO:resolution", 
                        &Qi_obj,&Ri_obj,&Q_obj,&dQ_obj,&R_obj)) return NULL;
  INVECTOR(Qi_obj,Qi,nQi);
  INVECTOR(Ri_obj,Ri,nRi);
  INVECTOR(Q_obj,Q,nQ);
  INVECTOR(dQ_obj,dQ,ndQ);
  OUTVECTOR(R_obj,R,nR);
  if (nQi != nRi) {
#ifndef BROKEN_EXCEPTIONS
    PyErr_SetString(PyExc_ValueError, "_librefl.convolve: Qi and Ri have different lengths");
#endif
    return NULL;
  }
  if (nQ != ndQ || nQ != nR) {
#ifndef BROKEN_EXCEPTIONS
    PyErr_SetString(PyExc_ValueError, "_librefl.convolve: Q, dQ and R have different lengths");
#endif
    return NULL;
  }
  resolution(nQi,Qi,Ri,nQ,Q,dQ,R);
  return Py_BuildValue("");
}

static PyMethodDef methods[] = {
   {"convolve",
    Pconvolve,
    METH_VARARGS,
    "convolve(Qi,Ri,Q,dQ,R): compute convolution of width dQ[k] at points Q[k], returned in R[k]"},
    {0}
} ;


#if defined(WIN32) && !defined(__MINGW32__)
__declspec(dllexport)
#endif

	
extern "C" void init_modeling(void) {
  Py_InitModule4("_modeling",
  		methods,
		"Modeling C Library",
		0,
		PYTHON_API_VERSION
		);
}
