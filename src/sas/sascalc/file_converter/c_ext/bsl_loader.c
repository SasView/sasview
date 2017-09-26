#include <Python.h>
#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <numpy/arrayobject.h>
#include <stdio.h>
#include <stdlib.h>
#include "structmember.h"
#include "bsl_loader.h"

typedef struct {
    PyObject_HEAD
    CLoader_params params;
} CLoader;

static PyObject *CLoader_new(PyTypeObject *type, PyObject *args, PyObject *kwds) {
    CLoader *self;

    self = (CLoader *)type->tp_alloc(type, 0);

    return (PyObject *)self;
}

static PyObject *CLoader_init(CLoader *self, PyObject *args, PyObject *kwds) {
    const char *filename;
    int n_frames;
    int n_pixels;
    int n_rasters;
    int swap_bytes;

    if (self != NULL) {
        if (!PyArg_ParseTuple(args, "siiii", &filename, &n_frames, &n_pixels, &n_rasters, &swap_bytes))
            Py_RETURN_NONE;
        if (!(self->params.filename = malloc(strlen(filename) + 1)))
            Py_RETURN_NONE;
        strcpy(self->params.filename, filename);
        self->params.n_frames = n_frames;
        self->params.n_pixels = n_pixels;
        self->params.n_rasters = n_rasters;
        self->params.swap_bytes = swap_bytes;
    }

    return 0;
}

static void CLoader_dealloc(CLoader *self) {
    free(self->params.filename);
    Py_TYPE(self)->tp_free((PyObject *)self);
}

static PyObject *to_string(CLoader *self, PyObject *params) {
    char str[100];
    sprintf(str,
        "Filename: %s\nn_frames: %d\nframe: %d\nn_pixels: %d\nn_rasters: %d\nswap_bytes: %d",
        self->params.filename,
        self->params.n_frames,
        self->params.frame,
        self->params.n_pixels,
        self->params.n_rasters,
        self->params.swap_bytes);
    return Py_BuildValue("s", str);
}

/*                    ----- Setters and Getters -----                        */

static PyObject *get_filename(CLoader *self, PyObject *args) {
    return Py_BuildValue("s", self->params.filename);
}

static PyObject *set_filename(CLoader *self, PyObject *args) {
    const char *new_filename;
    if (!PyArg_ParseTuple(args, "s", &new_filename))
        return NULL;
    strcpy(self->params.filename, new_filename);

    return Py_BuildValue("s", self->params.filename);
}

static PyObject *get_n_frames(CLoader *self, PyObject *args) {
    return Py_BuildValue("i", self->params.n_frames);
}

static PyObject *set_n_frames(CLoader *self, PyObject *args) {
    int new_frames;
    if (!PyArg_ParseTuple(args, "i", &new_frames))
        return NULL;
    self->params.n_frames = new_frames;

    return Py_BuildValue("i", self->params.n_frames);
}

static PyObject *get_frame(CLoader *self, PyObject *args) {
    return Py_BuildValue("i", self->params.frame);
}

static PyObject *set_frame(CLoader *self, PyObject *args) {
    int new_frame;
    if (!PyArg_ParseTuple(args, "i", &new_frame))
        return NULL;
    self->params.frame = new_frame;

    return Py_BuildValue("i", self->params.frame);
}

static PyObject *get_n_pixels(CLoader *self, PyObject *args) {
    return Py_BuildValue("i", self->params.n_pixels);
}

static PyObject *set_n_pixels(CLoader *self, PyObject *args) {
    int new_pixels;
    if (!PyArg_ParseTuple(args, "i", &new_pixels))
        return NULL;
    self->params.n_pixels = new_pixels;

    return Py_BuildValue("i", self->params.n_pixels);
}

static PyObject *get_n_rasters(CLoader *self, PyObject *args) {
    return Py_BuildValue("i", self->params.n_rasters);
}

static PyObject *set_n_rasters(CLoader *self, PyObject *args) {
    int new_rasters;
    if (!PyArg_ParseTuple(args, "i", &new_rasters))
        return NULL;
    self->params.n_rasters = new_rasters;

    return Py_BuildValue("i", self->params.n_rasters);
}

static PyObject *get_swap_bytes(CLoader *self, PyObject *args) {
    return Py_BuildValue("i", self->params.swap_bytes);
}

static PyObject *set_swap_bytes(CLoader *self, PyObject *args) {
    int new_swap;
    if (!PyArg_ParseTuple(args, "i", &new_swap))
        return NULL;
    self->params.swap_bytes = new_swap;

    return Py_BuildValue("i", self->params.swap_bytes);
}

/*                        ----- Instance Methods -----                       */

float reverse_float(const float in_float) {
    // Reverse the order of the bytes of a float
    float retval;
    char *to_convert = (char *)&in_float;
    char *return_float = (char *)&retval;

    return_float[0] = to_convert[3];
    return_float[1] = to_convert[2];
    return_float[2] = to_convert[1];
    return_float[3] = to_convert[0];

    return retval;
}

static PyObject *load_data(CLoader *self, PyObject *args) {
    int raster;
    int pixel;
    int frame_pos;
    npy_intp size[2] = {self->params.n_rasters, self->params.n_pixels};
    float cur_val;
    FILE *input_file;
    PyArrayObject *data;

    // Create a new numpy array to store the data in
    data = (PyArrayObject *)PyArray_SimpleNew(2, size, NPY_FLOAT);

    // Attempt to open the file specified
    input_file = fopen(self->params.filename, "rb");
    if (!input_file) {
        // BSL filenames are 10 characters long
        // Filename validity checked in bsl_loader.py
        size_t filename_start = strlen(self->params.filename) - 10;
        char *filename = self->params.filename + filename_start;
        char *err_msg = (char *)malloc(sizeof(char) * 32);

        sprintf(err_msg, "Unable to open file: %s", filename);

        PyErr_SetString(PyExc_RuntimeError, err_msg);
        free(err_msg);
        return NULL;
    }

    // Move the file cursor the the position where the data we're interested
    // in begins
    frame_pos = self->params.n_pixels * self->params.n_rasters * self->params.frame;
    fseek(input_file, frame_pos*sizeof(float), SEEK_SET);

    for (raster = 0; raster < self->params.n_rasters; raster++) {
        for (pixel = 0; pixel < self->params.n_pixels; pixel++) {
            // Try reading the file
            if (fread(&cur_val, sizeof(float), 1, input_file) == 0) {
                PyErr_SetString(PyExc_RuntimeError, "Error reading file or EOF reached.");
                return NULL;
            }

            // Swap the order of the bytes read, if specified that we should do
            // so in the header file
            if (self->params.swap_bytes == 0)
                cur_val = reverse_float(cur_val);

            // Add the read value to the numpy array
            PyArray_SETITEM(data, PyArray_GETPTR2(data, raster, pixel), PyFloat_FromDouble(cur_val));
        }
    }

    fclose(input_file);

    return Py_BuildValue("N", data);
}

/*                           ----- Class Registration -----                  */

static PyMethodDef CLoader_methods[] = {
    { "to_string", (PyCFunction)to_string, METH_VARARGS, "Print the objects params" },
    { "get_filename", (PyCFunction)get_filename, METH_VARARGS, "Get the filename" },
    { "set_filename", (PyCFunction)set_filename, METH_VARARGS, "Set the filename" },
    { "get_n_frames", (PyCFunction)get_n_frames, METH_VARARGS, "Get n_frames" },
    { "set_n_frames", (PyCFunction)set_n_frames, METH_VARARGS, "Set n_frames" },
    { "get_frame", (PyCFunction)get_frame, METH_VARARGS, "Get the frame that will be loaded" },
    { "set_frame", (PyCFunction)set_frame, METH_VARARGS, "Set the frame that will be loaded" },
    { "get_n_pixels", (PyCFunction)get_n_pixels, METH_VARARGS, "Get n_pixels" },
    { "set_n_pixels", (PyCFunction)set_n_pixels, METH_VARARGS, "Set n_pixels" },
    { "get_n_rasters", (PyCFunction)get_n_rasters, METH_VARARGS, "Get n_rasters" },
    { "set_n_rasters", (PyCFunction)set_n_rasters, METH_VARARGS, "Set n_rasters" },
    { "get_swap_bytes", (PyCFunction)get_swap_bytes, METH_VARARGS, "Get swap_bytes" },
    { "set_swap_bytes", (PyCFunction)set_swap_bytes, METH_VARARGS, "Set swap_bytes" },
    { "load_data", (PyCFunction)load_data, METH_VARARGS, "Load the data into a numpy array" },
    {NULL}
};

static PyMemberDef CLoader_members[] = {
    {NULL}
};

static PyTypeObject CLoaderType = {
    //PyObject_HEAD_INIT(NULL)
    //0,                         /*ob_size*/
    PyVarObject_HEAD_INIT(NULL, 0)
    "CLoader",             /*tp_name*/
    sizeof(CLoader),             /*tp_basicsize*/
    0,                         /*tp_itemsize*/
    (destructor)CLoader_dealloc, /*tp_dealloc*/
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
    "CLoader objects",           /* tp_doc */
    0,		               /* tp_traverse */
    0,		               /* tp_clear */
    0,		               /* tp_richcompare */
    0,		               /* tp_weaklistoffset */
    0,		               /* tp_iter */
    0,		               /* tp_iternext */
    CLoader_methods,             /* tp_methods */
    CLoader_members,             /* tp_members */
    0,                         /* tp_getset */
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    (initproc)CLoader_init,      /* tp_init */
    0,                         /* tp_alloc */
    CLoader_new,                 /* tp_new */
};

/**
 * Function used to add the model class to a module
 * @param module: module to add the class to
 */
void addCLoader(PyObject *module)
{
    if (PyType_Ready(&CLoaderType) < 0)
        return;
    Py_INCREF(&CLoaderType);
    PyModule_AddObject(module, "CLoader", (PyObject *)&CLoaderType);
}

#define MODULE_DOC "C module for loading bsl."
#define MODULE_NAME "bsl_loader"
#define MODULE_INIT2 initbsl_loader
#define MODULE_INIT3 PyInit_bsl_loader
#define MODULE_METHODS module_methods

/* ==== boilerplate python 2/3 interface bootstrap ==== */


#if defined(WIN32) && !defined(__MINGW32__)
    #define DLL_EXPORT __declspec(dllexport)
#else
    #define DLL_EXPORT
#endif

#if PY_MAJOR_VERSION >= 3

  static PyMethodDef module_methods[] = {
      {NULL}
  };

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
    import_array();
    addCLoader(m);
    return m;
  }

#else /* !PY_MAJOR_VERSION >= 3 */

  DLL_EXPORT PyMODINIT_FUNC MODULE_INIT2(void)
  {
    PyObject* m = Py_InitModule(MODULE_NAME, NULL);
    import_array();
    addCLoader(m);
  }

#endif /* !PY_MAJOR_VERSION >= 3 */