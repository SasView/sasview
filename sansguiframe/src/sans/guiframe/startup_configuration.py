
################################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation. 
#
#See the license text in license.txt
#
#copyright 2009, University of Tennessee
################################################################################
import wx
import os
import sys
import copy
#import sans.guiframe.gui_manager as gui
from sans.guiframe.events import StatusEvent  
from sans.guiframe.gui_style import GUIFRAME
from sans.guiframe import gui_manager as CURRENT
from sans.guiframe.customdir  import SetupCustom
# default configuration
DEFAULT_STRINGS = {'GUIFRAME_WIDTH':-1,
                   'GUIFRAME_HEIGHT':-1,
                   'PLOPANEL_WIDTH':-1,
                   'DATAPANEL_WIDTH':-1,
                   'DATALOADER_SHOW':True,
                   'TOOLBAR_SHOW':True,
                   'FIXED_PANEL':True,
                   'WELCOME_PANEL_SHOW':False,
                   'CLEANUP_PLOT':False,
                   'DEFAULT_PERSPECTIVE':'Fitting',
                   'DEFAULT_OPEN_FOLDER': None}
try:
    CURRENT_STRINGS = {'GUIFRAME_WIDTH':CURRENT.GUIFRAME_WIDTH,
                       'GUIFRAME_HEIGHT':CURRENT.GUIFRAME_HEIGHT,
                       'PLOPANEL_WIDTH':CURRENT.PLOPANEL_WIDTH,
                       'DATAPANEL_WIDTH':CURRENT.DATAPANEL_WIDTH,
                       'DATALOADER_SHOW':CURRENT.DATALOADER_SHOW,
                       'TOOLBAR_SHOW':CURRENT.TOOLBAR_SHOW,
                       'FIXED_PANEL':CURRENT.FIXED_PANEL,
                       'WELCOME_PANEL_SHOW':CURRENT.WELCOME_PANEL_SHOW,
                       'CLEANUP_PLOT':CURRENT.CLEANUP_PLOT,
                       'DEFAULT_PERSPECTIVE':CURRENT.DEFAULT_PERSPECTIVE,
                       'DEFAULT_OPEN_FOLDER':CURRENT.DEFAULT_OPEN_FOLDER}
except:
    CURRENT_STRINGS = DEFAULT_STRINGS
    
if sys.platform.count("win32") > 0:
    PANEL_WIDTH = 265 
    PANEL_HEIGHT = 235
    FONT_VARIANT = 0
else:
    PANEL_WIDTH = 285
    PANEL_HEIGHT = 255
    FONT_VARIANT = 1
    
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
        self.path = SetupCustom().find_dir()
        self._gui = gui
        # font size 
        self.SetWindowVariant(variant=FONT_VARIANT)
        self.current_string = copy.deepcopy(CURRENT_STRINGS)
        self.return_string = copy.deepcopy(DEFAULT_STRINGS)
        # build layout
        panel = wx.Panel(self, -1)
        vbox = wx.BoxSizer(wx.VERTICAL)
        wx.StaticBox(panel, -1, 'Set View-Configuration', (5, 5),
                      (PANEL_WIDTH*0.94, PANEL_HEIGHT*0.7))
        default_bt = wx.RadioButton(panel, -1, 'Default View', (15, 30), 
                                    style=wx.RB_GROUP)
        default_bt.Bind(wx.EVT_RADIOBUTTON, self.OnDefault)
        default_bt.SetValue(True)
        current_bt = wx.RadioButton(panel, -1, 'Current View', (15, 55))
        current_bt.SetValue(False)
        current_bt.Bind(wx.EVT_RADIOBUTTON, self.OnCurrent)
        msg = "\nThis new configuration will take effect when\n"
        msg += "running this application next time."
        note_txt = wx.StaticText(panel, -1, msg, (15, 75))
        note_txt.SetForegroundColour("black")
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        cancelButton = wx.Button(self, -1, 'Cancel', size=(70, 25))
        hbox.Add(cancelButton, 1, wx.RIGHT, 5)
        cancelButton.Bind(wx.EVT_BUTTON, self.OnCancel)
        okButton = wx.Button(self, -1, 'OK', size=(70, 25))
        hbox.Add(okButton, 1, wx.RIGHT, 5)
        okButton.Bind(wx.EVT_BUTTON, self.OnClose)
        vbox.Add(panel)

        vbox.Add(hbox, 1, wx.ALIGN_CENTER | wx.RIGHT | wx.BOTTOM, 5)
        # set sizer
        self.SetSizer(vbox)
        #pos = self.parent.GetPosition()
        #self.SetPosition(pos)
        
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
                p_panel = self.parent._mgr.GetPane(panel.window_name)
                if p_panel.IsShown():
                    if p_size == None or panel.size > p_size:
                        p_size = panel.size
            if p_size == None:
                p_size = CURRENT_STRINGS['PLOPANEL_WIDTH']
            self.current_string['PLOPANEL_WIDTH'] = p_size
            
            data_pw, _ = self.parent.panels["data_panel"].GetSizeTuple()
            if data_pw == None:
                data_pw = CURRENT_STRINGS['DATAPANEL_WIDTH']
            self.current_string['DATAPANEL_WIDTH'] = data_pw
            
            #label = self.parent._data_panel_menu.GetText()
            label = self.parent._mgr.GetPane(\
                        self.parent.panels['data_panel'].window_name).IsShown()
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
                
            if self.parent._mgr.GetPane(self.parent.panels['default'].window_name).IsShown():
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

    def OnCancel(self, event):
        """
        Close event
        """
        # clear event
        event.Skip()
        self.return_string = {}
        self.Destroy()
    
    def OnClose(self, event):
        """
        Close event
        """
        # clear event
        event.Skip()
        fname = os.path.join(self.path, 'custom_config.py')
        self.write_string(fname, self.return_string)
    
        self.Destroy()

    def write_string(self, fname, strings):
        """
        Write and Save file
        """
        
        try:
            out_f =  open(fname,'w')
        except :
            raise  #RuntimeError, "Error: Can not change the configuration..."
        out_f.write("#Application appearance custom configuration\n" )
        for key, item in strings.iteritems():
            if (key == 'DEFAULT_PERSPECTIVE') or \
                (key == 'DEFAULT_OPEN_FOLDER' and item != None):
                out_f.write("%s = \"%s\"\n" % (key,str(item)))
            else:
                out_f.write("%s = %s\n" % (key,str(item)))
    
        out_f.close() 
        