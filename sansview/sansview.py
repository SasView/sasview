import wx
#import gui_manager
from sans.guiframe import gui_manager

# For py2exe, import config here
import local_config
import logging

# Application dimensions
APP_HEIGHT = 800
APP_WIDTH  = 1000

class SansViewApp(gui_manager.ViewApp):
    def OnInit(self):
        #from gui_manager import ViewerFrame
        self.frame = gui_manager.ViewerFrame(None, -1, local_config.__appname__, 
                             window_height=APP_HEIGHT, window_width=APP_WIDTH)    
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

        # Fitting perspective
        import perspectives.fitting as module    
        fitting_plug = module.Plugin()
        self.gui.add_perspective(fitting_plug)
      
        # Build the GUI
        self.gui.build_gui()
        
        # Set the application manager for the GUI
        self.gui.set_manager(self)
        
        # Start the main loop
        self.gui.MainLoop()  
        

if __name__ == "__main__": 
    sansview = SansView()