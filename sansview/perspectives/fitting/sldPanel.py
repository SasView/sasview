"""
    This module provide GUI for the neutron scattering length density calculator
    @author: Gervaise B. Alina
"""

import wx
import sys

from sans.guiframe.utils import format_number, check_float
from sans.guicomm.events import StatusEvent  
from sldCalculator import SldCalculator

_BOX_WIDTH = 76
_STATICBOX_WIDTH = 350
_SCALE = 1e-6

#SLD panel size 
if sys.platform.count("darwin")==0:
    _STATICBOX_WIDTH = 350
    PANEL_SIZE = 400
    FONT_VARIANT = 0
else:
    _STATICBOX_WIDTH = 380
    PANEL_SIZE = 430
    FONT_VARIANT = 1
    
class SldPanel(wx.Panel):
    """
        Provides the SLD calculator GUI.
    """
    def __init__(self, parent,base=None, id = -1):
        wx.Panel.__init__(self, parent, id = id)
        #Font size 
        self.SetWindowVariant(variant=FONT_VARIANT)
        
        # Object that receive status event
        self.base= base
        self.calculator = SldCalculator()
        self.wavelength = self.calculator.wavelength
        
        self._do_layout()
        self.SetAutoLayout(True)
        self.Layout()
       

    def _do_layout(self):
        """
            Draw window content
        """
        unit_a = '[A]'
        unit_density = '[g/cm^(3)]'
        unit_sld= '[1/A^(2)]'
        unit_cm1='[1/cm]'
        unit_cm='[cm]'
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
        
        compound_txt = wx.StaticText(self, -1, 'Compound ')
        self.compound_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,-1))
        density_txt = wx.StaticText(self, -1, 'Density ')
        self.density_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,-1))
        unit_density_txt = wx.StaticText(self, -1, unit_density)
        wavelength_txt = wx.StaticText(self, -1, 'Wavelength ')
        self.wavelength_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,-1))
        self.wavelength_ctl.SetValue(str(self.wavelength))
        unit_a_txt = wx.StaticText(self, -1, unit_a)
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
        ix +=1
        sizer_input.Add(unit_density_txt,(iy, ix),(1,1),\
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        iy += 1
        ix = 0
        sizer_input.Add(wavelength_txt,(iy, ix),(1,1),\
                             wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix +=1
        sizer_input.Add(self.wavelength_ctl,(iy, ix),(1,1),\
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        ix +=1
        sizer_input.Add(unit_a_txt,(iy, ix),(1,1),\
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        boxsizer1.Add( sizer_input )
        sizer1.Add(boxsizer1,0, wx.EXPAND | wx.ALL, 10)
        #---------Outputs sizer--------
        outputbox = wx.StaticBox(self, -1, "Output")
        boxsizer2 = wx.StaticBoxSizer(outputbox, wx.VERTICAL)
        boxsizer2.SetMinSize((_STATICBOX_WIDTH,-1))
        
        i_complex= '+ i'
        neutron_sld_txt = wx.StaticText(self, -1, 'Neutron SLD')
        self.neutron_sld_reel_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,-1))
        self.neutron_sld_reel_ctl.SetEditable(False)
        self.neutron_sld_reel_ctl.SetToolTipString("Neutron SLD reel.")
        self.neutron_sld_im_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,-1))
        self.neutron_sld_im_ctl.SetEditable(False)
        self.neutron_sld_im_ctl.SetToolTipString("Neutron SLD imaginary.")
        neutron_sld_units_txt = wx.StaticText(self, -1, unit_sld)
        
        cu_ka_sld_txt = wx.StaticText(self, -1, 'Cu Ka SLD')
        self.cu_ka_sld_reel_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,-1))
        self.cu_ka_sld_reel_ctl.SetEditable(False)
        self.cu_ka_sld_reel_ctl.SetToolTipString("Cu Ka SLD reel.")
        self.cu_ka_sld_im_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,-1))
        self.cu_ka_sld_im_ctl.SetEditable(False)
        self.cu_ka_sld_im_ctl.SetToolTipString("Cu Ka SLD imaginary.")
        cu_ka_sld_units_txt = wx.StaticText(self, -1, unit_sld)
        
        mo_ka_sld_txt = wx.StaticText(self, -1, 'Mo Ka SLD')
        self.mo_ka_sld_reel_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,-1))
        self.mo_ka_sld_reel_ctl.SetEditable(False)
        self.mo_ka_sld_reel_ctl.SetToolTipString("Mo Ka SLD reel.")
        self.mo_ka_sld_im_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,-1))
        self.mo_ka_sld_im_ctl.SetEditable(False)
        self.mo_ka_sld_im_ctl.SetToolTipString("Mo Ka SLD reel.")
        mo_ka_sld_units_txt = wx.StaticText(self, -1, unit_sld)
        
        neutron_inc_txt = wx.StaticText(self, -1, 'Neutron Inc. Xs')
        self.neutron_inc_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,-1))
        self.neutron_inc_ctl.SetEditable(False)
        self.neutron_inc_ctl.SetToolTipString("Neutron Inc. Xs")
        neutron_inc_units_txt = wx.StaticText(self, -1,  unit_cm1)
        
        neutron_abs_txt = wx.StaticText(self, -1, 'Neutron Abs. Xs')
        self.neutron_abs_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,-1))
        self.neutron_abs_ctl.SetEditable(False)
        self.neutron_abs_ctl.SetToolTipString("Neutron Abs. Xs")
        neutron_abs_units_txt = wx.StaticText(self, -1,  unit_cm1)
        
        neutron_length_txt = wx.StaticText(self, -1, 'Neutron 1/e length')
        self.neutron_length_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,-1))
        self.neutron_length_ctl.SetEditable(False)
        self.neutron_length_ctl.SetToolTipString("Neutron 1/e length")
        neutron_length_units_txt = wx.StaticText(self, -1,  unit_cm)
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
        ix +=2
        sizer_output.Add(neutron_inc_units_txt,(iy, ix),(1,1),
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        iy += 1
        ix = 0
        sizer_output.Add(neutron_abs_txt,(iy, ix),(1,1),
                             wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix +=1
        sizer_output.Add(self.neutron_abs_ctl,(iy, ix),(1,1),
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        ix +=2
        sizer_output.Add(neutron_abs_units_txt,(iy, ix),(1,1),
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        iy += 1
        ix = 0
        sizer_output.Add(neutron_length_txt,(iy, ix),(1,1),
                             wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix +=1
        sizer_output.Add(self.neutron_length_ctl,(iy, ix),(1,1),
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix +=2
        sizer_output.Add(neutron_length_units_txt,(iy, ix),(1,1),
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0)  
        boxsizer2.Add( sizer_output )
        sizer2.Add(boxsizer2,0, wx.EXPAND | wx.ALL, 10)
        #-----Button  sizer------------
        id = wx.NewId()
        button_help = wx.Button(self, id, "Help")
        button_help.SetToolTipString("Help  SlD calculations and formula.")
        self.Bind(wx.EVT_BUTTON, self.onHelp, id = id)  
         
        id = wx.NewId()
        button_calculate = wx.Button(self, id, "Calculate")
        button_calculate.SetToolTipString("Calculate SlD of neutrons.")
        self.Bind(wx.EVT_BUTTON, self.calculateSld, id = id)   
        
        sizer_button.Add((200, 20), 1, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        sizer_button.Add(button_help, 0, wx.RIGHT|wx.ADJUST_MINSIZE,10)
        sizer_button.Add(button_calculate, 0, wx.RIGHT|wx.ADJUST_MINSIZE,20)
        sizer3.Add(sizer_button)
        #---------layout----------------
        vbox  = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(sizer1)
        vbox.Add(sizer2)
        vbox.Add(sizer3)
        vbox.Fit(self) 
        self.SetSizer(vbox)
        
        
    def check_inputs(self):
        """Check validity user inputs"""
        flag= True
       
        if check_float(self.density_ctl):
            self.density = float(self.density_ctl.GetValue())
        else:
            flag=False
            raise ValueError,"Error for Density value :expect float"
    
        self.wavelength= self.wavelength_ctl.GetValue()
        if self.wavelength.lstrip().rstrip()=="":
            self.wavelength = self.calculator.wavelength
        else:
            if check_float(self.wavelength_ctl):
                self.wavelength= float(self.wavelength)
            else:
                flag = False
                raise ValueError,"Error for wavelenth value :expect float"
                
        self.formulata_text= self.compound_ctl.GetValue().lstrip().rstrip()
        if self.formulata_text!="":
            self.compound_ctl.SetBackgroundColour(wx.WHITE)
            self.compound_ctl.Refresh()
        else:
            self.compound_ctl.SetBackgroundColour("pink")
            self.compound_ctl.Refresh()
            flag=False
            raise ValueError, "Enter a formula"
        return flag 
        
        
    def onHelp(self, event):
        """
            provide more hint on the SLD calculator
        """
        from helpPanel import  HelpWindow
        frame = HelpWindow(None, -1, pageToOpen="doc/sld_calculator_help.html")    
        frame.Show(True)
        name = "SLD_calculator"
        if frame.rhelp.HasAnchor(name):
            frame.rhelp.ScrollToAnchor(name)
        else:
           msg= "Cannot find SLD Calculator description "
           msg +="Please.Search in the Help window"
           wx.PostEvent(self.base, StatusEvent(status = msg ))  
           
           
    def calculateSld(self, event):
        """
            Calculate the neutron scattering density length of a molecule
        """
        try:
            #Check validity user inputs
            if self.check_inputs():
                #get ready to compute
                try:
                    self.calculator.setValue(self.formulata_text,self.density,self.wavelength)
                except:
                    if self.base !=None:
                        msg= "SLD Calculator: %s" % (sys.exc_value)
                        wx.PostEvent(self.base, StatusEvent(status= msg ))
                    else:
                        raise
                    return
                
                # Compute the Cu SLD
                Cu_reel, Cu_im = self.calculator.calculateXRaySld( "Cu")
                self.cu_ka_sld_reel_ctl.SetValue(format_number(Cu_reel*_SCALE))
                self.cu_ka_sld_im_ctl.SetValue(format_number(Cu_im*_SCALE))
                
                # Compute the Mo SLD
                Mo_reel, Mo_im = self.calculator.calculateXRaySld( "Mo")
                self.mo_ka_sld_reel_ctl.SetValue(format_number(Mo_reel*_SCALE))
                self.mo_ka_sld_im_ctl.SetValue(format_number(Mo_im*_SCALE))
               
                coh,absorp,inc= self.calculator.calculateNSld()
                im = self.calculator.calculateAbsorptionIm()
                length = self.calculator.calculateLength()
                # Neutron SLD
                self.neutron_sld_reel_ctl.SetValue(format_number(coh*_SCALE))
                self.neutron_sld_im_ctl.SetValue(format_number(im*_SCALE))
                self.neutron_inc_ctl.SetValue(format_number(inc ))
                self.neutron_abs_ctl.SetValue(format_number(absorp))
                # Neutron length
                self.neutron_length_ctl.SetValue(format_number(length))
                # display wavelength
                self.wavelength_ctl.SetValue(str(self.wavelength))
        except:
            if self.base !=None:
                  msg= "SLD Calculator: %s" % (sys.exc_value)
                  wx.PostEvent(self.base, StatusEvent(status= msg ))
            else:
                raise
            return   

   
        
  
    
   
 
        
               
class SldWindow(wx.Frame):
    def __init__(self, parent=None, id=1, title="SLD Calculator",base=None):
        wx.Frame.__init__(self, parent, id, title, size=( PANEL_SIZE,  PANEL_SIZE))
        
        self.panel = SldPanel(self, base=base)
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
