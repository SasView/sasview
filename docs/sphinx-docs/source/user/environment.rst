.. _Environment_Variables:

Environment Variables
======================

SasView creates and uses a number of environment variables:

- **SAS_MODELPATH=path**
   - sets the directory containing custom models

- **SAS_DLL_PATH=path**
   - sets the path to the compiled modules
   
- **SAS_WEIGHTS_PATH=~/.sasview/weights**
   - sets the path to custom distribution files (see :ref:`polydispersityhelp`)

- **XDG_CACHE_HOME=~/.cache**
   - sets the pyopencl cache root (linux only)
   - defined in the appdirs package

- **SAS_COMPILER=tinycc|msvc|mingw|unix**
   - sets the DLL compiler

- **SAS_OPENCL=vendor:device|none**
   - sets the target OpenCL device for GPU computations
   - use *none* to disable

- **SAS_OPENMP=1|0**
   - turns on/off OpenMP multi-processing of the DLLs

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

*Document History*

| 2018-07-20 Steve King

