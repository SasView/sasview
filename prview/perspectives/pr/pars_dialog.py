#!/usr/bin/env python

# version
__id__ = "$Id: aboutdialog.py 1193 2007-05-03 17:29:59Z dmitriy $"
__revision__ = "$Revision: 1193 $"

import wx


class ParsDialog(wx.Dialog):
    """
        Dialog box to let the user edit detector settings
    """
    
    def __init__(self, *args, **kwds):

        kwds["style"] = wx.DEFAULT_DIALOG_STYLE
        wx.Dialog.__init__(self, *args, **kwds)
        
        self.label_nfunc = wx.StaticText(self, -1, "Number of terms")
        self.label_alpha = wx.StaticText(self, -1, "Regularization constant")
        self.label_dmax  = wx.StaticText(self, -1, "Max distance [A]")
        self.label_file  = wx.StaticText(self, -1, "Input file")
        
        # Npts, q max
        self.nfunc_ctl = wx.TextCtrl(self, -1, size=(60,20))
        self.alpha_ctl = wx.TextCtrl(self, -1, size=(60,20))
        self.dmax_ctl  = wx.TextCtrl(self, -1, size=(60,20))
        self.file_ctl  = wx.TextCtrl(self, -1, size=(120,20))

        self.static_line_3 = wx.StaticLine(self, -1)
        
        
        self.button_OK = wx.Button(self, wx.ID_OK, "OK")
        self.Bind(wx.EVT_BUTTON, self.checkValues, self.button_OK)
        
        self.button_Cancel = wx.Button(self, wx.ID_CANCEL, "Cancel")
        
        self.button_load = wx.Button(self, 1, "Choose file")
        self.Bind(wx.EVT_BUTTON, self._load_file, id = 1)        

        self.__set_properties()
        self.__do_layout()

        self.Fit()
        
    def _load_file(self, evt):
        import os
        path = None
        dlg = wx.FileDialog(self, "Choose a file", os.getcwd(), "", "*.txt", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            mypath = os.path.basename(path)
        dlg.Destroy()
        
        if path and os.path.isfile(path):
            self.file_ctl.SetValue(str(path))

        
    def checkValues(self, event):
        flag = True
        try:
            float(self.alpha_ctl.GetValue())
            self.alpha_ctl.SetBackgroundColour(wx.WHITE)
            self.alpha_ctl.Refresh()
        except:
            flag = False
            self.alpha_ctl.SetBackgroundColour("pink")
            self.alpha_ctl.Refresh()
            
        try:
            float(self.dmax_ctl.GetValue())
            self.dmax_ctl.SetBackgroundColour(wx.WHITE)
            self.dmax_ctl.Refresh()
        except:
            flag = False
            self.dmax_ctl.SetBackgroundColour("pink")
            self.dmax_ctl.Refresh()
            
        try:
            int(self.nfunc_ctl.GetValue())
            self.nfunc_ctl.SetBackgroundColour(wx.WHITE)
            self.nfunc_ctl.Refresh()
        except:
            flag = False
            self.nfunc_ctl.SetBackgroundColour("pink")
            self.nfunc_ctl.Refresh()
        
        if flag:
            event.Skip(True)
    
    def setContent(self, nfunc, alpha, dmax, file):
        self.nfunc_ctl.SetValue(str(nfunc))
        self.alpha_ctl.SetValue(str(alpha))
        self.dmax_ctl.SetValue(str(dmax))
        self.file_ctl.SetValue(str(file))

    def getContent(self):
        nfunc = int(self.nfunc_ctl.GetValue())
        alpha = float(self.alpha_ctl.GetValue())
        dmax = float(self.dmax_ctl.GetValue())
        file = self.file_ctl.GetValue()
        return nfunc, alpha, dmax, file

    def __set_properties(self):
        self.SetTitle("P(r) inversion parameters")
        self.SetSize((600, 595))

    def __do_layout(self):
        sizer_main = wx.BoxSizer(wx.VERTICAL)
        sizer_button = wx.BoxSizer(wx.HORIZONTAL)
        sizer_params = wx.GridBagSizer(5,5)

        iy = 0
        sizer_params.Add(self.label_nfunc, (iy,0), (1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        sizer_params.Add(self.nfunc_ctl,   (iy,1), (1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        iy += 1
        sizer_params.Add(self.label_alpha, (iy,0), (1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        sizer_params.Add(self.alpha_ctl,   (iy,1), (1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        iy += 1
        sizer_params.Add(self.label_dmax, (iy,0), (1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        sizer_params.Add(self.dmax_ctl,   (iy,1), (1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        iy += 1
        sizer_params.Add(self.label_file, (iy,0), (1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        sizer_params.Add(self.file_ctl,   (iy,1), (1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)

        sizer_main.Add(sizer_params, 0, wx.EXPAND|wx.ALL, 10)
        sizer_main.Add(self.static_line_3, 0, wx.EXPAND, 0)
        
        
        sizer_button.Add((20, 20), 1, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        sizer_button.Add(self.button_load, 0, wx.LEFT|wx.ADJUST_MINSIZE, 10)
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
        dialog = ParsDialog(None, -1, "")
        self.SetTopWindow(dialog)
        dialog.setContent(10, 0.05)
        nfunc, alpha = dialog.getContent()
        print nfunc, alpha
        dialog.Destroy()
        return 1

# end of class MyApp

if __name__ == "__main__":
    app = MyApp(0)
    app.MainLoop()
    
##### end of testing code #####################################################    
