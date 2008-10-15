NOTE ABOUT THE SANS MODELS REFACTOR [Oct 14, 2008]

This is the code that was used to produce the first version of the
SANS models. This code should be refactored to eliminate all the code 
in c_extensions and merge it with the C++ code in c_models.

- Some of the C code that was used to port the IGOR code is still used.
  For instance, the functions defined in cylinder.c is used in c_models/cylinder.cpp.

- As of writing, the C functions are used in the McVine code to implement
  a simulated SANS instrument.
  
- The script c_extensions/WrapperGenerator.py is the original script 
  that was used to generate the python C extensions for our models.
  For instance, CCylinderModel.c was created with WrapperGenerator.py run
  on cylinder.h.
 
- See c_models/README.txt for more details about the new c_models.

 
  