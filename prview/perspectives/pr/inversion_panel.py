#!/usr/bin/env python

# version
__id__ = "$Id: aboutdialog.py 1193 2007-05-03 17:29:59Z dmitriy $"
__revision__ = "$Revision: 1193 $"

import wx
from sans.guicomm.events import StatusEvent    

class InversionDlg(wx.Dialog):
    def __init__(self, parent, id, title, plots, file=False, pars=True):
        
        # Estimate size
        nplots = len(plots)
        # y size for data set only
        ysize  = 110 + nplots*20
        # y size including parameters
        if pars:
            ysize  += 90
        
        wx.Dialog.__init__(self, parent, id, title, size=(250, ysize))
        self.SetTitle(title)

        # Data set
        self.datasets = InversionPanel(self, -1, plots)
        vbox = wx.BoxSizer(wx.VERTICAL)

        vbox.Add(self.datasets)

        # Parameters
        self.pars_flag = False
        if pars==True:
            self.pars_flag = True
            self.pars = ParsDialog(self, -1, file=file)
            vbox.Add(self.pars)

        static_line = wx.StaticLine(self, -1)
        vbox.Add(static_line, 0, wx.EXPAND, 0)
        
        button_OK = wx.Button(self, wx.ID_OK, "OK")
        button_Cancel = wx.Button(self, wx.ID_CANCEL, "Cancel")
        
        sizer_button = wx.BoxSizer(wx.HORIZONTAL)
        sizer_button.Add((20, 20), 1, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        sizer_button.Add(button_OK, 0, wx.LEFT|wx.ADJUST_MINSIZE, 10)
        sizer_button.Add(button_Cancel, 0, wx.LEFT|wx.RIGHT|wx.ADJUST_MINSIZE, 10)        
        vbox.Add(sizer_button, 0, wx.EXPAND|wx.BOTTOM|wx.TOP, 10)

        self.SetSizer(vbox)
        self.SetAutoLayout(True)
        
        self.Layout()
        self.Centre()

    def get_content(self):
        dataset = self.datasets.get_selected()
        if self.pars_flag:
            nfunc, alpha, dmax, file = self.pars.getContent()
            return dataset, nfunc, alpha, dmax
        else:
            return dataset
    
    def set_content(self, dataset, nfunc, alpha, dmax):
        if not dataset==None and dataset in self.datasets.radio_buttons.keys():
            self.datasets.radio_buttons[dataset].SetValue(True)
        if self.pars_flag:
            self.pars.setContent(nfunc, alpha, dmax, None)

class InversionPanel(wx.Panel):
    
    def __init__(self, parent, id = -1, plots = None, **kwargs):
        wx.Panel.__init__(self, parent, id = id, **kwargs)
        
        self.plots = plots
        self.radio_buttons = {}
        
        self._do_layout()
        
    def _do_layout(self):
        panel = wx.Panel(self, -1)
        vbox = wx.BoxSizer(wx.VERTICAL)

        ysize = 30+20*len(self.plots)
        wx.StaticBox(panel, -1, 'Choose a data set', (5, 5), (230, ysize))
        ypos = 30
        self.radio_buttons = {}
        for item in self.plots.keys():
            self.radio_buttons[self.plots[item].name] = wx.RadioButton(panel, -1, self.plots[item].name, (15, ypos))
            ypos += 20
        
        vbox.Add(panel)

        self.SetSizer(vbox)
        
    def get_selected(self):
        for item in self.radio_buttons:
            if self.radio_buttons[item].GetValue():
                return item
        return None

class InversionControl(wx.Panel):
    window_name = 'pr_control'
    window_caption = "P(r) control panel"
    CENTER_PANE = True
    
    # Figure of merit parameters [default]
    oscillation_max = 1.5
    
    def __init__(self, parent, id = -1, plots = None, **kwargs):
        wx.Panel.__init__(self, parent, id = id, **kwargs)
        
        self.plots = plots
        self.radio_buttons = {}
        
        ## Data file TextCtrl
        self.data_file = None
        self.plot_data = None
        self.nfunc_ctl = None
        self.alpha_ctl = None
        self.dmax_ctl  = None
        self.time_ctl  = None
        self.chi2_ctl  = None
        self.osc_ctl  = None
        self.file_radio = None
        self.plot_radio = None
        
        ## Estimates
        self.alpha_estimate_ctl = None
        
        ## Data manager
        self.manager   = None
        
        self._do_layout()
        
    def __setattr__(self, name, value):
        """
            Allow direct hooks to text boxes
        """
        if name=='nfunc':
            self.nfunc_ctl.SetValue(str(value))
        elif name=='d_max':
            self.dmax_ctl.SetValue(str(value))
        elif name=='alpha':
            self.alpha_ctl.SetValue(str(value))
        elif name=='chi2':
            self.chi2_ctl.SetValue("%-5.3g" % value)
        elif name=='elapsed':
            self.time_ctl.SetValue("%-5.2g" % value)
        elif name=='oscillation':
            self.osc_ctl.SetValue("%-5.2g" % value)
        elif name=='alpha_estimate':
            self.alpha_estimate_ctl.SetValue("%-5.2g" % value)
        elif name=='plotname':
            self.plot_data.SetValue(str(value))
            self.plot_radio.SetValue(True)
            self._on_pars_changed(None)
        else:
            wx.Panel.__setattr__(self, name, value)
        
    def __getattr__(self, name):
        """
            Allow direct hooks to text boxes
        """
        if name=='nfunc':
            int(self.nfunc_ctl.GetValue())
        elif name=='d_max':
            self.dmax_ctl.GetValue()
        elif name=='alpha':
            self.alpha_ctl.GetValue()
        elif name=='chi2':
            self.chi2_ctl.GetValue()
        elif name=='elapsed':
            self.time_ctl.GetValue()
        elif name=='oscillation':
            self.osc_ctl.GetValue()
        elif name=='alpha_estimate':
            self.alpha_estimate_ctl.GetValue()
        elif name=='plotname':
            self.plot_data.GetValue()
        else:
            wx.Panel.__getattr__(self, name)
        
    def set_manager(self, manager):
        self.manager = manager
        # Get data
        
        # Push data to form
        
        
    def _do_layout(self):
        #panel = wx.Panel(self, -1)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # ----- I(q) data -----
        databox = wx.StaticBox(self, -1, "I(q) data")
        
        boxsizer1 = wx.StaticBoxSizer(databox, wx.VERTICAL)
        boxsizer1.SetMinSize((320,50))
        pars_sizer = wx.GridBagSizer(5,5)

        iy = 0
        self.file_radio = wx.RadioButton(self, -1, "File data:")
        self.data_file = wx.TextCtrl(self, -1, size=(100,20))
        self.data_file.SetEditable(False)
        self.data_file.SetValue("")
        id = wx.NewId()
        choose_button = wx.Button(self, id, "Choose file")
        self.Bind(wx.EVT_BUTTON, self._change_file, id = id)   
        pars_sizer.Add(self.file_radio, (iy,0), (1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        pars_sizer.Add(self.data_file, (iy,1), (1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        pars_sizer.Add(choose_button, (iy,3), (1,1), wx.RIGHT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        
        iy += 1
        self.plot_radio = wx.RadioButton(self, -1, "Plot data:")
        self.plot_data = wx.TextCtrl(self, -1, size=(100,20))
        self.plot_data.SetEditable(False)
        pars_sizer.Add(self.plot_radio, (iy,0), (1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        pars_sizer.Add(self.plot_data, (iy,1), (1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        
        boxsizer1.Add(pars_sizer, 0, wx.EXPAND)
        vbox.Add(boxsizer1)

        # ----- Parameters -----
        parsbox = wx.StaticBox(self, -1, "Parameters")
        boxsizer2 = wx.StaticBoxSizer(parsbox, wx.VERTICAL)
        boxsizer2.SetMinSize((320,50))
        
        label_nfunc = wx.StaticText(self, -1, "Number of terms")
        label_nfunc.SetMinSize((120,20))
        label_alpha = wx.StaticText(self, -1, "Regularization constant")
        label_dmax  = wx.StaticText(self, -1, "Max distance [A]")
        label_sugg  = wx.StaticText(self, -1, "Suggested value")
        
        self.nfunc_ctl = wx.TextCtrl(self, -1, size=(60,20))
        self.alpha_ctl = wx.TextCtrl(self, -1, size=(60,20))
        self.dmax_ctl  = wx.TextCtrl(self, -1, size=(60,20))
        self.alpha_estimate_ctl  = wx.TextCtrl(self, -1, size=(60,20))
        self.alpha_estimate_ctl.Enable(False)
        
        # EVT_TEXT would trigger an event for each character entered
        self.nfunc_ctl.Bind(wx.EVT_KILL_FOCUS, self._on_pars_changed)
        #self.alpha_ctl.Bind(wx.EVT_KILL_FOCUS, self._on_pars_changed)
        self.dmax_ctl.Bind(wx.EVT_KILL_FOCUS, self._on_pars_changed)
        self.Bind(wx.EVT_TEXT_ENTER, self._on_pars_changed)
        
        sizer_params = wx.GridBagSizer(5,5)

        iy = 0
        sizer_params.Add(label_sugg, (iy,2), (1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        iy += 1
        sizer_params.Add(label_nfunc, (iy,0), (1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        sizer_params.Add(self.nfunc_ctl,   (iy,1), (1,1), wx.RIGHT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        iy += 1
        sizer_params.Add(label_alpha, (iy,0), (1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        sizer_params.Add(self.alpha_ctl,   (iy,1), (1,1), wx.RIGHT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        sizer_params.Add(self.alpha_estimate_ctl,   (iy,2), (1,1), wx.RIGHT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        iy += 1
        sizer_params.Add(label_dmax, (iy,0), (1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        sizer_params.Add(self.dmax_ctl,   (iy,1), (1,1), wx.RIGHT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)

        boxsizer2.Add(sizer_params, 0)
        vbox.Add(boxsizer2)

        # ----- Results -----
        resbox = wx.StaticBox(self, -1, "Outputs")
        ressizer = wx.StaticBoxSizer(resbox, wx.VERTICAL)
        ressizer.SetMinSize((320,50))
        
        label_time = wx.StaticText(self, -1, "Computation time")
        label_time_unit = wx.StaticText(self, -1, "secs")
        label_time.SetMinSize((120,20))
        label_chi2 = wx.StaticText(self, -1, "Chi2/dof")
        label_osc = wx.StaticText(self, -1, "Oscillations")
        
        self.time_ctl = wx.TextCtrl(self, -1, size=(60,20))
        self.time_ctl.SetEditable(False)
        self.chi2_ctl = wx.TextCtrl(self, -1, size=(60,20))
        self.chi2_ctl.SetEditable(False)
        self.osc_ctl = wx.TextCtrl(self, -1, size=(60,20))
        self.osc_ctl.SetEditable(False)
        
        sizer_res = wx.GridBagSizer(5,5)

        iy = 0
        sizer_res.Add(label_time, (iy,0), (1,1), wx.LEFT|wx.EXPAND, 15)
        sizer_res.Add(self.time_ctl,   (iy,1), (1,1), wx.RIGHT|wx.EXPAND, 15)
        sizer_res.Add(label_time_unit,   (iy,2), (1,1), wx.RIGHT|wx.EXPAND, 15)
        iy += 1
        sizer_res.Add(label_chi2, (iy,0), (1,1), wx.LEFT|wx.EXPAND, 15)
        sizer_res.Add(self.chi2_ctl,   (iy,1), (1,1), wx.RIGHT|wx.EXPAND, 15)
        iy += 1
        sizer_res.Add(label_osc, (iy,0), (1,1), wx.LEFT|wx.EXPAND, 15)
        sizer_res.Add(self.osc_ctl,   (iy,1), (1,1), wx.RIGHT|wx.EXPAND, 15)

        ressizer.Add(sizer_res, 0)
        vbox.Add(ressizer)

        # ----- Buttons -----
        static_line = wx.StaticLine(self, -1)
        vbox.Add(static_line, 0, wx.EXPAND|wx.TOP, 10)
        
        id = wx.NewId()
        button_OK = wx.Button(self, id, "Compute")
        self.Bind(wx.EVT_BUTTON, self._on_invert, id = id)   
        #button_Cancel = wx.Button(self, wx.ID_CANCEL, "Cancel")
        
        sizer_button = wx.BoxSizer(wx.HORIZONTAL)
        sizer_button.Add((20, 20), 1, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        sizer_button.Add(button_OK, 0, wx.LEFT|wx.ADJUST_MINSIZE, 10)
        #sizer_button.Add(button_Cancel, 0, wx.LEFT|wx.RIGHT|wx.ADJUST_MINSIZE, 10)        
        vbox.Add(sizer_button, 0, wx.EXPAND|wx.BOTTOM|wx.TOP, 10)


        self.SetSizer(vbox)
        
    def _on_pars_changed(self, evt):
        """
            Called when an input parameter has changed
            We will estimate the alpha parameter behind the
            scenes. 
        """
        flag, alpha, dmax, nfunc = self._read_pars()
        
        # If the pars are valid, estimate alpha
        if flag:
            if self.plot_radio.GetValue():
                dataset = self.plot_data.GetValue()
                self.manager.estimate_plot_inversion(alpha=alpha, nfunc=nfunc, 
                                                     d_max=dmax)
            else:
                path = self.data_file.GetValue()
                self.manager.estimate_file_inversion(alpha=alpha, nfunc=nfunc, 
                                                     d_max=dmax, path=path)
        
        
    def _read_pars(self):    
        alpha = 0
        nfunc = 5
        dmax  = 120
        
        flag = True
        
        # Read alpha
        try:
            alpha = float(self.alpha_ctl.GetValue())
            self.alpha_ctl.SetBackgroundColour(wx.WHITE)
            self.alpha_ctl.Refresh()
        except:
            flag = False
            self.alpha_ctl.SetBackgroundColour("pink")
            self.alpha_ctl.Refresh()
        
        # Read d_max    
        try:
            dmax = float(self.dmax_ctl.GetValue())
            self.dmax_ctl.SetBackgroundColour(wx.WHITE)
            self.dmax_ctl.Refresh()
        except:
            flag = False
            self.dmax_ctl.SetBackgroundColour("pink")
            self.dmax_ctl.Refresh()
            
        # Read nfunc
        try:
            nfunc = int(self.nfunc_ctl.GetValue())
            self.nfunc_ctl.SetBackgroundColour(wx.WHITE)
            self.nfunc_ctl.Refresh()
        except:
            flag = False
            self.nfunc_ctl.SetBackgroundColour("pink")
            self.nfunc_ctl.Refresh()
        
        return flag, alpha, dmax, nfunc
    
    def _on_invert(self, evt):
        """
            Perform inversion
            @param silent: when True, there will be no output for the user 
        """
        # Get the data from the form
        # Push it to the manager
        
        flag, alpha, dmax, nfunc = self._read_pars()
        
        if flag:
            if self.plot_radio.GetValue():
                dataset = self.plot_data.GetValue()
                self.manager.setup_plot_inversion(alpha=alpha, nfunc=nfunc, 
                                                  d_max=dmax)
            else:
                path = self.data_file.GetValue()
                self.manager.setup_file_inversion(alpha=alpha, nfunc=nfunc, 
                                                  d_max=dmax, path=path)
                
        else:
            message = "The P(r) form contains invalid values: please submit it again."
            wx.PostEvent(self.parent, StatusEvent(status=message))
        
    def _change_file(self, evt):
        """
            Choose a new input file for I(q)
        """
        import os
        if not self.manager==None:
            path = self.manager.choose_file()
            
            if path and os.path.isfile(path):
                self.data_file.SetValue(str(path))
                self.file_radio.SetValue(True)
                self._on_pars_changed(None)
        

class ParsDialog(wx.Panel):
    """
        Dialog box to let the user edit detector settings
    """
    
    def __init__(self, parent, id = id, file=True, **kwargs):

        wx.Panel.__init__(self, parent, id = id, **kwargs)
        self.file = file
        
        self.label_nfunc = wx.StaticText(self, -1, "Number of terms")
        self.label_alpha = wx.StaticText(self, -1, "Regularization constant")
        self.label_dmax  = wx.StaticText(self, -1, "Max distance [A]")
        
        # Npts, q max
        self.nfunc_ctl = wx.TextCtrl(self, -1, size=(60,20))
        self.alpha_ctl = wx.TextCtrl(self, -1, size=(60,20))
        self.dmax_ctl  = wx.TextCtrl(self, -1, size=(60,20))

        self.label_file = None
        self.file_ctl   = None

        self.static_line_3 = wx.StaticLine(self, -1)
        
        

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
        if self.file:
            self.file_ctl.SetValue(str(file))

    def getContent(self):
        nfunc = int(self.nfunc_ctl.GetValue())
        alpha = float(self.alpha_ctl.GetValue())
        dmax = float(self.dmax_ctl.GetValue())
        file = None
        if self.file:
            file = self.file_ctl.GetValue()
        return nfunc, alpha, dmax, file


    def __do_layout(self):
        sizer_main = wx.BoxSizer(wx.VERTICAL)
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
        if self.file:
            self.label_file  = wx.StaticText(self, -1, "Input file")
            self.file_ctl  = wx.TextCtrl(self, -1, size=(120,20))
            sizer_params.Add(self.label_file, (iy,0), (1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
            sizer_params.Add(self.file_ctl,   (iy,1), (1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)

        sizer_main.Add(sizer_params, 0, wx.EXPAND|wx.ALL, 10)
        
        
        if self.file:
            sizer_button = wx.BoxSizer(wx.HORIZONTAL)
            self.button_load = wx.Button(self, 1, "Choose file")
            self.Bind(wx.EVT_BUTTON, self._load_file, id = 1)        
            sizer_button.Add(self.button_load, 0, wx.LEFT|wx.ADJUST_MINSIZE, 10)
        
        
            sizer_main.Add(sizer_button, 0, wx.EXPAND|wx.BOTTOM|wx.TOP, 10)
        self.SetAutoLayout(True)
        self.SetSizer(sizer_main)
        self.Layout()
        self.Centre()
        # end wxGlade


# end of class DialogAbout

##### testing code ############################################################
class TestPlot:
    def __init__(self, text):
        self.name = text
    
class MyApp(wx.App):
    def OnInit(self):
        wx.InitAllImageHandlers()
        plots = {}
        plots['a'] = TestPlot("data 1")
        plots['b'] = TestPlot("data 2")
        #plots['c'] = TestPlot("data 3")
        #plots['d'] = TestPlot("data 1")
        #plots['e'] = TestPlot("data 2")
        #plots['f'] = TestPlot("data 3")
        dialog = InversionDlg(None, -1, "P(r) parameters", plots)
        if dialog.ShowModal() == wx.ID_OK:
            print dialog.get_content()
        dialog.Destroy()
        
        return 1

# end of class MyApp

if __name__ == "__main__":
    app = MyApp(0)
    app.MainLoop()
    
##### end of testing code #####################################################    
