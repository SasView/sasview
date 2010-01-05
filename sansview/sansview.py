"""
This software was developed by the University of Tennessee as part of the
Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
project funded by the US National Science Foundation. 

See the license text in license.txt

copyright 2009, University of Tennessee
"""
import wx
from sans.guiframe import gui_manager
from welcome_panel import WelcomePanel
# For py2exe, import config here
import local_config
import logging

# Application dimensions
APP_HEIGHT = 800
APP_WIDTH  = 1000

class SansViewApp(gui_manager.ViewApp):
    def OnInit(self):
        screen_size = wx.GetDisplaySize()
        app_height = APP_HEIGHT if screen_size[1]>APP_HEIGHT else screen_size[1]-50
        app_width  = APP_WIDTH if screen_size[0]>APP_WIDTH else screen_size[0]-50

        self.frame = gui_manager.ViewerFrame(None, -1, local_config.__appname__, 
                             window_height=app_height, window_width=app_width)    
        self.frame.Show(True)

        if hasattr(self.frame, 'special'):
            self.frame.special.SetCurrent()
        self.SetTopWindow(self.frame)
        return True

class SansView():
    
    def __init__(self):
        """
        
        """
        #from gui_manager import ViewApp
        self.gui = SansViewApp(0) 
        
        # Add perspectives to the basic application
        # Additional perspectives can still be loaded
        # dynamically
        # Note: py2exe can't find dynamically loaded
        # modules. We load the fitting module here
        # to ensure a complete Windows executable build.

        # P(r) perspective
        try:
            import sans.perspectives.pr as module    
            fitting_plug = module.Plugin(standalone=False)
            self.gui.add_perspective(fitting_plug)
        except:
            logging.error("SansView: could not find P(r) plug-in module") 
         
        #Calculator perspective   
        try:
            import sans.perspectives.calculator as module    
            calculator_plug = module.Plugin(standalone=False)
            self.gui.add_perspective(calculator_plug)
        except:
            logging.error("SansView: could not find Calculator plug-in module") 
            
        # theory perspective
        try:
            import sans.perspectives.theory as module    
            theory_plug = module.Plugin(standalone=False)
            self.gui.add_perspective(theory_plug)
        except:
            raise
            #logging.error("SansView: could not find theory plug-in module")
        # Fitting perspective
        import perspectives.fitting as module    
        fitting_plug = module.Plugin()
        self.gui.add_perspective(fitting_plug)
      
        # Add welcome page
        self.gui.set_welcome_panel(WelcomePanel)
      
        # Build the GUI
        self.gui.build_gui()
        
        # Set the application manager for the GUI
        self.gui.set_manager(self)
        
        # Start the main loop
        self.gui.MainLoop()  
        

if __name__ == "__main__": 
    sansview = SansView()