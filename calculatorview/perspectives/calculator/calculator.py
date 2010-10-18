
################################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation. 
#
#See the license text in license.txt
#
#copyright 2010, University of Tennessee
################################################################################

import wx
import logging

class Plugin:
    """
    This class defines the interface for a Plugin class
    for calculator perspective
    """
    
    def __init__(self, standalone=True):
        """
        Abstract class for gui_manager Plugins.
        """
        ## Plug-in name. It will appear on the application menu.
        self.sub_menu = "Calculator"        
        
        ## Reference to the parent window. Filled by get_panels() below.
        self.parent = None
        
        ## List of panels that you would like to open in AUI windows
        #  for your plug-in. This defines your plug-in "perspective"
        self.perspective = []
        # Log startup
        logging.info("Calculator plug-in started")   
        
    def populate_menu(self, id, owner):
        """
        Create and return the list of application menu
        items for the plug-in. 
        
        :param id: deprecated. Un-used.
        :param parent: parent window
        
        :return: plug-in menu
        
        """
        return []
      
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
       
        return []
       
    
    def help(self, evt):
        """
        Show a general help dialog. 
        
        :TODO: replace the text with a nice image
            provide more hint on the SLD calculator
        """
        from help_panel import  HelpWindow
        frame = HelpWindow(None, -1)    
        frame.Show(True)
      
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
            
            @param graph: the Graph object to which we attach the context menu
            @return: a list of menu items with call-back function
        """
        return []    
    
    def get_perspective(self):
        """
        Get the list of panel names for this perspective
        """
        return self.perspective
        
    
    def get_tools(self):
        """
        Returns a set of menu entries for tools
        """
        kiessig_help = "This tool is to approximatly compute the "
        kiessig_help += "thickness of a shell or the size of "
        kiessig_help += "particles \n from the width of a Kiessig fringe."
        sld_help = "Provides computation related to Scattering Length Density"
        slit_length_help = "Provides computation related to Slit Length Density"
        data_editor_help = "Meta Data Editor"
        return [("SLD Calculator", sld_help, self.on_calculate_sld),
                ("Slit Size Calculator", slit_length_help,
                        self.on_calculate_slit_size),
                ("Kiessig Thickness Calculator", 
                        kiessig_help, self.on_calculate_kiessig),]#,
                #("Data Editor", data_editor_help, self.on_edit_data)]
              
    def on_edit_data(self, event):
        """
        Edit meta data 
        """
        from data_editor import DataEditorWindow
        frame = DataEditorWindow(parent=self.parent, data=[], title="Data Editor")
        frame.Show(True)

    def on_calculate_kiessig(self, event):
        """
        Compute the Kiessig thickness
        """
        from kiessig_calculator_panel import KiessigWindow
        frame = KiessigWindow()
        frame.Show(True) 
    
       
    def on_calculate_sld(self, event):
        """
        Compute the scattering length density of molecula
        """
        from sld_panel import SldWindow
        frame = SldWindow(base=self.parent)
        frame.Show(True) 
    
    def on_calculate_slit_size(self, event):
        """
        Compute the slit size a given data
        """
        from slit_length_calculator_panel import SlitLengthCalculatorWindow
        frame = SlitLengthCalculatorWindow(parent=self.parent)    
        frame.Show(True)
        
    def on_perspective(self, event):
        """
        Call back function for the perspective menu item.
        We notify the parent window that the perspective
        has changed.
        
        :param event: menu event
        
        """
        self.parent.set_perspective(self.perspective)
       
    
    def post_init(self):
        """
        Post initialization call back to close the loose ends
        """
        pass
    
  
    
