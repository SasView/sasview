
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


class SansViewApp(gui_manager.ViewApp):
    """
    """
  

class SansView():
    """
    """
    def __init__(self):
        """
        """
        #from gui_manager import ViewApp
        self.gui = SansViewApp(0) 
        # Set the application manager for the GUI
        self.gui.set_manager(self)
        # Add perspectives to the basic application
        # Additional perspectives can still be loaded
        # dynamically
        # Note: py2exe can't find dynamically loaded
        # modules. We load the fitting module here
        # to ensure a complete Windows executable build.
        
        # Fitting perspective
        try:
            import sans.perspectives.fitting as module    
            fitting_plug = module.Plugin()
            self.gui.add_perspective(fitting_plug)
        except:
            logging.error("SansView: could not find Fitting plug-in module")
            logging.error(sys.exc_value)  
            
        # P(r) perspective
        try:
            import sans.perspectives.pr as module    
            pr_plug = module.Plugin(standalone=False)
            self.gui.add_perspective(pr_plug)
        except:
            raise
            logging.error("SansView: could not find P(r) plug-in module") 
            logging.error(sys.exc_value)  
        
        #Invariant perspective
        try:
            import sans.perspectives.invariant as module    
            invariant_plug = module.Plugin(standalone=False)
            self.gui.add_perspective(invariant_plug)
        except:
            raise
            logging.error("SansView: could not find Invariant plug-in module") 
            logging.error(sys.exc_value)  
        
        #Calculator perspective   
        try:
            import sans.perspectives.calculator as module    
            calculator_plug = module.Plugin(standalone=False)
            self.gui.add_perspective(calculator_plug)
        except:
            logging.error("SansView: could not find Calculator plug-in module")
            logging.error(sys.exc_value)  

            
        # Add welcome page
        self.gui.set_welcome_panel(WelcomePanel)
      
        # Build the GUI
        self.gui.build_gui()
        
        # Start the main loop
        self.gui.MainLoop()  
       

if __name__ == "__main__": 
    sansview = SansView()