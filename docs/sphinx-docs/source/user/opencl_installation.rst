.. _opencl-installation:

*******************
OpenCL Installation
*******************

1. Check if you have OpenCL already installed
=============================================

Windows
=========
    The following instructions are based on
    http://web.engr.oregonstate.edu/~mjb/cs475/DoIHaveOpenCL.pdf

    * Go to: Start -> Control Panel -> Administrative Tools
    * Double Click on Computer Managment
    * Click on Device Manager
    * Click open Display Adapters
    * Right-click on available adapter and select Properties
    * Click on Driver
    * Go to Driver Details
    * Scroll down and see if OpenCL is installed (look for OpenCL*.dll files)

Mac OSX
=========
    For OSXs higher than 10.6 OpenCL is shipped along with the system.


2. Installation
===============

Windows
=========
    Depeneding on the graphic card on your system, drivers
    can be obtained from different sources:

    * Nvidia: https://developer.nvidia.com/opencl
    * AMD: http://developer.amd.com/tools-and-sdks/opencl-zone/

Mac OSX
=========
    N/A


.. note::
    Note that Intel provides an OpenCL drivers for Intel processors:
    https://software.intel.com/en-us/articles/opencl-drivers
    This can sometimes make use of special vector instructions across multiple
    processors, so it is worth installing if the GPU does not support double
    precision. You can install this driver alongside the GPU driver for NVIDIA
    or AMD.
