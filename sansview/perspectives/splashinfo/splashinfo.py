
import os
import sys
import wx

class Plugin:
    
    def __init__(self):
        ## Plug-in name
        self.sub_menu = "Welcome"
        
        ## Reference to the parent window
        self.parent = None
        ## List of panels for the simulation perspective (names)
        self.perspective = []
        
    
    def populate_menu(self, id, owner):
        """
            Create a menu for the plug-in
        """
        return []
    
    
    def help(self, evt):
        """
            Show a general help dialog. 
            TODO: replace the text with a nice image
        """
    
    def get_panels(self, parent):
        """
            Create and return a list of panel objects
        """
        self.parent = parent
        self.about_page=None
        from welcome_panel import PanelAbout
        self.about_page = PanelAbout(self.parent, -1)
      
        self.perspective = []
        self.perspective.append(self.about_page.window_name)
    
        return [self.about_page]
   
    
    def get_perspective(self):
        """
            Get the list of panel names for this perspective
        """
        return self.perspective
    
    def on_perspective(self, event):
        """
            Call back function for the perspective menu item.
            We notify the parent window that the perspective
            has changed.
        """
        self.parent.set_perspective(self.perspective)
    
    def post_init(self):
        """
            Post initialization call back to close the loose ends
        """
        self.parent.set_perspective(self.perspective)

   
    