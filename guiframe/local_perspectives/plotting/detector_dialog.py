#!/usr/bin/env python

# version
__id__ = "$Id: aboutdialog.py 1193 2007-05-03 17:29:59Z dmitriy $"
__revision__ = "$Revision: 1193 $"

import wx
from sans.guiframe.utils import format_number

class DetectorDialog(wx.Dialog):
    """
        Dialog box to let the user edit detector settings
    """
    
    def __init__(self, *args, **kwds):

        kwds["style"] = wx.DEFAULT_DIALOG_STYLE
        wx.Dialog.__init__(self, *args, **kwds)
        
        self.label_xnpts = wx.StaticText(self, -1, "Detector width in pixels")
        self.label_ynpts = wx.StaticText(self, -1, "Detector Height in pixels")
        self.label_qmax = wx.StaticText(self, -1, "Q max")
        self.label_zmin = wx.StaticText(self, -1, "Min amplitude for color map (optional)")
        self.label_zmax = wx.StaticText(self, -1, "Max amplitude for color map (optional)")
        self.label_beam = wx.StaticText(self, -1, "Beam stop radius in units of q")
        #self.label_sym  = wx.StaticText(self, -1, 'Use 4-fold symmetry')
        
        # Npts, q max
        #self.npts_ctl = wx.TextCtrl(self, -1, size=(60,20))
        #self.qmax_ctl = wx.TextCtrl(self, -1, size=(60,20))
        #self.beam_ctl = wx.TextCtrl(self, -1, size=(60,20))
        self.xnpts_ctl = wx.StaticText(self, -1, "")
        self.ynpts_ctl = wx.StaticText(self, -1, "")
        self.qmax_ctl = wx.StaticText(self, -1, "")
        self.beam_ctl = wx.StaticText(self, -1, "")
        
        self.zmin_ctl = wx.TextCtrl(self, -1, size=(60,20))
        self.zmax_ctl = wx.TextCtrl(self, -1, size=(60,20))
        #self.chk_sym  = wx.CheckBox(self, -1, '')

        self.static_line_3 = wx.StaticLine(self, -1)
        
        
        self.button_OK = wx.Button(self, wx.ID_OK, "OK")
        self.button_Cancel = wx.Button(self, wx.ID_CANCEL, "Cancel")
        self.Bind(wx.EVT_BUTTON, self.checkValues, self.button_OK)

        self.__set_properties()
        self.__do_layout()

        self.Fit()
        
    class Event:
        xnpts = 0
        ynpts = 0
        qpax = 0
        beam = 0
        zmin = 0
        zmax = 0
        sym4 = False
        
    def checkValues(self, event):
        flag = True
        try:
            value=self.zmin_ctl.GetValue()
            if value and float( value)==0.0:
                flag = False
                self.zmin_ctl.SetBackgroundColour("pink")
                self.zmin_ctl.Refresh()
            else:
                self.zmin_ctl.SetBackgroundColour(wx.WHITE)
                self.zmin_ctl.Refresh()
        except:
            flag = False
            self.zmin_ctl.SetBackgroundColour("pink")
            self.zmin_ctl.Refresh()
        try:
            value=self.zmax_ctl.GetValue()
            if value and int(value)==0.0:
                flag = False
                self.zmax_ctl.SetBackgroundColour("pink")
                self.zmax_ctl.Refresh()
            else:
                self.zmax_ctl.SetBackgroundColour(wx.WHITE)
                self.zmax_ctl.Refresh()
        except:
            flag = False
            self.zmax_ctl.SetBackgroundColour("pink")
            self.zmax_ctl.Refresh()
        
        if flag:
            event.Skip(True)
    
    def setContent(self, xnpts,ynpts, qmax, beam,zmin=None,zmax=None, sym=False):
        self.xnpts_ctl.SetLabel(str(format_number(xnpts)))
        self.ynpts_ctl.SetLabel(str(format_number(ynpts)))
        self.qmax_ctl.SetLabel(str(format_number(qmax)))
        self.beam_ctl.SetLabel(str(format_number(beam)))
        #self.chk_sym.SetValue(sym)
        if zmin !=None:
            self.zmin_ctl.SetValue(str(format_number(zmin)))
        if zmax !=None:
            self.zmax_ctl.SetValue(str(format_number(zmax)))

    def getContent(self):
        event = self.Event()
        #event.npts = int(self.npts_ctl.GetValue())
        #event.qmax = float(self.qmax_ctl.GetValue())
        #event.beam = float(self.beam_ctl.GetValue())
        #event.sym4 = self.chk_sym.GetValue()
        
        t_min = self.zmin_ctl.GetValue()
        t_max = self.zmax_ctl.GetValue()
        v_min = None
        v_max = None
        
        if len(t_min.lstrip())>0:
            try:
                v_min = float(t_min)
            except:
                v_min = None
        
        if len(t_max.lstrip())>0:
            try:
                v_max = float(t_max)
            except:
                v_max = None
        
        event.zmin = v_min
        event.zmax = v_max
        
        return event

    def __set_properties(self):
        self.SetTitle("Detector parameters")
        self.SetSize((600, 595))

    def __do_layout(self):
        sizer_main = wx.BoxSizer(wx.VERTICAL)
        sizer_button = wx.BoxSizer(wx.HORIZONTAL)
        sizer_params = wx.GridBagSizer(5,5)

        iy = 0
        sizer_params.Add(self.label_xnpts, (iy,0), (1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        sizer_params.Add(self.xnpts_ctl,   (iy,1), (1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        iy += 1
        sizer_params.Add(self.label_ynpts, (iy,0), (1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        sizer_params.Add(self.ynpts_ctl,   (iy,1), (1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        iy += 1
        sizer_params.Add(self.label_qmax, (iy,0), (1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        sizer_params.Add(self.qmax_ctl,   (iy,1), (1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        iy += 1
        sizer_params.Add(self.label_beam, (iy,0), (1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        sizer_params.Add(self.beam_ctl,   (iy,1), (1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        iy += 1
        sizer_params.Add(self.label_zmin, (iy,0), (1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        sizer_params.Add(self.zmin_ctl,   (iy,1), (1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        iy += 1
        sizer_params.Add(self.label_zmax, (iy,0), (1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        sizer_params.Add(self.zmax_ctl,   (iy,1), (1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        iy += 1
        #sizer_params.Add(self.label_sym,  (iy,0), (1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        #sizer_params.Add(self.chk_sym,    (iy,1), (1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)

        sizer_main.Add(sizer_params, 0, wx.EXPAND|wx.ALL, 10)
        sizer_main.Add(self.static_line_3, 0, wx.EXPAND, 0)
        
        
        sizer_button.Add((20, 20), 1, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        sizer_button.Add(self.button_OK, 0, wx.LEFT|wx.ADJUST_MINSIZE, 10)
        sizer_button.Add(self.button_Cancel, 0, wx.LEFT|wx.RIGHT|wx.ADJUST_MINSIZE, 10)
        
        
        sizer_main.Add(sizer_button, 0, wx.EXPAND|wx.BOTTOM|wx.TOP, 10)
        self.SetAutoLayout(True)
        self.SetSizer(sizer_main)
        self.Layout()
        self.Centre()
        # end wxGlade


# end of class DialogAbout

##### testing code ############################################################
class MyApp(wx.App):
    def OnInit(self):
        wx.InitAllImageHandlers()
        dialog = DetectorDialog(None, -1, "")
        self.SetTopWindow(dialog)
        dialog.setContent(128, 0.05)
        print dialog.ShowModal()
        evt = dialog.getContent()
        print evt.npts, evt.qmax
        dialog.Destroy()
        return 1

# end of class MyApp

if __name__ == "__main__":
    app = MyApp(0)
    app.MainLoop()
    
##### end of testing code #####################################################    
