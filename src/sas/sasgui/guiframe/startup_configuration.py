################################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation.
#
#See the license text in license.txt
#
#copyright 2009, University of Tennessee
################################################################################
import os
import copy

import wx

from sas import make_custom_config_path
from sas.sasgui.guiframe.events import StatusEvent
from sas.sasgui.guiframe.gui_style import GUIFRAME
from sas.sasgui.guiframe import gui_manager as CURRENT


# default configuration
DEFAULT_STRINGS = {'GUIFRAME_WIDTH':-1,
                   'GUIFRAME_HEIGHT':-1,
                   'CONTROL_WIDTH':-1,
                   'CONTROL_HEIGHT':-1,
                   'PLOPANEL_WIDTH':-1,
                   'DATAPANEL_WIDTH':-1,
                   'DATALOADER_SHOW':True,
                   'TOOLBAR_SHOW':True,
                   'FIXED_PANEL':True,
                   'WELCOME_PANEL_SHOW':False,
                   'CLEANUP_PLOT':False,
                   'DEFAULT_PERSPECTIVE':'Fitting',
                   'DEFAULT_OPEN_FOLDER': None,
                   'SAS_OPENCL': None}
try:
    CURRENT_STRINGS = {'GUIFRAME_WIDTH':CURRENT.GUIFRAME_WIDTH,
                       'GUIFRAME_HEIGHT':CURRENT.GUIFRAME_HEIGHT,
                       'CONTROL_WIDTH':CURRENT.CONTROL_WIDTH,
                       'CONTROL_HEIGHT':CURRENT.CONTROL_HEIGHT,
                       'PLOPANEL_WIDTH':CURRENT.PLOPANEL_WIDTH,
                       'DATAPANEL_WIDTH':CURRENT.DATAPANEL_WIDTH,
                       'DATALOADER_SHOW':CURRENT.DATALOADER_SHOW,
                       'TOOLBAR_SHOW':CURRENT.TOOLBAR_SHOW,
                       'FIXED_PANEL':CURRENT.FIXED_PANEL,
                       'WELCOME_PANEL_SHOW':CURRENT.WELCOME_PANEL_SHOW,
                       'CLEANUP_PLOT':CURRENT.CLEANUP_PLOT,
                       'DEFAULT_PERSPECTIVE':CURRENT.DEFAULT_PERSPECTIVE,
                       'DEFAULT_OPEN_FOLDER':CURRENT.DEFAULT_OPEN_FOLDER,
                       'SAS_OPENCL': None}
except:
    CURRENT_STRINGS = DEFAULT_STRINGS
FONT_VARIANT = 0
PANEL_WIDTH = 285
PANEL_HEIGHT = 215

"""
Dialog to set Appication startup configuration
"""
class StartupConfiguration(wx.Dialog):
    """
    Dialog for Startup Configuration
    """
    def __init__(self, parent, gui, id=-1, title="Startup Setting"):
        wx.Dialog.__init__(self, parent, id, title,
                           size=(PANEL_WIDTH, PANEL_HEIGHT))
        # parent
        self.parent = parent
        self._gui = gui
        # font size
        self.SetWindowVariant(variant=FONT_VARIANT)
        self.current_string = copy.deepcopy(CURRENT_STRINGS)
        self.return_string = copy.deepcopy(DEFAULT_STRINGS)
        # build layout
        vbox = wx.BoxSizer(wx.VERTICAL)
        title_text = wx.StaticText(self, id=wx.NewId(), label='Set interface configuration')

        default_bt = wx.RadioButton(self, -1, 'Default View', (15, 30),
                                    style=wx.RB_GROUP)
        default_bt.Bind(wx.EVT_RADIOBUTTON, self.OnDefault)
        default_bt.SetValue(True)
        current_bt = wx.RadioButton(self, -1, 'Current View', (15, 55))
        current_bt.SetValue(False)
        current_bt.Bind(wx.EVT_RADIOBUTTON, self.OnCurrent)
        msg = "\nThis new configuration will take effect when\n"
        msg += "running this application next time."
        note_txt = wx.StaticText(self, -1, msg, (15, 75))
        note_txt.SetForegroundColour("black")

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        okButton = wx.Button(self, wx.ID_OK, 'Set', size=(70, 25))
        closeButton = wx.Button(self, wx.ID_CANCEL, 'Cancel', size=(70, 25))
        hbox.Add(closeButton, 1, wx.RIGHT, 5)
        hbox.Add(okButton, 1, wx.RIGHT, 5)

        vbox.Add(title_text, 0, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 10)
        vbox.Add(default_bt, 0, wx.LEFT, 20)
        vbox.Add(current_bt, 0, wx.LEFT, 20)
        vbox.Add(note_txt, 0, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 10)
        vbox.Add(hbox, 0, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 10)

        self.SetSizer(vbox)


    def OnDefault(self, event=None):
        """
        Set to default
        """
        event.Skip()
        # event object and selection
        self.return_string = copy.deepcopy(DEFAULT_STRINGS)
        return self.return_string

    def OnCurrent(self, event=None):
        """
        Set to curent setup
        """
        event.Skip()
        if self.parent.IsMaximized():
            gui_pw, gui_ph = (0, 0)
        else:
            gui_pw, gui_ph = self.parent.get_window_size()
        self.current_string['GUIFRAME_WIDTH'] = gui_pw
        self.current_string['GUIFRAME_HEIGHT'] = gui_ph
        try:
            p_size = None
            for panel in self.parent.plot_panels.values():
                #p_panel = self.parent._mgr.GetPane(panel.window_name)
                width, _ = panel.frame.GetSizeTuple()
                if panel.frame.IsShown():
                    if p_size is None or width > p_size:
                        p_size = width
            if p_size is None:
                p_size = CURRENT_STRINGS['PLOPANEL_WIDTH']
            self.current_string['PLOPANEL_WIDTH'] = p_size

            try:
                control_frame = self.parent.get_current_perspective().frame
                control_w, control_h = control_frame.GetSizeTuple()
                self.current_string['CONTROL_WIDTH'] = control_w
                self.current_string['CONTROL_HEIGHT'] = control_h
            except:
                self.current_string['CONTROL_WIDTH'] = -1
                self.current_string['CONTROL_HEIGHT'] = -1

            data_pw, _ = self.parent.panels["data_panel"].frame.GetSizeTuple()
            if data_pw is None:
                data_pw = CURRENT_STRINGS['DATAPANEL_WIDTH']
            self.current_string['DATAPANEL_WIDTH'] = data_pw

            #label = self.parent._data_panel_menu.GetText()
            label = self.parent.panels['data_panel'].frame.IsShown()
            if label:# == 'Hide Data Explorer':
                self.current_string['DATALOADER_SHOW'] = True
            else:
                self.current_string['DATALOADER_SHOW'] = False

            if self.parent._toolbar.IsShown():
                self.current_string['TOOLBAR_SHOW'] = True
            else:
                self.current_string['TOOLBAR_SHOW'] = False

            style = self._gui & GUIFRAME.FLOATING_PANEL
            if style == GUIFRAME.FLOATING_PANEL:
                self.current_string['FIXED_PANEL'] = False
            else:
                self.current_string['FIXED_PANEL'] = True

            if self.parent.panels['default'].frame.IsShown():
                self.current_string['WELCOME_PANEL_SHOW'] = True
            else:
                self.current_string['WELCOME_PANEL_SHOW'] = False
            self.current_string['CLEANUP_PLOT'] = \
                                        self.parent.cleanup_plots
            perspective = self.parent.get_current_perspective()
            self.current_string['DEFAULT_PERSPECTIVE'] =\
                                            str(perspective.sub_menu)
            location = ''
            temp = self.parent._default_save_location.split("\\")
            for strings in temp:
                location += (strings + "/")
            self.current_string['DEFAULT_OPEN_FOLDER'] = location
                        #self.parent._default_save_location.ascii_letters

        except:
            raise
        # event object and selection
        self.return_string = self.current_string
        return self.return_string


    def write_custom_config(self):
        """
        Write custom configuration
        """
        path = make_custom_config_path()
        with open(path, 'w') as out_f:
            out_f.write("#Application appearance custom configuration\n")
            for key, item in self.return_string.iteritems():
                if (key == 'DEFAULT_PERSPECTIVE') or \
                    (key == 'DEFAULT_OPEN_FOLDER' and item != None):
                    out_f.write("%s = \"%s\"\n" % (key, str(item)))
                else:
                    out_f.write("%s = %s\n" % (key, str(item)))
