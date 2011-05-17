
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
# default configuration
DEFAULT_STRINGS = {'GUIFRAME_WIDTH':1150,
                   'GUIFRAME_HEIGHT':840,
                   'PLOPANEL_WIDTH':415,
                   'DATAPANEL_WIDTH':235,
                   'DATALOADER_SHOW':True,
                   'TOOLBAR_SHOW':True,
                   'FIXED_PANEL':True,
                   'WELCOME_PANEL_SHOW':False,
                   'DEFAULT_PERSPECTIVE':'Fitting'}

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
        self.path = parent.path
        self._gui = gui
        # font size 
        self.SetWindowVariant(variant=FONT_VARIANT)
        self.current_string = copy.deepcopy(DEFAULT_STRINGS)
        # build layout
        panel = wx.Panel(self, -1)
        vbox = wx.BoxSizer(wx.VERTICAL)
        wx.StaticBox(panel, -1, 'Change Configuration', (5, 5),
                      (PANEL_WIDTH*0.94, PANEL_HEIGHT*0.7))
        default_bt = wx.RadioButton(panel, -1, 'Default View', (15, 30), 
                                    style=wx.RB_GROUP)
        default_bt.Bind(wx.EVT_RADIOBUTTON, self.OnDefault)
        default_bt.SetValue(True)
        current_bt = wx.RadioButton(panel, -1, 'Current View', (15, 55))
        current_bt.SetValue(False)
        current_bt.Bind(wx.EVT_RADIOBUTTON, self.OnCurrent)
        msg = "\nThis new configuration will take effect on\n"
        msg += "restarting this application..."
        note_txt = wx.StaticText(panel, -1, msg, (15, 75))
        
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
        return DEFAULT_STRINGS
        
    def OnCurrent(self, event=None):
        """
        Set to curent setup
        """
        event.Skip()
        
        gui_pw, gui_ph = self.parent.GetSizeTuple()
        self.current_string['GUIFRAME_WIDTH'] = gui_pw
        self.current_string['GUIFRAME_HEIGHT'] = gui_ph
        try:
            p_size = None
            for panel in self.parent.plot_panels.values():
                if p_size == None or panel.size > p_size:
                    p_size = panel.size
            if p_size == None:
                p_size = DEFAULT_STRINGS['PLOPANEL_WIDTH']
            self.current_string['PLOPANEL_WIDTH'] = p_size
            
            data_pw, _ = self.parent.panels["data_panel"].GetSizeTuple()
            if data_pw == None:
                data_pw = DEFAULT_STRINGS['DATAPANEL_WIDTH']
            self.current_string['DATAPANEL_WIDTH'] = data_pw
            
            label = self.parent._data_panel_menu.GetText()
            if label == 'Data Explorer OFF':
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
            
            perspective = self.parent.get_current_perspective()
            self.current_string['DEFAULT_PERSPECTIVE'] = str(perspective.sub_menu)
            
        except:
            raise
        # event object and selection
        return self.current_string

    def OnCancel(self, event):
        """
        Close event
        """
        # clear event
        event.Skip()
    
        self.Destroy()
    
    def OnClose(self, event):
        """
        Close event
        """
        # clear event
        event.Skip()
        fname = os.path.join(self.path, 'custom_config.py')
        self.write_string(fname, self.current_string)
    
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
            if key == 'DEFAULT_PERSPECTIVE':
                out_f.write("%s = '%s'\n" % (key,str(item)))
            else:
                out_f.write("%s = %s\n" % (key,str(item)))
    
        out_f.close() 