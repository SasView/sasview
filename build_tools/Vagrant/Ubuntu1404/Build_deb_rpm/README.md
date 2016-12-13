Build tools for Debian and RPM
------------------------------

How-to  build SasView Debian and RPM packages on Ubuntu using Anaconda
  
  - Set up conda environment using the environment.yml file
  - Use pyopencl from conda 
  - Do not use pyopencl from pip - this will cause pyinstaller to fail finding pyopencl 
  - Copy CMakelist.txt to the sasview/build_tools folder


Known Issues:
-------------
  - pyopencl from conda is not the newest version
  - To bypass one could build new pyopencl package based on the pip pyopencl package 
  - Windows, OSX, Linux all have different versions of pyopencl available  on conda  


