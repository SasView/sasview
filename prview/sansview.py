import wx
#import gui_manager
from sans.guiframe import gui_manager

# For py2exe, import config here
import local_config
from perspectives.pr.pr import NewPrFileEvent

# OS-dependent preferred height
#TODO: refactor this
_DEFAULT_HEIGHT=650
import sys
if sys.platform.count("darwin")>0:
	_DEFAULT_HEIGHT=720

class PrFrame(gui_manager.ViewerFrame):
    def _on_open(self, event):
        wx.PostEvent(self, NewPrFileEvent())

class PrApp(gui_manager.ViewApp):
    def OnInit(self):
        #from gui_manager import ViewerFrame
        self.frame = PrFrame(None, -1, local_config.__appname__, 
                             window_height=_DEFAULT_HEIGHT, window_width=850)    
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
        #self.gui = gui_manager.ViewApp(0) 
        self.gui = PrApp(0)
        
        # Add perspectives to the basic application
        # Additional perspectives can still be loaded
        # dynamically
        import perspectives.pr as module
        self.pr_plug = module.Plugin()
        self.gui.add_perspective(self.pr_plug)
            
        # Build the GUI
        self.gui.build_gui()
        
        # Set the application manager for the GUI
        self.gui.set_manager(self)
        
        # Start the main loop
        self.gui.MainLoop()  
        

if __name__ == "__main__": 
    sansview = SansView()