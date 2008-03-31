#!/usr/bin/python

# fitDialog.py

import wx
from sans.guitools.PlotPanel import PlotPanel

class LinearFit(wx.Dialog):
    def __init__(self, parent, id, title):
        wx.Dialog.__init__(self, parent, id, title, size=(500, 300))
        """
            for the fit window
        """
        self.parent = parent
        panel = wx.Panel(self, -1, style=wx.SIMPLE_BORDER)   
        vbox  = wx.BoxSizer(wx.VERTICAL)
        sizer = wx.GridBagSizer(5,0)
        vbox.Add(panel, 1, wx.EXPAND | wx.ALL)
 
        self.tcA = wx.TextCtrl(panel, -1,style=wx.SIMPLE_BORDER)
        self.tcErrA = wx.TextCtrl(panel, -1,style=wx.SIMPLE_BORDER)
        self.tcB = wx.TextCtrl(panel, -1,style=wx.SIMPLE_BORDER)
        self.tcErrB = wx.TextCtrl(panel, -1,style=wx.SIMPLE_BORDER)
        self.tcChi = wx.TextCtrl(panel, -1,style=wx.SIMPLE_BORDER)
        self.tcXmin = wx.TextCtrl(panel,-1,style=wx.SIMPLE_BORDER)
        self.tcXmax = wx.TextCtrl(panel,-1,style=wx.SIMPLE_BORDER)
        self.btFit =wx.Button(panel,-1,'Fit' )
        btClose =wx.Button(panel, wx.ID_CANCEL,'Close' )
        
        ix = 1
        iy = 1
        sizer.Add(wx.StaticText(panel, -1, 'y = Ax +B'),(iy, ix))
        ix = 1
        iy += 2
        sizer.Add(wx.StaticText(panel, -1, 'Param A'),(iy, ix))
        ix += 1
        sizer.Add(self.tcA, (iy, ix))
        ix += 1
        sizer.Add(wx.StaticText(panel, -1, '+/-'),(iy, ix))
        ix += 1
        sizer.Add(self.tcErrA, (iy, ix))
        #self.tcErrA.Bind(wx.EVT_KILL_FOCUS, self._onTextEnter)
        iy += 1
        ix = 1
        sizer.Add(wx.StaticText(panel, -1, 'Param B'),(iy, ix))
        ix += 1
        sizer.Add(self.tcB, (iy, ix))
        #self.tcB.Bind(wx.EVT_KILL_FOCUS, self._onTextEnter)
        ix += 1
        # sizer.Add(wx.StaticText(panel, -1, '+/-'),(iy, ix))
        ix += 1
        sizer.Add(self.tcErrB, (iy, ix))
        self.tcErrB.Bind(wx.EVT_KILL_FOCUS, self._onTextEnter)
        iy += 1
        ix = 1
        sizer.Add(wx.StaticText(panel, -1, 'Chi ^{2}'),(iy, ix))
        ix += 1
        sizer.Add(self.tcChi, (iy, ix))
        #self.tcChi.Bind(wx.EVT_KILL_FOCUS, self._onTextEnter)
        iy += 1
        ix = 1
        sizer.Add(wx.StaticText(panel, -1, 'Xmin'),(iy, ix))
        ix += 2
        sizer.Add(wx.StaticText(panel, -1, 'Xmax'),(iy, ix))
        iy += 1
        ix = 1
        sizer.Add(self.tcXmin, (iy, ix))
        #self.tcXmin.Bind(wx.EVT_KILL_FOCUS, self._onTextEnter)
        ix += 2
        sizer.Add(self.tcXmax, (iy, ix))
        #self.tcXmax.Bind(wx.EVT_KILL_FOCUS, self._onTextEnter)
        iy += 1
        ix = 1
        sizer.Add(self.btFit, (iy, ix))
        self.tcXmax.Bind(wx.EVT_KILL_FOCUS, self._onFit)
        ix += 2
        sizer.Add(btClose, (iy, ix))
       
        panel.SetSizer(sizer)
        self.SetSizer(vbox)
        self.Centre()
    def _onFit(self ,event):
         param_evt1 = PlotPanel.FunctionFitEvent(\
            Xmin=self._checkVal(self.tcXmin.GetValue()),\
            Xmax=self._checkVal(self.tcXmax.GetValue())                                     )
         wx.PostEvent(self, param_evt1)
    
    def _onsetValues(self,cstA,cstB,errA,errB,Chi):
        
         self.tcA.SetValue(cstA)
         self.tcB.SetValue(cstB)
         self.tcErrA.SetValue(cstB)
         self.tcErrB.SetValue(cstA)
         self.tcChi.SetValue(Chi)
    def _getXrange(self):
        if self.tcXmin.GetValue() and self.tcXmax.GetValue():
            return float(),float(self.tcXmax.GetValue())
        else:
            return None, None
    def _checkVal(self,value):
        """
                Ensure that fields parameter contains a value 
                before sending to fit in Plotter1D
        """
        try:
            param = float(value)
        except:
            param = None
        return param
if __name__ == "__main__": 
    app = wx.App()
    dialog=LinearFit(None, -1, 'Fitting')
    dialog.ShowModal()
    app.MainLoop()


