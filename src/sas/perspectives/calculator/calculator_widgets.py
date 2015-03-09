"""
This software was developed by the University of Tennessee as part of the
Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
project funded by the US National Science Foundation.

See the license text in license.txt

copyright 2009, University of Tennessee
"""
import wx
import sys
CHILD_FRAME = wx.MDIChildFrame
if sys.platform.count("win32") < 1:
    if sys.platform.count("darwin") < 1:
        CHILD_FRAME = wx.Frame

class InputTextCtrl(wx.TextCtrl):
    """
        Text control for model and fit parameters.
        Binds the appropriate events for user interactions.
    """
    def __init__(self, parent=None, *args, **kwds):

        wx.TextCtrl.__init__(self, parent, *args, **kwds)

        ## Set to True when the mouse is clicked while the whole 
        #string is selected
        self.full_selection = False
        ## Call back for EVT_SET_FOCUS events
        _on_set_focus_callback = None
        # Bind appropriate events
        self.Bind(wx.EVT_LEFT_UP, self._highlight_text)
        self.Bind(wx.EVT_SET_FOCUS, self._on_set_focus)
        self.Bind(wx.EVT_TEXT_ENTER, parent._onparamEnter)

    def _on_set_focus(self, event):
        """
            Catch when the text control is set in focus to highlight the whole
            text if necessary
            @param event: mouse event
        """
        event.Skip()
        self.full_selection = True

    def _highlight_text(self, event):
        """
            Highlight text of a TextCtrl only of no text has be selected
            @param event: mouse event
        """
        # Make sure the mouse event is available to other listeners
        event.Skip()
        control = event.GetEventObject()
        if self.full_selection:
            self.full_selection = False
            # Check that we have a TextCtrl
            if issubclass(control.__class__, wx.TextCtrl):
                # Check whether text has been selected, 
                # if not, select the whole string
                (start, end) = control.GetSelection()
                if start == end:
                    control.SetSelection(-1, -1)


class InterActiveOutputTextCtrl(wx.TextCtrl):
    """
        Text control used to display outputs.
        No editing allowed. The background is
        grayed out. User can't select text.
    """
    def __init__(self, *args, **kwds):
        wx.TextCtrl.__init__(self, *args, **kwds)
        self.SetEditable(False)
        self.SetBackgroundColour(self.GetParent().GetBackgroundColour())

class OutputTextCtrl(InterActiveOutputTextCtrl):
    """
        Text control used to display outputs.
        No editing allowed. The background is
        grayed out. User can't select text.
    """
    def __init__(self, *args, **kwds):
        InterActiveOutputTextCtrl.__init__(self, *args, **kwds)
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

