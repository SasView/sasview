"""
Dummy application.
Allows the user to set an external data manager
"""
import sas.guiframe.gui_manager as gui_manager

from sas.guiframe.plugin_base import PluginBase

class DummyView(gui_manager.ViewApp):
    """
    """
    
class TestPlugin(PluginBase):
    
    def populate_menu(self, parent):
        """
        Create and return the list of application menu
        items for the plug-in. 
        :param parent: parent window
        
        :return: plug-in menu
        
        """
        import wx
        # Create a menu
        plug_menu = wx.Menu()

        # Always get event IDs from wx
        id = wx.NewId()
        
        # Fill your menu
        plug_menu.Append(id, '&Do something')
        def _on_do_something(event):
            print "Do something"
        wx.EVT_MENU(self.parent, id, _on_do_something)
    
        # Returns the menu and a name for it.
        return [(plug_menu, "DummyApp")]    
    
    def get_panels(self, parent):
        """
        Create and return the list of wx.Panels for your plug-in.
        Define the plug-in perspective.
        
        Panels should inherit from DefaultPanel defined below,
        or should present the same interface. They must define
        "window_caption" and "window_name".
        
        :param parent: parent window
        
        :return: list of panels
        
        """
        ## Save a reference to the parent
        self.parent = parent
        
        # Define a panel
        defaultpanel = gui_manager.DefaultPanel(self.parent, -1)
        defaultpanel.window_name = "Test"
        
        # If needed, add its name to the perspective list
        self.perspective = [defaultpanel.window_name]

        # Return the list of panels
        return [defaultpanel]
    
    def get_tools(self):
        """
        Returns a set of menu entries for tools
        """
        def _test_dialog(event):
            import wx
            frame = wx.Dialog(None, -1, 'Test Tool')    
            frame.Show(True)
        return [["Tool 1", "This is an example tool", _test_dialog],
                ["Tool 2", "This is another example tool", _test_dialog]]

    def get_context_menu(self, graph=None):
        """
        This method is optional.
    
        When the context menu of a plot is rendered, the 
        get_context_menu method will be called to give you a 
        chance to add a menu item to the context menu.
        
        A ref to a Graph object is passed so that you can
        investigate the plot content and decide whether you
        need to add items to the context menu.  
        
        This method returns a list of menu items.
        Each item is itself a list defining the text to 
        appear in the menu, a tool-tip help text, and a
        call-back method.
        
        :param graph: the Graph object to which we attach the context menu
        
        :return: a list of menu items with call-back function
        """
        return [["Menu text", 
                 "Tool-tip help text", 
                 "self._on_context_do_something"]]   

class SansView():
    
    def __init__(self):
        """
        Initialization
        """
        self.gui = DummyView(0)
        
        fitting_plug = TestPlugin()
        self.gui.add_perspective(fitting_plug)
        
        # Build the GUI
        self.gui.build_gui()
        
        # Set the application manager for the GUI
        self.gui.set_manager(self)
        
        # Start the main loop
        self.gui.MainLoop()  

if __name__ == "__main__": 
    from multiprocessing import freeze_support
    freeze_support()
    sansview = SansView()
