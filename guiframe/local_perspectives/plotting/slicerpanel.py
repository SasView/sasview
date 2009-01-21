"""
    Panel class to show the slicer parameters 
"""

import wx
import wx.lib.newevent
from copy import deepcopy

(SlicerEvent, EVT_SLICER)   = wx.lib.newevent.NewEvent()
(SlicerParameterEvent, EVT_SLICER_PARS)   = wx.lib.newevent.NewEvent()

class SlicerPanel(wx.Panel):
    #TODO: show units
    #TODO: order parameters properly
     ## Internal name for the AUI manager
    window_name = "Slicer panel"
    ## Title to appear on top of the window
    window_caption = "Slicer Panel"
    
    CENTER_PANE = False
    
    def __init__(self, parent,id=-1,type=None, params={}, *args, **kwargs):
        wx.Panel.__init__(self, parent,id, *args, **kwargs)
        print "panel created"
        self.params = params
        self.parent = parent
        self.type = type
        self.listeners = []
        self.parameters = []
        self.bck = wx.GridBagSizer(5,5)
        self.SetSizer(self.bck)
        if type==None and params==None:      
            title = wx.StaticText(self, -1, "Right-click on 2D plot for slicer options", style=wx.ALIGN_LEFT)
            self.bck.Add(title, (0,0), (1,2), flag=wx.LEFT|wx.ALIGN_CENTER_VERTICAL, border=15)
        else:
            self.set_slicer( type, params)
        # Bindings
        #self.parent.Bind(EVT_SLICER, self.onEVT_SLICER)
        self.parent.Bind(EVT_SLICER, self.onEVT_SLICER)
        self.parent.Bind(EVT_SLICER_PARS, self.onParamChange)

    def onEVT_SLICER(self, event):
        """
            Process EVT_SLICER events
            When the slicer changes, update the panel
            
            @param event: EVT_SLICER event
        """
        print "went here panel"
        event.Skip()
        if event.obj_class==None:
            self.set_slicer(None, None)
            
        else:
            print "when here not empty event",event.type, event.params
            self.set_slicer(event.type, event.params)
        
    def set_slicer(self, type, params):
        """
            Rebuild the panel
        """
        self.bck.Clear(True)  
        self.type = type  
        print "in set slicer", type, params
        if type==None:
            title = wx.StaticText(self, -1, "Right-click on 2D plot for slicer options", style=wx.ALIGN_LEFT)
            self.bck.Add(title, (0,0), (1,2), flag=wx.LEFT|wx.ALIGN_CENTER_VERTICAL, border=15)

        else:
            title = wx.StaticText(self, -1, "Slicer Parameters", style=wx.ALIGN_LEFT)
            self.bck.Add(title, (0,0), (1,2), flag=wx.LEFT|wx.ALIGN_CENTER_VERTICAL, border=15)
            
            n = 1
            self.parameters = []
            #params = slicer.get_params()
            keys = params.keys()
            keys.sort()
            
            for item in keys:
                n += 1
                text = wx.StaticText(self, -1, item, style=wx.ALIGN_LEFT)
                self.bck.Add(text, (n-1,0), flag = wx.LEFT|wx.ALIGN_CENTER_VERTICAL, border = 15)
                ctl = wx.TextCtrl(self, -1, size=(80,20), style=wx.TE_PROCESS_ENTER)
                
                ctl.SetToolTipString("Modify the value of %s to change the 2D slicer" % item)
                
                
                ctl.SetValue(str(params[item]))
                self.Bind(wx.EVT_TEXT_ENTER, self.onTextEnter)
                ctl.Bind(wx.EVT_KILL_FOCUS, self.onTextEnter)
                self.parameters.append([item, ctl])
                self.bck.Add(ctl, (n-1,1), flag=wx.TOP|wx.BOTTOM, border = 0)

        self.bck.Layout()
        self.bck.Fit(self)
        self.parent.GetSizer().Layout()
    def onParamChange(self, evt):
        print "parameters changed"
        evt.Skip()
        #if evt.type == "UPDATE":
        for item in self.parameters:              
            if item[0] in evt.params:
                item[1].SetValue("%-5.3g" %evt.params[item[0]])
                item[1].Refresh()
        

    def old_onParamChange(self, evt):
        evt.Skip()
        if evt.type == "UPDATE":
            for item in self.parameters:              
                if item[0] in evt.params:
                    item[1].SetValue("%-5.3g" %evt.params[item[0]])
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

        if has_error==False:
            # Post parameter event
            event = SlicerParameterEvent(type=self.type, params=params)
            wx.PostEvent(self.parent, event)
        