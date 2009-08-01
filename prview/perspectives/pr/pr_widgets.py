"""
This software was developed by the University of Tennessee as part of the
Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
project funded by the US National Science Foundation. 

See the license text in license.txt

copyright 2009, University of Tennessee
"""

"""
    Text controls for input/output of the main PrView panel
"""

import wx
import os

class PrTextCtrl(wx.TextCtrl):
    """
        Text control for model and fit parameters.
        Binds the appropriate events for user interactions.
    """
    def __init__(self, *args, **kwds):
        
        wx.TextCtrl.__init__(self, *args, **kwds)
        
        # Bind appropriate events
        self.Bind(wx.EVT_LEFT_UP, self._highlight_text)
        
    def _highlight_text(self, event):
        """
            Highlight text of a TextCtrl only of no text has be selected
            @param event: mouse event
        """
        control  = event.GetEventObject()
        # Check that we have a TextCtrl
        if issubclass(control.__class__, wx.TextCtrl):
            # Check whether text has been selected, 
            # if not, select the whole string

            (start, end) = control.GetSelection()
            if start==end:
                control.SetSelection(-1,-1)
                
        # Make sure the mouse event is available to other listeners
        event.Skip()

class OutputTextCtrl(wx.TextCtrl):
    """
        Text control used to display outputs.
        No editing allowed. The background is 
        grayed out. User can't select text.
    """
    def __init__(self, *args, **kwds):
        wx.TextCtrl.__init__(self, *args, **kwds)
        self.SetEditable(False)
        self.SetBackgroundColour(self.GetParent().GetBackgroundColour())
        
        # Bind to mouse event to avoid text highlighting
        # The event will be skipped once the call-back
        # is called.
        self.Bind(wx.EVT_MOUSE_EVENTS, self._click)
        
    def _click(self, event):
        """
            Prevent further handling of the mouse event
            by not calling Skip().
        """ 
        pass
        

class DataFileTextCtrl(OutputTextCtrl):
    """
        Text control used to display only the file name
        given a full path.
         
        TODO: now that we no longer choose the data file from the panel,
        it's no longer necessary to pass around the file path. That code
        should be refactored away and simplified. 
    """
    def __init__(self, *args, **kwds):
        OutputTextCtrl.__init__(self, *args, **kwds)
        self._complete_path = None
    
    def SetValue(self, value):
        """
            Sets the file name given a path
        """
        self._complete_path = str(value)
        file = os.path.basename(self._complete_path)
        OutputTextCtrl.SetValue(self, file)
        
    def GetValue(self):
        """
            Return the full path
        """
        return self._complete_path
