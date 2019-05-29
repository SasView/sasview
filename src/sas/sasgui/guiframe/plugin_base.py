"""
Defines the interface for a Plugin class that can be used by the gui_manager.
"""

################################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation.
#
#See the license text in license.txt
#
#copyright 2008, University of Tennessee
################################################################################

class PluginBase(object):
    """
    This class defines the interface for a Plugin class
    that can be used by the gui_manager.

    Plug-ins should be placed in a sub-directory called "perspectives".
    For example, a plug-in called Foo should be place in "perspectives/Foo".
    That directory contains at least two files:

    1. perspectives/Foo/__init__.py contains two lines: ::

        PLUGIN_ID = "Foo plug-in 1.0"
        from Foo import *

    2. perspectives/Foo/Foo.py contains the definition of the Plugin
       class for the Foo plug-in. The interface of that Plugin class
       should follow the interface of the class you are looking at.

    See dummyapp.py for a plugin example.
    """

    def __init__(self, name="Test_plugin"):
        """
        Abstract class for gui_manager Plugins.
        """
        # Define if the plugin is local to Viewerframe  and always active
        self._always_active = False
        ## Plug-in name. It will appear on the application menu.
        self.sub_menu = name
        ## Reference to the parent window. Filled by get_panels() below.
        self.parent = None
        self.frame = None
        #plugin state reader
        self.state_reader = None
        self._extensions = ''
        ## List of panels that you would like to open in AUI windows
        #  for your plug-in. This defines your plug-in "perspective"
        self.perspective = []
        #flag to tell the current plugin that aaplication is in batch mode
        self.batch_on = False
        #properties for color and ID of a specific plugin..
        self.color = None
        self.id = -1
        self.batch_capable = self.get_batch_capable()

    def get_batch_capable(self):
        """
        Check if the plugin has a batch capability
        """
        return False

    def add_color(self, color, id):
        """
        Adds color to a plugin
        """

    def clear_panel(self):
        """
        clear all related panels
        """

    def get_extensions(self):
        """
        return state reader and its extensions
        """
        return self.state_reader, self._extensions

    def can_load_data(self):
        """
        if return True, then call handler to laod data
        """
        return False

    def use_data(self):
        """
        return True if these plugin use data
        """
        return True

    def is_in_use(self, data_id):
        """
        get a  data id a list of data name if data data is
         currently used by the plugin and the name of the plugin

        data_name = 'None'
        in_use = False
        example [(data_name, self.sub_menu)]
        """
        return []

    def delete_data(self, data_id):
        """
        Delete all references of data which id are in data_list. 
        """

    def load_data(self, event):
        """
        Load  data
        """
        raise NotImplementedError

    def load_folder(self, event):
        """
        Load entire folder
        """
        raise NotImplementedError

    def set_is_active(self, active=False):
        """
        Set if the perspective is always active
        """
        self._always_active = active

    def is_always_active(self):
        """
        return True is this plugin is always active and it is local to guiframe
        even if the user is switching between perspectives
        """
        return self._always_active

    def populate_file_menu(self):
        """
        Append menu item under file menu item of the frame
        """
        return []

    def populate_menu(self, parent):
        """
        Create and return the list of application menu
        items for the plug-in. 

        :param parent: parent window

        :return: plug-in menu

        """
        return []

    def get_frame(self):
        """
        Returns MDIChildFrame
        """
        return self.frame

    def _frame_set_helper(self):
        """
        Sets default frame config
        """
        if self.frame is not None:
            self.frame.EnableCloseButton(False)
            self.frame.Show(False)

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

        # Return the list of panels
        return []

    def get_tools(self):
        """
        Returns a set of menu entries for tools
        """
        return []

    def get_context_menu(self, plotpanel=None):
        """
        This method is optional.

        When the context menu of a plot is rendered, the
        get_context_menu method will be called to give you a
        chance to add a menu item to the context menu.

        A ref to a plotpanel object is passed so that you can
        investigate the plot content and decide whether you
        need to add items to the context menu.

        This method returns a list of menu items.
        Each item is itself a list defining the text to
        appear in the menu, a tool-tip help text, and a
        call-back method.

        :param graph: the Graph object to which we attach the context menu

        :return: a list of menu items with call-back function
        """
        return []

    def get_perspective(self):
        """
        Get the list of panel names for this perspective
        """
        return self.perspective

    def on_perspective(self, event=None):
        """
        Call back function for the perspective menu item.
        We notify the parent window that the perspective
        has changed.

        :param event: menu event
        """
        old_frame = None
        old_persp = self.parent.get_current_perspective()
        if old_persp is not None:
            old_frame = old_persp.get_frame()
        self.parent.check_multimode(self)
        self.parent.set_current_perspective(self)
        self.parent.set_perspective(self.perspective)

        if self.frame is not None:
            if old_frame is not None:
                pos_x, pos_y = old_frame.GetPositionTuple()
                self.frame.SetPosition((pos_x, pos_y))
            if not self.frame.IsShown():
                self.frame.Show(True)

    def set_batch_selection(self, flag):
        """
        the plugin to its batch state if flag is True
        """
        self.batch_on = flag
        self.on_batch_selection(self.batch_on)

    def on_batch_selection(self, flag):
        """
        need to be overwritten by the derivated class
        """
    
    def post_init(self):
        """
        Post initialization call back to close the loose ends
        """
        pass

    def set_state(self, state=None, datainfo=None):    
        """
        update state
        """

    def set_data(self, data_list=None):
        """
        receive a list of data and use it in the current perspective
        """

    def set_theory(self, theory_list=None):
        """
        :param theory_list: list of information
            related to available theory state
        """
        msg = "%s plugin: does not support import theory" % str(self.sub_menu)
        raise (ValueError, msg)

    def on_set_state_helper(self, event):
        """
        update state
        """

