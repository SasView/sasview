import wx
#import gui_manager
from sans.guiframe import gui_manager

# For py2exe, import config here
import local_config


class SansView():
    
    def __init__(self):
        """
        
        """
        #from gui_manager import ViewApp
        self.gui = gui_manager.ViewApp(0) 
        
        # Add perspectives to the basic application
        # Additional perspectives can still be loaded
        # dynamically
        # Note: py2exe can't find dynamically loaded
        # modules. We load the fitting module here
        # to ensure a complete Windows executable build.
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