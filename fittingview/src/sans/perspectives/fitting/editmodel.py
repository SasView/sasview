"""
Console Module display Python console
"""
import sys
import wx
import wx.py.editor as editor
if sys.platform.count("win32")>0:
    PANEL_WIDTH = 800
    PANEL_HEIGHT = 600
    FONT_VARIANT = 0
else:
    PANEL_WIDTH = 830
    PANEL_HEIGHT = 620
    FONT_VARIANT = 1
    
class PyConsole(editor.EditorFrame):
    ## Internal nickname for the window, used by the AUI manager
    window_name = "Custom Model Editor"
    ## Name to appear on the window title bar
    window_caption = "Custom Model Editor"
    ## Flag to tell the AUI manager to put this panel in the center pane
    CENTER_PANE = False
    def __init__(self, parent=None, manager=None,
                    title='Custom Model Editor', filename=None,
                    size=(PANEL_WIDTH, PANEL_HEIGHT)):
        self.config = None
        editor.EditorFrame.__init__(self, parent=parent, 
                                        title=title, size=size,
                                        filename=filename)
        self.parent = parent
        self._manager = manager
        self.Centre()

    def set_manager(self, manager):
        """
        Set the manager of this window
        """
        self._manager = manager
        
    def OnAbout(self, event):
        """
        On About
        """
        message = ABOUT
        dial = wx.MessageDialog(self, message, 'About',
                           wx.OK|wx.ICON_INFORMATION)  
        dial.ShowModal()
             
ABOUT =  "Welcome to Python %s! \n\n"% sys.version.split()[0]
ABOUT += "This uses Py Editor in wx (developed by Patrick K. O'Brien).\n"
ABOUT += "If this is your first time using Python, \n"
ABOUT += "you should definitely check out the tutorial "
ABOUT += "on the Internet at http://www.python.org/doc/tut/."
 
        
if __name__ == "__main__":
   
    app  = wx.App()
    dlg = PyConsole()
    dlg.Show()
    app.MainLoop()