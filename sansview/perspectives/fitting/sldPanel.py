import wx
_BOX_WIDTH = 76
_STATICBOX_WIDTH = 350

class SldPanel(wx.Panel):
    def __init__(self, parent, id = -1):
        wx.Panel.__init__(self, parent, id = id)
        
        self._do_layout()
        self.SetAutoLayout(True)
        self.Layout()
       

    def _do_layout(self):
        """
            Draw window content
        """
        sizer_input = wx.GridBagSizer(5,5)
        sizer_output = wx.GridBagSizer(5,5)
        sizer_button = wx.BoxSizer(wx.HORIZONTAL)
        sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        #---------inputs----------------
        inputbox = wx.StaticBox(self, -1, "Input")
        boxsizer1 = wx.StaticBoxSizer(inputbox, wx.VERTICAL)
        boxsizer1.SetMinSize((_STATICBOX_WIDTH,-1))
        
        compound_txt = wx.StaticText(self, -1, 'Compound')
        self.compound_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,-1))
        density_txt = wx.StaticText(self, -1, 'Density(g/cm^3)')
        self.density_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,-1))
        wavelength_txt = wx.StaticText(self, -1, 'Wavelength (A)')
        self.wavelength_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,-1))
        iy = 0
        ix = 0
        sizer_input.Add(compound_txt,(iy, ix),(1,1),\
                             wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix +=1
        sizer_input.Add(self.compound_ctl,(iy, ix),(1,1),\
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        iy += 1
        ix = 0
        sizer_input.Add(density_txt,(iy, ix),(1,1),\
                             wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix +=1
        sizer_input.Add(self.density_ctl,(iy, ix),(1,1),\
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        iy += 1
        ix = 0
        sizer_input.Add(wavelength_txt,(iy, ix),(1,1),\
                             wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix +=1
        sizer_input.Add(self.wavelength_ctl,(iy, ix),(1,1),\
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        boxsizer1.Add( sizer_input )
        sizer1.Add(boxsizer1,0, wx.EXPAND | wx.ALL, 10)
        #---------Outputs sizer--------
        outputbox = wx.StaticBox(self, -1, "Output")
        boxsizer2 = wx.StaticBoxSizer(outputbox, wx.VERTICAL)
        boxsizer2.SetMinSize((_STATICBOX_WIDTH,-1))
        
        unit_a= '[A^(-2)]'
        unit_cm1='[cm^(-1)]'
        unit_cm='[cm]'
        i_complex= '+ i'
        neutron_sld_txt = wx.StaticText(self, -1, 'Neutron SLD')
        self.neutron_sld_reel_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,-1))
        self.neutron_sld_reel_ctl.SetEditable(False)
        self.neutron_sld_reel_ctl.SetToolTipString("Neutron SLD reel.")
        self.neutron_sld_im_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,-1))
        self.neutron_sld_im_ctl.SetEditable(False)
        self.neutron_sld_im_ctl.SetToolTipString("Neutron SLD imaginary.")
        neutron_sld_units_txt = wx.StaticText(self, -1, unit_a)
        
        cu_ka_sld_txt = wx.StaticText(self, -1, 'Cu Ka SLD')
        self.cu_ka_sld_reel_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,-1))
        self.cu_ka_sld_reel_ctl.SetEditable(False)
        self.cu_ka_sld_reel_ctl.SetToolTipString("Cu Ka SLD reel.")
        self.cu_ka_sld_im_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,-1))
        self.cu_ka_sld_im_ctl.SetEditable(False)
        self.cu_ka_sld_im_ctl.SetToolTipString("Cu Ka SLD imaginary.")
        cu_ka_sld_units_txt = wx.StaticText(self, -1, unit_a)
        
        mo_ka_sld_txt = wx.StaticText(self, -1, 'Mo Ka SLD')
        self.mo_ka_sld_reel_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,-1))
        self.mo_ka_sld_reel_ctl.SetEditable(False)
        self.mo_ka_sld_reel_ctl.SetToolTipString("Mo Ka SLD reel.")
        self.mo_ka_sld_im_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,-1))
        self.mo_ka_sld_im_ctl.SetEditable(False)
        self.mo_ka_sld_im_ctl.SetToolTipString("Mo Ka SLD reel.")
        mo_ka_sld_units_txt = wx.StaticText(self, -1, unit_a)
        
        neutron_inc_txt = wx.StaticText(self, -1, 'Neutron Inc. Xs')
        self.neutron_inc_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,-1))
        self.neutron_inc_ctl.SetEditable(False)
        self.neutron_inc_ctl.SetToolTipString("Neutron Inc. Xs")
        
        neutron_abs_txt = wx.StaticText(self, -1, 'Neutron Abs. Xs')
        self.neutron_abs_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,-1))
        self.neutron_abs_ctl.SetEditable(False)
        self.neutron_abs_ctl.SetToolTipString("Neutron Abs. Xs")
        
        neutron_length_txt = wx.StaticText(self, -1, 'Neutron 1/e length')
        self.neutron_length_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,-1))
        self.neutron_length_ctl.SetEditable(False)
        self.neutron_length_ctl.SetToolTipString("Neutron 1/e length")
        iy = 0
        ix = 0
        sizer_output.Add(neutron_sld_txt,(iy, ix),(1,1),
                             wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix +=1
        sizer_output.Add(self.neutron_sld_reel_ctl,(iy, ix),(1,1),
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        ix +=1
        sizer_output.Add(wx.StaticText(self, -1, i_complex)
                         ,(iy, ix),(1,1),wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        ix +=1
        sizer_output.Add(self.neutron_sld_im_ctl
                         ,(iy, ix),(1,1),wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        ix +=1
        sizer_output.Add(neutron_sld_units_txt
                         ,(iy, ix),(1,1),wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        iy += 1
        ix = 0
        sizer_output.Add(cu_ka_sld_txt,(iy, ix),(1,1),
                             wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix +=1
        sizer_output.Add(self.cu_ka_sld_reel_ctl,(iy, ix),(1,1),
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        ix +=1
        sizer_output.Add(wx.StaticText(self, -1, i_complex)
                         ,(iy, ix),(1,1),wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix +=1
        sizer_output.Add(self.cu_ka_sld_im_ctl
                         ,(iy, ix),(1,1),wx.EXPAND|wx.ADJUST_MINSIZE, 0)  
        ix +=1
        sizer_output.Add(cu_ka_sld_units_txt
                         ,(iy, ix),(1,1),wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        iy += 1
        ix = 0
        sizer_output.Add(mo_ka_sld_txt,(iy, ix),(1,1),
                             wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix +=1
        sizer_output.Add(self.mo_ka_sld_reel_ctl,(iy, ix),(1,1),
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        ix +=1
        sizer_output.Add(wx.StaticText(self, -1, i_complex)
                         ,(iy, ix),(1,1),wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix +=1
        sizer_output.Add(self.mo_ka_sld_im_ctl
                         ,(iy, ix),(1,1),wx.EXPAND|wx.ADJUST_MINSIZE, 0)  
        ix +=1
        sizer_output.Add(mo_ka_sld_units_txt
                         ,(iy, ix),(1,1),wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        iy += 1
        ix = 0
        sizer_output.Add(neutron_inc_txt,(iy, ix),(1,1),
                             wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix +=1
        sizer_output.Add(self.neutron_inc_ctl,(iy, ix),(1,1),
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        iy += 1
        ix = 0
        sizer_output.Add(neutron_abs_txt,(iy, ix),(1,1),
                             wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix +=1
        sizer_output.Add(self.neutron_abs_ctl,(iy, ix),(1,1),
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        iy += 1
        ix = 0
        sizer_output.Add(neutron_length_txt,(iy, ix),(1,1),
                             wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix +=1
        sizer_output.Add(self.neutron_length_ctl,(iy, ix),(1,1),
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        boxsizer2.Add( sizer_output )
        sizer2.Add(boxsizer2,0, wx.EXPAND | wx.ALL, 10)
        #-----Button  sizer------------
        id = wx.NewId()
        button_calculate = wx.Button(self, id, "Calculate")
        button_calculate.SetToolTipString("Calculate SlD of neutrons.")
        #self.Bind(wx.EVT_BUTTON, self._calculateSld, id = id)   
        sizer_button.Add((20, 20), 1, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        sizer_button.Add(button_calculate, 0, wx.RIGHT|wx.ADJUST_MINSIZE, 10)
        sizer3.Add(sizer_button)
        #---------layout----------------
        vbox  = wx.BoxSizer(wx.VERTICAL)

        vbox.Add(sizer1)
        vbox.Add(sizer2)
        vbox.Add(sizer3)
        vbox.Fit(self) 
        self.SetSizer(vbox)
        
        
class SldWindow(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, size=(400, 400))
        
        self.panel = SldPanel(self)
        self.Centre()
        self.Show(True)
        
class ViewApp(wx.App):
    def OnInit(self):
        frame = SldWindow(None, -1, 'SLD Calculator')    
        frame.Show(True)
        self.SetTopWindow(frame)
        
        return True
        

if __name__ == "__main__": 
    app = ViewApp(0)
    app.MainLoop()     
