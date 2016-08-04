#include <Python.h>
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
    const int frame;
    const int n_pixels;
    const int n_rasters;
    if (self != NULL) {
        if (!PyArg_ParseTuple(args, "siii", &filename, &frame, &n_pixels, &n_rasters))
            Py_RETURN_NONE;
        if (!(self->params.filename = malloc(strlen(filename) + 1)))
            Py_RETURN_NONE;
        strcpy(self->params.filename, filename);
        self->params.n_pixels = n_pixels;
        self->params.n_rasters = n_rasters;
    }

    return 0;
}

static void CLoader_dealloc(CLoader *self) {
    free(self->params.filename);
    self->ob_type->tp_free((PyObject *)self);
}

static PyObject *to_string(CLoader *self, PyObject *params) {
    char str[100];
    sprintf(str,
        "Filename: %s\nframe: %d\nn_pixels: %d\nn_rasters: %d\n",
        self->params.filename,
        self->params.frame,
        self->params.n_pixels,
        self->params.n_rasters);
    return Py_BuildValue("s", str);
}

static PyObject *get_filename(CLoader *self, PyObject *args) {
    return Py_BuildValue("s", self->params.filename);
}

static PyObject *get_frame(CLoader *self, PyObject *args) {
    return Py_BuildValue("i", self->params.frame);
}

static PyObject *get_n_pixels(CLoader *self, PyObject *args) {
    return Py_BuildValue("i", self->params.n_pixels);
}

static PyObject *get_n_rasters(CLoader *self, PyObject *args) {
    return Py_BuildValue("i", self->params.n_rasters);
}

static PyObject *load_data(CLoader *self, PyObject *args) {
    int raster;
    int pixel;
    int frame_pos;
    int size[2] = {self->params.n_rasters, self->params.n_pixels};
    float cur_val;
    PyObject *read_val;
    FILE *input_file;
    PyArrayObject *data;

    printf("load_data called\n");

    if (!PyArg_ParseTuple(args, "O!", &PyArray_Type, &data)) {
        printf("Failed parsing PyArray object");
        return NULL;
    }

    input_file = fopen(self->params.filename, "rb");
    if (!input_file) {
        printf("Failed opening file\n");
        return NULL;
    }

    printf("Calculating frame_pos\n");
    frame_pos = self->params.n_pixels * self->params.n_rasters * self->params.frame;
    printf("frame_pos: %d\n", frame_pos);
    fseek(input_file, frame_pos*sizeof(float), SEEK_SET);
    printf("fseek completed\n");

    for (raster = 0; raster < self->params.n_rasters; raster++) {
        for (pixel = 0; pixel < self->params.n_pixels; pixel++) {
            fread(&cur_val, sizeof(float), 1, input_file);
            PyArray_SETITEM(data, PyArray_GETPTR2(data, raster, pixel), PyFloat_FromDouble(cur_val));
            read_val = PyArray_GETITEM(data, PyArray_GETPTR2(data, raster, pixel));
        }
    }
    printf("Data read.\n");

    fclose(input_file);
    printf("File closed\n");
    Py_DECREF(data);
    printf("Function completed\n");
    return Py_BuildValue("O", data);
}

static PyMethodDef CLoader_methods[] = {
    { "to_string", (PyCFunction)to_string, METH_VARARGS, "Print the objects params" },
    { "get_filename", (PyCFunction)get_filename, METH_VARARGS, "Get the filename" },
    { "get_frame", (PyCFunction)get_frame, METH_VARARGS, "Get the frame that will be loaded" },
    { "get_n_pixels", (PyCFunction)get_n_pixels, METH_VARARGS, "Get n_pixels" },
    { "get_n_rasters", (PyCFunction)get_n_rasters, METH_VARARGS, "Get n_rasters" },
    { "load_data", (PyCFunction)load_data, METH_VARARGS, "Load the data into a numpy array" },
    {NULL}
};

static PyMemberDef CLoader_members[] = {
    {NULL}
};

static PyTypeObject CLoaderType = {
    PyObject_HEAD_INIT(NULL)
    0,                         /*ob_size*/
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

PyMODINIT_FUNC
initbsl_loader(void)
{
    PyObject *module;
    module = Py_InitModule("bsl_loader", NULL);
    import_array();

    if (PyType_Ready(&CLoaderType) < 0)
        return;

    Py_INCREF(&CLoaderType);
    PyModule_AddObject(module, "CLoader", (PyObject *)&CLoaderType);
}
