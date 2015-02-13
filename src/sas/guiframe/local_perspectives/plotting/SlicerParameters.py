

import wx
import wx.lib.newevent
#from copy import deepcopy
from sas.guiframe.events import EVT_SLICER_PARS
from sas.guiframe.utils import format_number
from sas.guiframe.events import EVT_SLICER
from sas.guiframe.events import SlicerParameterEvent


class SlicerParameterPanel(wx.Dialog):
    """
    Panel class to show the slicer parameters 
    """
    #TODO: show units
    #TODO: order parameters properly
    
    def __init__(self, parent, *args, **kwargs):
        wx.Dialog.__init__(self, parent, *args, **kwargs)
        """
        Dialog window that allow to edit parameters slicer 
        by entering new values
        """
        self.params = {}
        self.parent = parent
        self.type = None
        self.listeners = []
        self.parameters = []
        self.bck = wx.GridBagSizer(5, 5)
        self.SetSizer(self.bck)
        label = "Right-click on 2D plot for slicer options"
        title = wx.StaticText(self, -1, label, style=wx.ALIGN_LEFT)
        self.bck.Add(title, (0, 0), (1, 2),
                     flag=wx.LEFT|wx.ALIGN_CENTER_VERTICAL, border=15)
        # Bindings
        self.parent.Bind(EVT_SLICER, self.onEVT_SLICER)
        self.parent.Bind(EVT_SLICER_PARS, self.onParamChange)

    def onEVT_SLICER(self, event):
        """
        Process EVT_SLICER events
        When the slicer changes, update the panel
        
        :param event: EVT_SLICER event
        """
        event.Skip()
        if event.obj_class == None:
            self.set_slicer(None, None)
        else:
            self.set_slicer(event.type, event.params)
        
    def set_slicer(self, type, params):
        """
        Rebuild the panel
        """
        self.bck.Clear(True)  
        self.type = type  
        if type == None:
            label = "Right-click on 2D plot for slicer options"
            title = wx.StaticText(self, -1, label, style=wx.ALIGN_LEFT)
            self.bck.Add(title, (0, 0), (1, 2), 
                         flag=wx.LEFT|wx.ALIGN_CENTER_VERTICAL, border=15)
        else:
            title = wx.StaticText(self, -1, 
                                  "Slicer Parameters", style=wx.ALIGN_LEFT)
            self.bck.Add(title, (0, 0), (1, 2),
                         flag=wx.LEFT|wx.ALIGN_CENTER_VERTICAL, border=15)
            ix = 0
            iy = 0
            self.parameters = []
            keys = params.keys()
            keys.sort()
            for item in keys:
                iy += 1
                ix = 0
                if not item in ["count", "errors"]:
                    text = wx.StaticText(self, -1, item, style=wx.ALIGN_LEFT)
                    self.bck.Add(text, (iy, ix), (1, 1), 
                                 wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
                    ctl = wx.TextCtrl(self, -1, size=(80, 20),
                                      style=wx.TE_PROCESS_ENTER)
                    hint_msg = "Modify the value of %s to change" % item
                    hint_msg += " the 2D slicer"
                    ctl.SetToolTipString(hint_msg)
                    ix = 1
                    ctl.SetValue(format_number(str(params[item])))
                    self.Bind(wx.EVT_TEXT_ENTER, self.onTextEnter)
                    self.parameters.append([item, ctl])
                    self.bck.Add(ctl, (iy, ix), (1, 1), 
                                 wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                    ix = 3
                    self.bck.Add((20, 20), (iy, ix), (1, 1), 
                                 wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                else:
                    text = wx.StaticText(self, -1, item + " : ", 
                                         style=wx.ALIGN_LEFT)
                    self.bck.Add(text, (iy, ix), (1, 1), 
                                 wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
                    ctl = wx.StaticText(self, -1, 
                                    format_number(str(params[item])), 
                                    style=wx.ALIGN_LEFT)
                    ix = 1
                    self.bck.Add(ctl, (iy, ix), (1, 1), 
                                 wx.EXPAND|wx.ADJUST_MINSIZE, 0)
            iy += 1
            ix = 1
            self.bck.Add((20, 20), (iy, ix), (1, 1), 
                         wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        self.bck.Layout()
        self.bck.Fit(self)
        self.parent.GetSizer().Layout()

    def onParamChange(self, evt):
        """
        receive an event end reset value text fields
        inside self.parameters
        """
        evt.Skip()
        if evt.type == "UPDATE":
            for item in self.parameters:              
                if item[0] in evt.params:
                    item[1].SetValue("%-5.3g" % evt.params[item[0]])
                    item[1].Refresh()
        
    def onTextEnter(self, evt): 
        """
        Parameters have changed
        """ 
        params = {}
        has_error = False
        for item in self.parameters:
            try:
                params[item[0]] = float(item[1].GetValue())
                item[1].SetBackgroundColour(
                        wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
                item[1].Refresh()
            except:
                has_error = True
                item[1].SetBackgroundColour("pink")
                item[1].Refresh()

        if has_error == False:
            # Post parameter event
            ##parent hier is plotter2D
            event = SlicerParameterEvent(type=self.type, params=params)
            wx.PostEvent(self.parent, event)
        