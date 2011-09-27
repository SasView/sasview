"""
Console Module display Python console
"""
import wx.py.crust
import sys

if sys.platform.count("win32")>0:
    PANEL_WIDTH = 800
    PANEL_HEIGHT = 600
    FONT_VARIANT = 0
else:
    PANEL_WIDTH = 830
    PANEL_HEIGHT = 620
    FONT_VARIANT = 1
    
class PyConsole(wx.py.crust.CrustFrame):
    ## Internal nickname for the window, used by the AUI manager
    window_name = "Python Console"
    ## Name to appear on the window title bar
    window_caption = "Python Console"
    ## Flag to tell the AUI manager to put this panel in the center pane
    CENTER_PANE = False
    def __init__(self, parent=None, manager=None,
                    title='Python Console by PyCrust', 
                    size=(PANEL_WIDTH, PANEL_HEIGHT)):
        if parent != None:
            dataDir = parent._default_save_location
        wx.py.crust.CrustFrame.__init__(self, parent=parent, 
                                        title=title, size=size,
                                        dataDir=dataDir)
   
        self.parent = parent
        self._manager = manager
        self.Centre()

    def set_manager(self, manager):
        """
        Set the manager of this window
        """
        self._manager = manager
     
 
if __name__ == "__main__":
   
    app  = wx.App()
    dlg = PyConsole()
    dlg.Show()
    app.MainLoop()