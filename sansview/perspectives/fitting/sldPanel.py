"""
    This module intends to compute the neutron scattering length density of molecule
    @author: Gervaise B. Alina
"""

import wx
import sys

import periodictable
from periodictable import formula
from periodictable.xsf import xray_energy, xray_sld_from_atoms
from periodictable.constants import avogadro_number
import periodictable.nsf
neutron_sld_from_atoms= periodictable.nsf.neutron_sld_from_atoms 

from sans.guiframe.utils import format_number, check_float
from sans.guicomm.events import StatusEvent  


_BOX_WIDTH = 76
_STATICBOX_WIDTH = 350
_SCALE = 1e-6
_DEFAULT_WAVELENGTH = 1.798


class SldPanel(wx.Panel):
    """
        Provides the SLD calculator GUI.
    """
    def __init__(self, parent,base=None, id = -1):
        wx.Panel.__init__(self, parent, id = id)
        # Object that receive status event
        self.base= base
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
            self.wavelength = _DEFAULT_WAVELENGTH
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
                    self.new_formula = formula(self.formulata_text, density= self.density)
                    atom = self.new_formula.atoms
                except:
                    if self.base !=None:
                        msg= "SLD Calculator: %s" % (sys.exc_value)
                        wx.PostEvent(self.base, StatusEvent(status= msg ))
                    else:
                        raise
                    return
                # Compute the Cu SLD
                Cu_reel, Cu_im = self.calculateXRaySld( "Cu", density= self.density,
                                                        user_formula= self.new_formula)
                self.cu_ka_sld_reel_ctl.SetValue(format_number(Cu_reel*_SCALE))
                self.cu_ka_sld_im_ctl.SetValue(format_number(Cu_im*_SCALE))
                # Compute the Mo SLD
                Mo_reel, Mo_im = self.calculateXRaySld( "Mo", density= self.density,
                                                        user_formula= self.new_formula)
                self.mo_ka_sld_reel_ctl.SetValue(format_number(Mo_reel*_SCALE))
                self.mo_ka_sld_im_ctl.SetValue(format_number(Mo_im*_SCALE))
               
                coh,absorp,inc= self.calculateNSld(self.density, wavelength= self.wavelength,
                                                     user_formula= self.new_formula)
                #Don't know if value is return in cm or  cm^(-1).assume return in cm
                # to match result of neutron inc of Alan calculator
                inc= inc*1/10
                #Doesn't match result of Alan calculator for absorption factor of 2
                #multiplication of 100 is going around
                absorp= absorp *2*100
                volume= (self.new_formula.mass /self.density)/avogadro_number*1.0e24
                #im: imaginary part of neutron SLD
                im=0
                for el, count in atom.iteritems():
                    if el.neutron.b_c_i !=None:
                        im += el.neutron.b_c_i*count 
                im = im/volume
                
                self.neutron_sld_reel_ctl.SetValue(format_number(coh*_SCALE))
                self.neutron_sld_im_ctl.SetValue(format_number(im*_SCALE))
                self.neutron_inc_ctl.SetValue(format_number(inc ))
                self.neutron_abs_ctl.SetValue(format_number(absorp))
                #Don't know if value is return in cm or  cm^(-1).assume return in cm
                # to match result of neutron inc of Alan calculator
                length= (coh+ absorp+ inc)/volume
                self.neutron_length_ctl.SetValue(format_number(length))
        except:
            if self.base !=None:
                  msg= "SLD Calculator: %s" % (sys.exc_value)
                  wx.PostEvent(self.base, StatusEvent(status= msg ))
            else:
                raise
            return   

    def calculateXRaySld(self, element, density,user_formula):
        """
            Get an element and compute the corresponding SLD for a given formula
            @param element:  elementis a string of existing atom
            @param formula: molecule enters by the user
        """
        try:
            myformula = formula(str (element))
            if len(myformula.atoms)!=1:
                return 
            element= myformula.atoms.keys()[0] 
            energy = xray_energy(element.K_alpha)
            atom = user_formula.atoms
            atom_reel, atom_im = xray_sld_from_atoms( atom,
                                                  density=density,
                                                  energy= energy )
            return atom_reel, atom_im
        except:
            if self.base !=None:
                  msg= "SLD Calculator: %s" % (sys.exc_value)
                  wx.PostEvent(self.base, StatusEvent(status= msg ))
            else:
                raise
            return   
        
    def calculateNSld(self,density,wavelength,user_formula ):
        """
            Compute the neutron SLD for a given molecule
            @return absorp: absorption
            @return coh: coherence cross section
            @return inc: incoherence cross section
          
        """
        if density ==0:
            raise ZeroDivisionError,"integer division or modulo by zero for density"
            return 
        atom = user_formula.atoms
        coh,absorp,inc = neutron_sld_from_atoms(atom,density,wavelength)

        return coh,absorp,inc
    
   
 
        
               
class SldWindow(wx.Frame):
    def __init__(self, parent=None, id=1, title="SLD Calculator",base=None):
        wx.Frame.__init__(self, parent, id, title, size=(400, 400))
        
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
