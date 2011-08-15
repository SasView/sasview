
################################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation. 
#
#See the license text in license.txt
#
#copyright 2009, University of Tennessee
################################################################################

import wx
import os
import sys
# The below will make sure that sansview application uses the matplotlib font 
# bundled with sansview. 
if hasattr(sys, 'frozen'):
    mplconfigdir = os.path.join(sys.prefix, '.matplotlib')
    if not os.path.exists(mplconfigdir):
        os.mkdir(mplconfigdir)
    os.environ['MPLCONFIGDIR'] = mplconfigdir

from sans.guiframe import gui_manager
from sans.guiframe.gui_style import GUIFRAME
from welcome_panel import WelcomePanel
# For py2exe, import config here
import local_config
import logging


class SimViewApp(gui_manager.ViewApp):
    """
    """

class SimView():
    
    def __init__(self):
        """
            Initialize application
        """
        #from gui_manager import ViewApp
        self.gui = SimViewApp(0) 
        
        # Add perspectives to the basic application
        # Additional perspectives can still be loaded
        # dynamically
        # Note: py2exe can't find dynamically loaded
        # modules. We load the fitting module here
        # to ensure a complete Windows executable build.

        # Simulation perspective
        import sans.perspectives.simulation as module    
        self.gui.add_perspective(module.Plugin())
      
        # Build the GUI
        self.gui.build_gui()
        
        # Set the application manager for the GUI
        self.gui.set_manager(self)
        
        # Start the main loop
        self.gui.MainLoop()  

if __name__ == "__main__": 
    sansview = SimView()