import wx
#import gui_manager
from sans.guiframe import gui_manager

# For py2exe, import config here
import local_config
import sys


# Application dimensions
APP_HEIGHT = 780
APP_WIDTH  = 850

class PrFrame(gui_manager.ViewerFrame):
    """
    """
    def _on_open(self, event):
        """
        """
        pass


class PrApp(gui_manager.ViewApp):
    """
    """
    def OnInit(self):
        """
        """
        # Check the size of the screen
        # Add some padding to make sure to clear any OS tool bar
        screen_size = wx.GetDisplaySize()
        app_height = APP_HEIGHT if screen_size[1]>APP_HEIGHT else screen_size[1]-50
        app_width  = APP_WIDTH if screen_size[0]>APP_WIDTH else screen_size[0]-50
        
        self.frame = PrFrame(None, -1, local_config.__appname__, 
                             window_height=app_height, window_width=app_width)    
        self.frame.Show(True)

        if hasattr(self.frame, 'special'):
            self.frame.special.SetCurrent()
        self.SetTopWindow(self.frame)
        return True
    
class SansView():
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
    sansview = SansView()