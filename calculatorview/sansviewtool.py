
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
from sans.guiframe import gui_manager

# For py2exe, import config here
import local_config
import logging
import sys
class SansViewToolApp(gui_manager.ViewApp):
    """
    """
    
   
class SansViewTool():
    """
    """
    def __init__(self):
        """
        """
        #from gui_manager import ViewApp
        self.gui = SansViewToolApp(0) 
        # Set the application manager for the GUI
        self.gui.set_manager(self)
        # Add perspectives to the basic application
        # Additional perspectives can still be loaded
        # dynamically
        # Note: py2exe can't find dynamically loaded
        # modules. We load the fitting module here
        # to ensure a complete Windows executable build.
        
        
        #Calculator perspective   
        try:
            import sans.perspectives.calculator as module    
            calculator_plug = module.Plugin(standalone=True)
            self.gui.add_perspective(calculator_plug)
        except:
            logging.error("SansView: could not find Calculator plug-in module")
            logging.error(sys.exc_value)  

      
        # Build the GUI
        self.gui.build_gui()
        
        # Start the main loop
        self.gui.MainLoop() 
        

if __name__ == "__main__": 
    sansviewtool = SansViewTool()