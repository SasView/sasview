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
    
    ## Oscillation parameters (sin function = 1.1)
    oscillation_max = 1.5
    
    ## Fraction of P(r) that is positive 
    positive = 1.0
    
    ## Fraction of P(r) that is greater than zero by more than 1 sigma
    pos_err  = 1.0
    
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
        self.label_sugg = None
        self.qmin_ctl = None
        self.qmax_ctl = None
        
        # TextCtrl for fraction of positive P(r)
        self.pos_ctl = None
        
        # TextCtrl for fraction of 1 sigma positive P(r)
        self.pos_err_ctl = None 
        
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
        elif name=='q_min':
            self.qmin_ctl.SetValue("%-5.3g" % value)
        elif name=='q_max':
            self.qmax_ctl.SetValue("%-5.3g" % value)
        elif name=='elapsed':
            self.time_ctl.SetValue("%-5.2g" % value)
        elif name=='oscillation':
            self.osc_ctl.SetValue("%-5.2g" % value)
        elif name=='positive':
            self.pos_ctl.SetValue("%-5.2g" % value)
        elif name=='pos_err':
            self.pos_err_ctl.SetValue("%-5.2g" % value)
        elif name=='alpha_estimate':
            self.alpha_estimate_ctl.SetToolTipString("Click to accept value.")
            self.alpha_estimate_ctl.Enable(True)
            self.alpha_estimate_ctl.SetLabel("%-3.1g" % value)
            #self.alpha_estimate_ctl.Show()
            #self.label_sugg.Show()
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
        elif name=='q_min':
            self.qmin_ctl.GetValue()
        elif name=='q_max':
            self.qmax_ctl.GetValue()
        elif name=='elapsed':
            self.time_ctl.GetValue()
        elif name=='oscillation':
            self.osc_ctl.GetValue()
        elif name=='pos':
            self.pos_ctl.GetValue()
        elif name=='pos_err':
            self.pos_err_ctl.GetValue()
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
        
        explanation  = "P(r) is found by fitting a set of base functions to I(Q). "
        explanation += "The minimization involves a regularization term to ensure "
        explanation += "a smooth P(r). The alpha parameter gives the size of that "  
        explanation += "term. The suggested value is the value above which the "
        explanation += "output P(r) will have only one peak."
        label_explain = wx.StaticText(self, -1, explanation, size=(280,80))
        boxsizer2.Add(label_explain,  wx.LEFT|wx.BOTTOM, 5)
        
        
        
        label_nfunc = wx.StaticText(self, -1, "Number of terms")
        label_nfunc.SetMinSize((120,20))
        label_alpha = wx.StaticText(self, -1, "Regularization constant")
        label_dmax  = wx.StaticText(self, -1, "Max distance [A]")
        self.label_sugg  = wx.StaticText(self, -1, "Suggested value")
        #self.label_sugg.Hide()
        
        self.nfunc_ctl = wx.TextCtrl(self, -1, size=(60,20))
        self.nfunc_ctl.SetToolTipString("Number of terms in the expansion.")
        self.alpha_ctl = wx.TextCtrl(self, -1, size=(60,20))
        self.alpha_ctl.SetToolTipString("Control parameter for the size of the regularization term.")
        self.dmax_ctl  = wx.TextCtrl(self, -1, size=(60,20))
        self.dmax_ctl.SetToolTipString("Maximum distance between any two points in the system.")
        id = wx.NewId()
        self.alpha_estimate_ctl  = wx.Button(self, id, "")
        #self.alpha_estimate_ctl.Hide()
        self.Bind(wx.EVT_BUTTON, self._on_accept_alpha, id = id)   
        self.alpha_estimate_ctl.Enable(False)
        #self.alpha_estimate_ctl.SetBackgroundColour('#ffdf85')
        #self.alpha_estimate_ctl.SetBackgroundColour(self.GetBackgroundColour())
        self.alpha_estimate_ctl.SetToolTipString("Waiting for estimate...")
        
        # EVT_TEXT would trigger an event for each character entered
        self.nfunc_ctl.Bind(wx.EVT_KILL_FOCUS, self._on_pars_changed)
        self.alpha_ctl.Bind(wx.EVT_KILL_FOCUS, self._read_pars)
        self.dmax_ctl.Bind(wx.EVT_KILL_FOCUS, self._on_pars_changed)
        self.Bind(wx.EVT_TEXT_ENTER, self._on_pars_changed)
        
        sizer_params = wx.GridBagSizer(5,5)

        iy = 0
        sizer_params.Add(self.label_sugg,       (iy,2), (1,1), wx.LEFT, 15)
        iy += 1
        sizer_params.Add(label_nfunc,      (iy,0), (1,1), wx.LEFT, 15)
        sizer_params.Add(self.nfunc_ctl,   (iy,1), (1,1), wx.RIGHT, 0)
        iy += 1
        sizer_params.Add(label_alpha,      (iy,0), (1,1), wx.LEFT, 15)
        sizer_params.Add(self.alpha_ctl,   (iy,1), (1,1), wx.RIGHT, 0)
        sizer_params.Add(self.alpha_estimate_ctl, (iy,2), (1,1), wx.LEFT, 15)
        iy += 1
        sizer_params.Add(label_dmax, (iy,0), (1,1), wx.LEFT, 15)
        sizer_params.Add(self.dmax_ctl,   (iy,1), (1,1), wx.RIGHT, 0)

        boxsizer2.Add(sizer_params, 0)
        
        vbox.Add(boxsizer2)

        # ----- Q range -----
        qbox = wx.StaticBox(self, -1, "Q range")
        qboxsizer = wx.StaticBoxSizer(qbox, wx.VERTICAL)
        qboxsizer.SetMinSize((320,20))
        
        sizer_q = wx.GridBagSizer(5,5)

        label_qmin = wx.StaticText(self, -1, "Q min")
        label_qmax = wx.StaticText(self, -1, "Q max")
        self.qmin_ctl = wx.TextCtrl(self, -1, size=(60,20))
        self.qmax_ctl = wx.TextCtrl(self, -1, size=(60,20))
        
        iy = 0
        sizer_q.Add(label_qmin, (iy,0), (1,1), wx.LEFT|wx.EXPAND, 15)
        sizer_q.Add(self.qmin_ctl, (iy,1), (1,1), wx.LEFT|wx.EXPAND, 10)
        sizer_q.Add(label_qmax, (iy,2), (1,1), wx.LEFT|wx.EXPAND, 15)
        sizer_q.Add(self.qmax_ctl, (iy,3), (1,1), wx.LEFT|wx.EXPAND, 10)
        qboxsizer.Add(sizer_q, wx.TOP, 15)
        vbox.Add(qboxsizer)
        
        

        # ----- Results -----
        resbox = wx.StaticBox(self, -1, "Outputs")
        ressizer = wx.StaticBoxSizer(resbox, wx.VERTICAL)
        ressizer.SetMinSize((320,50))
        
        label_time = wx.StaticText(self, -1, "Computation time")
        label_time_unit = wx.StaticText(self, -1, "secs")
        label_time.SetMinSize((120,20))
        label_chi2 = wx.StaticText(self, -1, "Chi2/dof")
        label_osc = wx.StaticText(self, -1, "Oscillations")
        label_pos = wx.StaticText(self, -1, "Positive fraction")
        label_pos_err = wx.StaticText(self, -1, "1-sigma positive fraction")
        
        self.time_ctl = wx.TextCtrl(self, -1, size=(60,20))
        self.time_ctl.SetEditable(False)
        self.time_ctl.SetToolTipString("Computation time for the last inversion, in seconds.")
        
        self.chi2_ctl = wx.TextCtrl(self, -1, size=(60,20))
        self.chi2_ctl.SetEditable(False)
        self.chi2_ctl.SetToolTipString("Chi^2 over degrees of freedom.")
        
        # Oscillation parameter
        self.osc_ctl = wx.TextCtrl(self, -1, size=(60,20))
        self.osc_ctl.SetEditable(False)
        self.osc_ctl.SetToolTipString("Oscillation parameter. P(r) for a sphere has an oscillation parameter of 1.1.")
        
        # Positive fraction figure of merit
        self.pos_ctl = wx.TextCtrl(self, -1, size=(60,20))
        self.pos_ctl.SetEditable(False)
        self.pos_ctl.SetToolTipString("Fraction of P(r) that is positive. Theoretically, P(r) is defined positive.")
        
        # 1-simga positive fraction figure of merit
        self.pos_err_ctl = wx.TextCtrl(self, -1, size=(60,20))
        self.pos_err_ctl.SetEditable(False)
        message  = "Fraction of P(r) that is at least 1 standard deviation greater than zero.\n"
        message += "This figure of merit tells you about the size of the P(r) errors.\n"
        message += "If it is close to 1 and the other figures of merit are bad, consider changing "
        message += "the maximum distance."
        self.pos_err_ctl.SetToolTipString(message)
        
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

        iy += 1
        sizer_res.Add(label_pos, (iy,0), (1,1), wx.LEFT|wx.EXPAND, 15)
        sizer_res.Add(self.pos_ctl,   (iy,1), (1,1), wx.RIGHT|wx.EXPAND, 15)

        iy += 1
        sizer_res.Add(label_pos_err, (iy,0), (1,1), wx.LEFT|wx.EXPAND, 15)
        sizer_res.Add(self.pos_err_ctl,   (iy,1), (1,1), wx.RIGHT|wx.EXPAND, 15)

        ressizer.Add(sizer_res, 0)
        vbox.Add(ressizer)

        # ----- Buttons -----
        static_line = wx.StaticLine(self, -1)
        vbox.Add(static_line, 0, wx.EXPAND|wx.TOP, 10)
        
        id = wx.NewId()
        button_OK = wx.Button(self, id, "Compute")
        button_OK.SetToolTipString("Perform P(r) inversion.")
        self.Bind(wx.EVT_BUTTON, self._on_invert, id = id)   
        #button_Cancel = wx.Button(self, wx.ID_CANCEL, "Cancel")
        
        sizer_button = wx.BoxSizer(wx.HORIZONTAL)
        sizer_button.Add((20, 20), 1, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        sizer_button.Add(button_OK, 0, wx.LEFT|wx.ADJUST_MINSIZE, 10)
        #sizer_button.Add(button_Cancel, 0, wx.LEFT|wx.RIGHT|wx.ADJUST_MINSIZE, 10)        
        vbox.Add(sizer_button, 0, wx.EXPAND|wx.BOTTOM|wx.TOP, 10)


        self.SetSizer(vbox)
        

        
    def _on_accept_alpha(self, evt):
        """
            User has accepted the estimated alpha, 
            set it as part of the input parameters
        """
        try:
            alpha = self.alpha_estimate_ctl.GetLabel()
            tmp = float(alpha)
            self.alpha_ctl.SetValue(alpha)
        except:
            # No estimate or bad estimate, either do nothing
            import sys
            print "InversionControl._on_accept_alpha: %s" % sys.exc_value
            pass
        
        
    def _on_pars_changed(self, evt):
        """
            Called when an input parameter has changed
            We will estimate the alpha parameter behind the
            scenes. 
        """
        flag, alpha, dmax, nfunc, qmin, qmax = self._read_pars()
        
        # If the pars are valid, estimate alpha
        if flag:
            if self.plot_radio.GetValue():
                dataset = self.plot_data.GetValue()
                self.manager.estimate_plot_inversion(alpha=alpha, nfunc=nfunc, 
                                                     d_max=dmax,
                                                     q_min=qmin, q_max=qmax)
            else:
                path = self.data_file.GetValue()
                self.manager.estimate_file_inversion(alpha=alpha, nfunc=nfunc, 
                                                     d_max=dmax, path=path,
                                                     q_min=qmin, q_max=qmax)
        
        
    def _read_pars(self, evt=None):    
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
        
        # Read qmin
        try:
            qmin_str = self.qmin_ctl.GetValue()
            if len(qmin_str.lstrip().rstrip())==0:
                qmin = None
            else:
                qmin = float(qmin_str)
                self.qmin_ctl.SetBackgroundColour(wx.WHITE)
                self.qmin_ctl.Refresh()
        except:
            flag = False
            self.qmin_ctl.SetBackgroundColour("pink")
            self.qmin_ctl.Refresh()
        
        # Read qmax
        try:
            qmax_str = self.qmax_ctl.GetValue()
            if len(qmax_str.lstrip().rstrip())==0:
                qmax = None
            else:
                qmax = float(qmax_str)
                self.qmax_ctl.SetBackgroundColour(wx.WHITE)
                self.qmax_ctl.Refresh()
        except:
            flag = False
            self.qmax_ctl.SetBackgroundColour("pink")
            self.qmax_ctl.Refresh()
        
        return flag, alpha, dmax, nfunc, qmin, qmax
    
    def _on_invert(self, evt):
        """
            Perform inversion
            @param silent: when True, there will be no output for the user 
        """
        # Get the data from the form
        # Push it to the manager
        
        flag, alpha, dmax, nfunc, qmin, qmax = self._read_pars()
        
        if flag:
            if self.plot_radio.GetValue():
                dataset = self.plot_data.GetValue()
                self.manager.setup_plot_inversion(alpha=alpha, nfunc=nfunc, 
                                                  d_max=dmax,
                                                  q_min=qmin, q_max=qmax)
            else:
                path = self.data_file.GetValue()
                self.manager.setup_file_inversion(alpha=alpha, nfunc=nfunc, 
                                                  d_max=dmax, path=path,
                                                  q_min=qmin, q_max=qmax
                                                  )
                
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
        



class HelpDialog(wx.Dialog):
    def __init__(self, parent, id):
        from sans.pr.invertor import help
        wx.Dialog.__init__(self, parent, id, size=(400, 420))
        self.SetTitle("P(r) help") 
        

        vbox = wx.BoxSizer(wx.VERTICAL)

        explanation = help()
           
        label_explain = wx.StaticText(self, -1, explanation, size=(350,320))
            
        vbox.Add(label_explain, 0, wx.ALL|wx.EXPAND, 15)


        static_line = wx.StaticLine(self, -1)
        vbox.Add(static_line, 0, wx.EXPAND, 0)
        
        button_OK = wx.Button(self, wx.ID_OK, "OK")
        #button_Cancel = wx.Button(self, wx.ID_CANCEL, "Cancel")
        
        sizer_button = wx.BoxSizer(wx.HORIZONTAL)
        sizer_button.Add((20, 20), 1, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        sizer_button.Add(button_OK, 0, wx.LEFT|wx.RIGHT|wx.ADJUST_MINSIZE, 10)
        #sizer_button.Add(button_Cancel, 0, wx.LEFT|wx.RIGHT|wx.ADJUST_MINSIZE, 10)        
        vbox.Add(sizer_button, 0, wx.EXPAND|wx.BOTTOM|wx.TOP, 10)

        self.SetSizer(vbox)
        self.SetAutoLayout(True)
        
        self.Layout()
        self.Centre()


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
        dialog = HelpDialog(None, -1)
        if dialog.ShowModal() == wx.ID_OK:
            pass
        dialog.Destroy()
        
        return 1

# end of class MyApp

if __name__ == "__main__":
    app = MyApp(0)
    app.MainLoop()
    
##### end of testing code #####################################################    
