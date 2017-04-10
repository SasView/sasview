
################################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation.
#
#See the license text in license.txt
#
#copyright 2009, University of Tennessee
################################################################################

"""
Text controls for input/output of the main PrView panel
"""

import wx
import os
from wx.lib.scrolledpanel import ScrolledPanel

WIDTH = 400
HEIGHT = 350


class DialogPanel(ScrolledPanel):
    def __init__(self, *args, **kwds):
        ScrolledPanel.__init__(self, *args, **kwds)
        self.SetupScrolling()


class PrTextCtrl(wx.TextCtrl):
    """
    Text control for model and fit parameters.
    Binds the appropriate events for user interactions.
    """
    def __init__(self, *args, **kwds):

        wx.TextCtrl.__init__(self, *args, **kwds)

        ## Set to True when the mouse is clicked while the whole string is selected
        self.full_selection = False
        ## Call back for EVT_SET_FOCUS events
        _on_set_focus_callback = None
        # Bind appropriate events
        self.Bind(wx.EVT_LEFT_UP, self._highlight_text)
        self.Bind(wx.EVT_SET_FOCUS, self._on_set_focus)

    def _on_set_focus(self, event):
        """
        Catch when the text control is set in focus to highlight the whole
        text if necessary

        :param event: mouse event

        """
        event.Skip()
        self.full_selection = True

    def _highlight_text(self, event):
        """
        Highlight text of a TextCtrl only of no text has be selected

        :param event: mouse event

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

class OutputTextCtrl(wx.TextCtrl):
    """
    Text control used to display outputs.
    No editing allowed. The background is
    grayed out. User can't select text.
    """
    def __init__(self, *args, **kwds):
        """
        """
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

    :TODO: now that we no longer choose the data file from the panel,
        it's no longer necessary to pass around the file path. That code
        should be refactored away and simplified.
    """
    def __init__(self, *args, **kwds):
        """
        """
        OutputTextCtrl.__init__(self, *args, **kwds)
        self._complete_path = None

    def SetValue(self, value):
        """
        Sets the file name given a path
        """
        self._complete_path = str(value)
        file_path = os.path.basename(self._complete_path)
        OutputTextCtrl.SetValue(self, file_path)

    def GetValue(self):
        """
        Return the full path
        """
        return self._complete_path


def load_error(error=None):
    """
    Pop up an error message.

    :param error: details error message to be displayed
    """
    message = "The data file you selected could not be loaded.\n"
    message += "Make sure the content of your file is properly formatted.\n\n"

    if error is not None:
        message += "When contacting the DANSE team, mention the"
        message += " following:\n%s" % str(error)

    dial = wx.MessageDialog(None, message, 'Error Loading File',
                            wx.OK | wx.ICON_EXCLAMATION)
    dial.ShowModal()


class DataDialog(wx.Dialog):
    """
    Allow file selection at loading time
    """
    def __init__(self, data_list, parent=None, text='', *args, **kwds):
        kwds['size'] = (WIDTH, HEIGHT)
        kwds['title'] = "Data Selection"
        wx.Dialog.__init__(self, parent, *args, **kwds)
        self.list_of_ctrl = []
        self._sizer_main = wx.BoxSizer(wx.VERTICAL)
        self._sizer_txt = wx.BoxSizer(wx.VERTICAL)
        self._sizer_button = wx.BoxSizer(wx.HORIZONTAL)
        self._choice_sizer = wx.GridBagSizer(5, 5)
        self._panel = DialogPanel(self, style=wx.RAISED_BORDER,
                                  size=(WIDTH - 20, HEIGHT / 3))

        self.__do_layout(data_list, text=text)

    def __do_layout(self, data_list, text=''):
        """
        layout the dialog
        """
        #add text
        if text.strip() == "":
            text = "This Perspective does not allow multiple data !\n"
            text += "Please select only one Data.\n"
        text_ctrl = wx.TextCtrl(self, -1, str(text), style=wx.TE_MULTILINE,
                                size=(-1, HEIGHT / 3))
        text_ctrl.SetEditable(False)
        self._sizer_txt.Add(text_ctrl, 1, wx.EXPAND | wx.ALL, 10)
        iy = 0
        ix = 0
        rbox = wx.RadioButton(self._panel, -1, str(data_list[0].name),
                              (10, 10), style=wx.RB_GROUP)
        rbox.SetValue(True)
        self.list_of_ctrl.append((rbox, data_list[0]))
        self._choice_sizer.Add(rbox, (iy, ix), (1, 1),
                               wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
        for i in range(1, len(data_list)):
            iy += 1
            rbox = wx.RadioButton(self._panel, -1,
                                  str(data_list[i].name), (10, 10))
            rbox.SetValue(False)
            self.list_of_ctrl.append((rbox, data_list[i]))
            self._choice_sizer.Add(rbox, (iy, ix),
                                   (1, 1), wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
        self._panel.SetSizer(self._choice_sizer)
        #add sizer
        self._sizer_button.Add((20, 20), 1, wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        button_cancel = wx.Button(self, wx.ID_CANCEL, "Cancel")
        self._sizer_button.Add(button_cancel, 0,
                               wx.LEFT | wx.RIGHT | wx.ADJUST_MINSIZE, 10)
        button_ok = wx.Button(self, wx.ID_OK, "Ok")
        button_ok.SetFocus()
        self._sizer_button.Add(button_ok, 0,
                               wx.LEFT | wx.RIGHT | wx.ADJUST_MINSIZE, 10)
        static_line = wx.StaticLine(self, -1)

        self._sizer_txt.Add(self._panel, 0, wx.EXPAND | wx.ALL, 5)
        self._sizer_main.Add(self._sizer_txt, 0, wx.EXPAND | wx.ALL, 5)
        self._sizer_main.Add(static_line, 0, wx.EXPAND, 0)
        self._sizer_main.Add(self._sizer_button, 0, wx.EXPAND | wx.ALL, 10)
        self.SetSizer(self._sizer_main)

    def get_data(self):
        """
        return the selected data
        """
        for item in self.list_of_ctrl:
            rbox, data = item
            if rbox.GetValue():
                return data
