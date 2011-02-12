

################################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation. 
#
#See the license text in license.txt
#
#copyright 2008, University of Tennessee
################################################################################


from sans.guiframe.events import PanelOnFocusEvent
import wx

class PanelBase:
    """
    Defines the API for a panels to work with
    the ViewerFrame toolbar and menu bar
    """
    ## Internal nickname for the window, used by the AUI manager
    #window_name = "default"
    ## Name to appear on the window title bar
    #window_caption = "Welcome panel"
    ## Flag to tell the AUI manager to put this panel in the center pane
    group_id = None
    
    def __init__(self, parent=None):
        """
        Initialize some flag that Viewerframe used
        """
        #panel manager
        self._manager = None
        self.parent = parent
        self._print_flag = False
        self._undo_flag = False
        self._redo_flag = False
        self._preview_flag = False
        self._bookmark_flag = False
        self._zoom_in_flag = False
        self._zoom_out_flag = False
        self._zoom_flag = False
        self._save_flag = False
        self._drag_flag = False
        self._reset_flag = False
        self._has_changed = False
        
        self.Bind(wx.EVT_LEFT_DOWN, self.on_set_focus)
        self.Bind(wx.EVT_TEXT_ENTER, self.on_set_focus)
        self.Bind(wx.EVT_MIDDLE_DOWN, self.on_set_focus)
        self.Bind(wx.EVT_RIGHT_DOWN, self.on_set_focus)
        
    def has_changed(self):
        """
        """
        return self._has_changed
            
    def _set_print_flag(self, flag=True):
        """
        The derivative class sets the print flag value to indicate that it can 
        be printed
        """
        if flag == self._print_flag:
            self._has_changed = False
            return
        self._has_changed = True
        self._print_flag = flag
        if self._manager is not None and self._manager.parent is not None:
            self._manager.parent.enable_print()
     
    def get_print_flag(self):
        """
        Get the print flag to update appropriately the tool bar
        """
        return self._print_flag
    
    def _set_undo_flag(self, flag=True):
        """
        The derivative class sets the undo flag value to indicate that the 
        current action done can be canceled
        """
        if flag == self._undo_flag:
            self._has_changed = False
            return
        self._has_changed = True
        self._undo_flag = flag
        if self._manager is not None and self._manager.parent is not None:
            self._manager.parent.enable_undo()
      
    def get_undo_flag(self):
        """
        Get the undo flag to update appropriately the tool bar
        """
        return self._undo_flag
    
    def _set_redo_flag(self, flag=True):
        """
        The derivative class sets the redo flag value to indicate that the 
        action done can be recovered
        """
        if flag == self._redo_flag:
            self._has_changed = False
            return
        self._has_changed = True
        self._redo_flag = flag
        if self._manager is not None and self._manager.parent is not None:
            self._manager.parent.enable_redo()
      
    def get_redo_flag(self):
        """
        Get the redo flag to update appropriately the tool bar
        """
        return self._redo_flag
    
    def _set_zoomed_in_flag(self, flag=True):
        """
        The derivative class sets the zoom in flag value to indicate that it
        can be zoomed in
        """
        if self._zoom_in_flag == flag:
            self._has_changed = False
            return
        self._has_changed = True
        self._zoom_in_flag = flag
        if self._manager is not None and self._manager.parent is not None:
            self._manager.parent.enable_zoom_in()
       
    def get_zoom_in_flag(self):
        """
        Get the zoom in flag to update appropriately the tool bar
        """
        return self._zoom_in_flag
    
    def _set_zoomed_out_flag(self, flag=True):
        """
        The derivative class sets the zoom out flag value to indicate that it
        can be zoomed out
        """
        if self._zoom_out_flag == flag:
            self._has_changed = False
            return
        self._has_changed = True
        self._zoom_out_flag = flag
        if self._manager is not None and self._manager.parent is not None:
            self._manager.parent.enable_zoom_out()
        
    def get_zoom_out_flag(self):
        """
        Get the zoom out flag to update appropriately the tool bar
        """
        return self._zoom_out_flag
    
    def _set_zoom_flag(self, flag=True):
        """
        The derivative class sets the zoom flag value to indicate that it
        can be zoomed
        """
        if flag == self._zoom_flag:
            self._has_changed = False
            return
        self._has_changed = True
        self._zoom_flag = flag
        if self._manager is not None and self._manager.parent is not None:
            self._manager.parent.enable_zoom()
     
    def get_zoom_flag(self):
        """
        Get the zoom flag to update appropriately the tool bar
        """
        return self._zoom_flag
    
    def _set_bookmark_flag(self, flag=True):
        """
        The derivative class sets the bookmark flag value to indicate that it
        can be bookmarked
        """
        if flag == self._bookmark_flag:
            self._has_changed = False
            return
        self._has_changed = True
        self._bookmark_flag = flag
        if self._manager is not None and self._manager.parent is not None:
            self._manager.parent.enable_bookmark()
       
    def get_bookmark_flag(self):
        """
        Get the bookmark flag to update appropriately the tool bar
        """
        return self._bookmark_flag
    
    def _set_preview_flag(self, flag=True):
        """
        The derivative class sets the preview flag value to indicate that it
        can be previewed
        """
        if flag == self._preview_flag:
            self._has_changed = False
            return
        self._has_changed = True
        self._preview_flag = flag
        if self._manager is not None and self._manager.parent is not None:
            self._manager.parent.enable_preview()
       
    def get_preview_flag(self):
        """
        Get the preview flag to update appropriately the tool bar
        """
        return self._preview_flag
    
    def _set_save_flag(self, flag=True):
        """
        The derivative class sets the drag flag value to indicate that it
        can be saved
        """
        if flag == self._save_flag:
            self._has_changed = False
            return
        self._has_changed = True
        self._save_flag = flag
        if self._manager is not None and self._manager.parent is not None:
            self._manager.parent.enable_save()

    def get_save_flag(self):
        """
        Get the save flag to update appropriately the tool bar
        """
        return self._save_flag
    
    def _set_drag_flag(self, flag=True):
        """
        The derivative class sets the drag flag value to indicate that 
        dragging motion is possible
        """
        if self._drag_flag == flag:
            self._has_changed = False
            return
        self._has_changed = True
        self._drag_flag = flag
        if self._manager is not None and self._manager.parent is not None:
            self._manager.parent.enable_drag()
       
    def get_drag_flag(self):
        """
        Get the drag flag to update appropriately the tool bar
        """
        return self._drag_flag
    
    def _set_reset_flag(self, flag=True):
        """
        The derivative class sets the reset flag value to indicate that it
        can be reset
        """
        if self._reset_flag == flag:
            self._has_changed = False
            return
        self._has_changed = True
        self._reset_flag = flag
        if self._manager is not None and self._manager.parent is not None:
            self._manager.parent.enable_reset()
      
    def get_reset_flag(self):
        """
        Get the reset flag to update appropriately the tool bar
        """
        return self._reset_flag

    def on_reset(self, event):
        """
        The derivative class state is restored
        """
    def on_drag(self, event):
        """
        The derivative class allows dragging motion if implemented
        """
    def on_preview(self, event):
        """
        Display a printable version of the class derivative
        """
    def on_save(self, event):
        """
        The state of the derivative class is restored
        """
    def on_redo(self, event):
        """
        The previous action is restored if possible
        """
    def on_undo(self, event):
        """
        The current action is canceled
        """
    def on_bookmark(self, event):
        """
        The derivative class is on bookmark mode if implemented
        """
    def on_zoom_in(self, event):
        """
        The derivative class is on zoom in mode if implemented
        """
    def on_zoom_out(self, event):
        """
        The derivative class is on zoom out mode if implemented
        """
    def on_zoom(self, event):
        """
        The derivative class is on zoom mode (using pane)
        if zoom mode is implemented
        """
    def on_set_focus(self, event=None):
        """
        The  derivative class is on focus if implemented
        """
        if self.parent is not None:
            wx.PostEvent(self.parent, PanelOnFocusEvent(panel=self))
        
    def get_data(self):
        """
        return list of current data
        """
        return
    
    def get_state(self):
        """
         return the current state
        """
        return

    def set_manager(self, manager):
        """
        """
        self._manager = manager 
        
    def get_manager(self):
        """
        """
        return self._manager