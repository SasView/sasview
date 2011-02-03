import wx
#import gui_manager
from sans.guiframe import gui_manager

# For py2exe, import config here
import local_config
import sys


# Application dimensions
APP_HEIGHT = 780
APP_WIDTH  = 850
PROG_SPLASH_SCREEN = "images/ball.png"

class PrApp(gui_manager.ViewApp):
    """
    """
    SIZE = (APP_WIDTH, APP_HEIGHT)
    TITLE = local_config.__appname__
    PROG_SPLASH_PATH = None
    STYLE = GUIFRAME.DEFAULT_STYLE
    
class PrView():
    """
    """
    def __init__(self):
        """
        """
        #from gui_manager import ViewApp
        #self.gui = gui_manager.ViewApp(0) 
        self.gui = PrApp(0)
        # Add perspectives to the basic application
        # Additional perspectives can still be loaded
        # dynamically
        import perspectives.pr as module
        self.pr_plug = module.Plugin(standalone=True)
        self.gui.add_perspective(self.pr_plug)
            
        # Build the GUI
        self.gui.build_gui()
        
        # Set the application manager for the GUI
        self.gui.set_manager(self)
        
        # Start the main loop
        self.gui.MainLoop()  
        

if __name__ == "__main__": 
    sansview = PrView()