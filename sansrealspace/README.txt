################################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation. 
#
#See the license text in license.txt
#
#copyright 2008, University of Tennessee
################################################################################


How-to build an application using guiframe:

1- Write a main application script along the lines of dummyapp.py
2- Write a config script along the lines of config.py, and 
    name it local_config.py
3- Write your plug-ins and place them in a directory called "perspectives".
    - Look at local_perspectives/plotting for an example of a plug-in.
    - A plug-in should define a class named Plugin,
    	 inheriting from PluginBase in plugin_base.py
    
4- each panel used in guiframe must inheritation from PanelBase in panel_base.py

Sansrealspace contains the VolumeCanvas module. This module creates a 
simulation canvas for real-space simulation of SANS scattering intensity.
The user can create an arrangement of basic shapes and estimate I(q) and
I(q_x, q_y). Error estimates on the simulation are also available. 