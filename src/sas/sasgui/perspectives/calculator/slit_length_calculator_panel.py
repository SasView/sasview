"""
This software was developed by the University of Tennessee as part of the
Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
project funded by the US National Science Foundation.

See the license text in license.txt

copyright 2008, 2009, University of Tennessee
"""

import wx
import sys
import os

from sas.sasgui.guiframe.panel_base import PanelBase

from sas.sasgui.guiframe.events import StatusEvent
from sas.sascalc.calculator.slit_length_calculator import SlitlengthCalculator
from .calculator_widgets import OutputTextCtrl
from .calculator_widgets import InterActiveOutputTextCtrl
from sas.sasgui.perspectives.calculator import calculator_widgets as widget
from sas.sasgui.guiframe.documentation_window import DocumentationWindow

_BOX_WIDTH = 76
#Slit length panel size 
if sys.platform.count("win32") > 0:
    PANEL_TOP = 0
    PANEL_WIDTH = 500
    PANEL_HEIGHT = 210
    FONT_VARIANT = 0
else:
    PANEL_TOP = 60
    PANEL_WIDTH = 530
    PANEL_HEIGHT = 210
    FONT_VARIANT = 1

class SlitLengthCalculatorPanel(wx.Panel, PanelBase):
    """
        Provides the slit length calculator GUI.
    """
    ## Internal nickname for the window, used by the AUI manager
    window_name = "Slit Size Calculator"
    ## Name to appear on the window title bar
    window_caption = "Slit Size Calculator"
    ## Flag to tell the AUI manager to put this panel in the center pane
    CENTER_PANE = True

    def __init__(self, parent, *args, **kwds):
        wx.Panel.__init__(self, parent, *args, **kwds)
        PanelBase.__init__(self)
        #Font size 
        self.SetWindowVariant(variant=FONT_VARIANT)
        #thread to read data 
        self.reader = None
        # Default location
        self._default_save_location = os.getcwd()
        # Object that receive status event
        self.parent = parent
        self._do_layout()

    def _define_structure(self):
        """
            Define the main sizers building to build this application.
        """
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.box_source = wx.StaticBox(self, -1, str("Slit Size Calculator"))
        self.boxsizer_source = wx.StaticBoxSizer(self.box_source,
                                                    wx.VERTICAL)
        self.data_name_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.slit_size_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.hint_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.button_sizer = wx.BoxSizer(wx.HORIZONTAL)

    def _layout_data_name(self):
        """
            Fill the sizer containing data's name
        """
        data_name_txt = wx.StaticText(self, -1, 'Data: ')
        self.data_name_tcl = OutputTextCtrl(self, -1,
                                            size=(_BOX_WIDTH * 4, -1))
        data_hint = "Loaded data"
        self.data_name_tcl.SetToolTipString(data_hint)
        #control that triggers importing data
        id = wx.NewId()
        self.browse_button = wx.Button(self, id, "Browse")
        hint_on_browse = "Click on this button to import data in this panel."
        self.browse_button.SetToolTipString(hint_on_browse)
        self.Bind(wx.EVT_BUTTON, self.on_load_data, id=id)
        self.data_name_sizer.AddMany([(data_name_txt, 0, wx.LEFT, 15),
                                      (self.data_name_tcl, 0, wx.LEFT, 10),
                                      (self.browse_button, 0, wx.LEFT, 10)])
    def _layout_slit_size(self):
        """
            Fill the sizer containing slit size information
        """
        slit_size_txt = wx.StaticText(self, -1, 'Slit Size (FWHM/2): ')
        self.slit_size_tcl = InterActiveOutputTextCtrl(self, -1,
                                                       size=(_BOX_WIDTH, -1))
        slit_size_hint = " Estimated full slit size"
        self.slit_size_tcl.SetToolTipString(slit_size_hint)
        slit_size_unit_txt = wx.StaticText(self, -1, 'Unit: ')
        self.slit_size_unit_tcl = OutputTextCtrl(self, -1,
                                                 size=(_BOX_WIDTH, -1))
        slit_size_unit_hint = "Full slit size's unit"
        self.slit_size_unit_tcl.SetToolTipString(slit_size_unit_hint)
        self.slit_size_sizer.AddMany([(slit_size_txt, 0, wx.LEFT, 15),
                                      (self.slit_size_tcl, 0, wx.LEFT, 10),
                                      (slit_size_unit_txt, 0, wx.LEFT, 10),
                                    (self.slit_size_unit_tcl, 0, wx.LEFT, 10)])

    def _layout_hint(self):
        """
            Fill the sizer containing hint
        """
        hint_msg = "This calculation works only for  SAXSess beam profile data."
        self.hint_txt = wx.StaticText(self, -1, hint_msg)
        self.hint_sizer.AddMany([(self.hint_txt, 0, wx.LEFT, 15)])

    def _layout_button(self):
        """
            Do the layout for the button widgets
        """
        self.bt_close = wx.Button(self, wx.ID_CANCEL, 'Close')
        self.bt_close.Bind(wx.EVT_BUTTON, self.on_close)
        self.bt_close.SetToolTipString("Close this window.")

        id = wx.NewId()
        self.button_help = wx.Button(self, id, "HELP")
        self.button_help.SetToolTipString("Help for slit length calculator.")
        self.Bind(wx.EVT_BUTTON, self.on_help, id=id)

        self.button_sizer.AddMany([(self.button_help, 0, wx.LEFT, 280),
                                   (self.bt_close, 0, wx.LEFT, 20)])

    def _do_layout(self):
        """
            Draw window content
        """
        self._define_structure()
        self._layout_data_name()
        self._layout_slit_size()
        self._layout_hint()
        self._layout_button()
        self.boxsizer_source.AddMany([(self.data_name_sizer, 0,
                                          wx.EXPAND | wx.TOP | wx.BOTTOM, 5),
                                   (self.slit_size_sizer, 0,
                                     wx.EXPAND | wx.TOP | wx.BOTTOM, 5),
                                     (self.hint_sizer, 0,
                                     wx.EXPAND | wx.TOP | wx.BOTTOM, 5)])
        self.main_sizer.AddMany([(self.boxsizer_source, 0, wx.ALL, 10),
                                  (self.button_sizer, 0,
                                    wx.EXPAND | wx.TOP | wx.BOTTOM, 5)])
        self.SetSizer(self.main_sizer)
        self.SetAutoLayout(True)

    def choose_data_file(self, location=None):
        path = None
        filename = ''
        if location is None:
            location = os.getcwd()

        wildcard = "SAXSess Data 1D (*.DAT, *.dat)|*.DAT"

        dlg = wx.FileDialog(self, "Choose a file", location,
                            "", wildcard, wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            filename = os.path.basename(path)
        dlg.Destroy()

        return path

    def on_help(self, event):
        """
        Bring up the slit length calculator Documentation whenever
        the HELP button is clicked.

        Calls DocumentationWindow with the path of the location within the
        documentation tree (after /doc/ ....".  Note that when using old
        versions of Wx (before 2.9) and thus not the release version of
        installers, the help comes up at the top level of the file as
        webbrowser does not pass anything past the # to the browser when it is
        running "file:///...."

    :param evt: Triggers on clicking the help button
    """

        _TreeLocation = "user/sasgui/perspectives/calculator/"
        _TreeLocation += "slit_calculator_help.html"
        _doc_viewer = DocumentationWindow(self, -1, _TreeLocation, "",
                                          "Slit Length Calculator Help")

    def on_close(self, event):
        """
            close the window containing this panel
        """
        self.parent.Close()

    def on_load_data(self, event):
        """
            Open a file dialog to allow the user to select a given file.
            The user is only allow to load file with extension .DAT or .dat.
            Display the slit size corresponding to the loaded data.
        """
        path = self.choose_data_file(location=self._default_save_location)

        if path is None:
            return
        self._default_save_location = path
        try:
            #Load data
            from .load_thread import DataReader
            ## If a thread is already started, stop it
            if self.reader is not None and self.reader.isrunning():
                self.reader.stop()
            if self.parent.parent is not None:
                wx.PostEvent(self.parent.parent,
                                StatusEvent(status="Loading...",
                                type="progress"))
            self.reader = DataReader(path=path,
                                    completefn=self.complete_loading,
                                    updatefn=self.load_update)
            self.reader.queue()
            self.load_update()
        except:
            if self.parent.parent is None:
                return
            msg = "Slit Length Calculator: %s" % (sys.exc_info()[1])
            wx.PostEvent(self.parent.parent,
                          StatusEvent(status=msg, type='stop'))
            return

    def load_update(self):
        """
        print update on the status bar
        """
        if self.parent.parent is None:
                return
        if self.reader.isrunning():
            type = "progress"
        else:
            type = "stop"
        wx.PostEvent(self.parent.parent, StatusEvent(status="",
                                                  type=type))

    def complete_loading(self, data=None, filename=''):
        """
            Complete the loading and compute the slit size
        """
        if data is None or data.__class__.__name__ == 'Data2D':
            if self.parent.parent is None:
                return
            msg = "Slit Length cannot be computed for 2D Data"
            wx.PostEvent(self.parent.parent,
                         StatusEvent(status=msg, type='stop'))
            return
        self.data_name_tcl.SetValue(str(data.filename))
        #compute the slit size
        try:
            x = data.x
            y = data.y
            if x == [] or  x is None or y == [] or y is None:
                msg = "The current data is empty please check x and y"
                raise ValueError(msg)
            slit_length_calculator = SlitlengthCalculator()
            slit_length_calculator.set_data(x=x, y=y)
            slit_length = slit_length_calculator.calculate_slit_length()
        except:
            if self.parent.parent is None:
                return
            msg = "Slit Size Calculator: %s" % (sys.exc_info()[1])
            wx.PostEvent(self.parent.parent,
                          StatusEvent(status=msg, type='stop'))
            return
        self.slit_size_tcl.SetValue(str(slit_length))
        #Display unit
        self.slit_size_unit_tcl.SetValue('[Unknown]')
        if self.parent.parent is None:
            return
        msg = "Load Complete"
        wx.PostEvent(self.parent.parent, StatusEvent(status=msg, type='stop'))


class SlitLengthCalculatorWindow(widget.CHILD_FRAME):
    """
    """
    def __init__(self, parent=None, manager=None, title="Slit Size Calculator",
                size=(PANEL_WIDTH, PANEL_HEIGHT), *args, **kwds):
        """
        """
        kwds['size'] = size
        kwds['title'] = title
        widget.CHILD_FRAME.__init__(self, parent, *args, **kwds)
        self.parent = parent
        self.manager = manager
        self.panel = SlitLengthCalculatorPanel(parent=self)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.SetPosition((wx.LEFT, PANEL_TOP))
        self.Show(True)

    def on_close(self, event):
        """
        Close event
        """
        if self.manager is not None:
            self.manager.cal_slit_frame = None
        self.Destroy()

if __name__ == "__main__":
    app = wx.PySimpleApp()
    widget.CHILD_FRAME = wx.Frame
    frame = SlitLengthCalculatorWindow()
    frame.Show(True)
    app.MainLoop()
