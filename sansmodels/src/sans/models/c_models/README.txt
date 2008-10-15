NOTE ABOUT THE SANS MODELS REFACTOR [Oct 14, 2008]

This is the new code to implement python extensions for our models.

- The major change here was to create model classes. Parameters
  are now class objects too, and polydispersity is now part of the
  parameter definition to speed up computations. See parameters.hh
  for more details, in particular the definitions of DispersionModel
  and Parameter.

- Some of the C code that was used to port the IGOR code is still used.
  For instance, the functions defined in cylinder.c is used in c_models/cylinder.cpp.

- The C++ class are intended to be easily compatible with McVine.
  
- The script c_models/WrapperGenerator.py is the script 
  that was used to generate the python C++ extensions for our models.
  For instance, CCylinderModel.cpp was created with WrapperGenerator.py run
  on c_extensions/cylinder.h.
 
- See c_extensions/README.txt for more details about the old c_models.

 
  