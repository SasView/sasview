"""
    This module provide GUI for the neutron scattering length density calculator
    @author: Gervaise B. Alina
"""

import wx
import sys

from sans.guiframe.utils import format_number, check_float
from sans.guicomm.events import StatusEvent  


_BOX_WIDTH = 76
_STATICBOX_WIDTH = 350
_SCALE = 1e-6

#SLD panel size 
if sys.platform.count("win32")>0:
    _STATICBOX_WIDTH = 350
    PANEL_WIDTH = 500
    PANEL_HEIGHT = 600
    FONT_VARIANT = 0
else:
    _STATICBOX_WIDTH = 380
    PANEL_WIDTH = 530
    PANEL_HEIGHT = 600
    FONT_VARIANT = 1
    
class InvariantPanel(wx.Panel):
    """
        Provides the SLD calculator GUI.
    """
    ## Internal nickname for the window, used by the AUI manager
    window_name = "SLD Calculator"
    ## Name to appear on the window title bar
    window_caption = "SLD Calculator"
    ## Flag to tell the AUI manager to put this panel in the center pane
    CENTER_PANE = True
    def __init__(self, parent, base=None):
        wx.Panel.__init__(self, parent)
        #Font size 
        self.SetWindowVariant(variant=FONT_VARIANT)
        #Object that receive status event
        self.base = base
        self._do_layout()
        self.SetAutoLayout(True)
        self.Layout()
       
    def _do_layout(self):
        """
            Draw window content
        """
        unit_invariant = '[1/cm][1/A]'
        unit_volume = ''
        unit_surface = ''
        uncertainty = "+/-"
        sizer_input = wx.GridBagSizer(5,5)
        sizer_output = wx.GridBagSizer(5,5)
        sizer_button = wx.BoxSizer(wx.HORIZONTAL)
        sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer3 = wx.BoxSizer(wx.HORIZONTAL)
       
        #---------inputs----------------
        background_txt = wx.StaticText(self, -1, 'Background')
        self.background_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,-1))
        self.background_ctl.SetToolTipString("Background to subtract to data.")
        scale_txt = wx.StaticText(self, -1, 'Scale')
        self.scale_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,-1))
        self.scale_ctl.SetToolTipString("Scale to apply to data.")
        contrast_txt = wx.StaticText(self, -1, 'Contrast')
        self.contrast_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,-1))
        self.contrast_ctl.SetToolTipString("Contrast in q range.")
        porod_const_txt = wx.StaticText(self, -1, 'Porod Constant')
        self.porod_const_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,-1))
        self.porod_const_ctl.SetToolTipString("Invariant in q range.")
       
        iy = 0
        ix = 0
        sizer_input.Add(background_txt,(iy, ix),(1,1),\
                             wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix +=1
        sizer_input.Add(self.background_ctl,(iy, ix),(1,1),\
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        iy += 1
        ix = 0
        sizer_input.Add(scale_txt,(iy, ix),(1,1),\
                             wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1
        sizer_input.Add(self.scale_ctl, (iy, ix), (1,1),\
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        iy += 1
        ix = 0
        sizer_input.Add(contrast_txt, (iy, ix),(1,1),\
                             wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1
        sizer_input.Add(self.contrast_ctl,(iy, ix),(1,1),\
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        iy += 1
        ix = 0
        sizer_input.Add(porod_const_txt, (iy, ix),(1,1),\
                             wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1
        sizer_input.Add(self.porod_const_ctl,(iy, ix),(1,1),\
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        
        sizer_low_q = wx.GridBagSizer(5,5)
        self.guinier = wx.RadioButton(self, -1, 'Guinier',
                                         (10, 10), style=wx.RB_GROUP)
        self.power_law_low = wx.RadioButton(self, -1, 'Power_law', (10, 10))
        #self.Bind(wx.EVT_RADIOBUTTON, self._set_dipers_Param,
        #           id=self.guinier.GetId())
        #self.Bind(wx.EVT_RADIOBUTTON, self._set_dipers_Param,
        #           id=self.power_law_law.GetId())
        #MAC needs SetValue
        self.guinier.SetValue(True)
        power_low_txt = wx.StaticText(self, -1, 'Power')
        self.power_low_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,-1))
        self.power_low_ctl.SetToolTipString("Power to apply to the\
                                         Power_law function.")
        iy = 0
        ix = 0
        sizer_low_q.Add(self.power_law_low,(iy, ix),(1,1),
                            wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        iy += 1
        ix = 0
        sizer_low_q.Add(power_low_txt,(iy, ix),(1,1),
                            wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1
        sizer_low_q.Add(self.power_low_ctl, (iy, ix), (1,1),
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        iy += 1
        ix = 0
        sizer_low_q.Add(self.guinier,(iy, ix),(1,1),
                             wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
      
        sizer_high_q = wx.GridBagSizer(5,5)
        self.power_law_high = wx.RadioButton(self, -1, 'Power_law', (10, 10))
        #self.Bind(wx.EVT_RADIOBUTTON, self._set_dipers_Param,
        #           id=self.power_law_high.GetId())
        #MAC needs SetValue
        self.power_law_high.SetValue(True)
        power_high_txt = wx.StaticText(self, -1, 'Power')
        self.power_high_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,-1))
        self.power_high_ctl.SetToolTipString("Power to apply to the\
                                         Power_law function.")
        iy = 0
        ix = 0
        sizer_high_q.Add(self.power_law_high,(iy, ix),(1,1),
                            wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        iy += 1
        ix = 0
        sizer_high_q.Add(power_high_txt,(iy, ix),(1,1),
                            wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1
        sizer_high_q.Add(self.power_high_ctl, (iy, ix), (1,1),
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        
        high_q_box = wx.StaticBox(self, -1, "High Q")
        boxsizer_high_q = wx.StaticBoxSizer(high_q_box, wx.VERTICAL)
        boxsizer_high_q.Add(sizer_high_q)
        
        low_q_box = wx.StaticBox(self, -1, "Low Q")
        boxsizer_low_q = wx.StaticBoxSizer(low_q_box, wx.VERTICAL)
        boxsizer_low_q.Add(sizer_low_q)
        
        sizer_extrapolation = wx.BoxSizer(wx.HORIZONTAL)
        extrapolation_box = wx.StaticBox(self, -1, "Extrapolation")
        boxsizer_extra = wx.StaticBoxSizer(extrapolation_box, wx.HORIZONTAL)
        boxsizer_extra.Add(boxsizer_low_q)
        boxsizer_extra.Add((10,10))
        boxsizer_extra.Add(boxsizer_high_q)
    
        inputbox = wx.StaticBox(self, -1, "Input")
        boxsizer1 = wx.StaticBoxSizer(inputbox, wx.VERTICAL)
        boxsizer1.SetMinSize((_STATICBOX_WIDTH,-1))
        boxsizer1.Add(sizer_input)
        boxsizer1.Add(boxsizer_extra)
        
        sizer1.Add(boxsizer1,0, wx.EXPAND | wx.ALL, 10)
        #---------Outputs sizer--------
        invariant_txt = wx.StaticText(self, -1, 'Invariant')
        self.invariant_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,-1))
        self.invariant_ctl.SetEditable(False)
        self.invariant_ctl.SetToolTipString("Invariant in q range.")
        self.invariant_err_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,-1))
        self.invariant_err_ctl.SetEditable(False)
        self.invariant_err_ctl.SetToolTipString("Uncertainty on invariant.")
        invariant_units_txt = wx.StaticText(self, -1, unit_invariant)
        
        invariant_total_txt = wx.StaticText(self, -1, 'Invariant Total')
        self.invariant_total_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,-1))
        self.invariant_total_ctl.SetEditable(False)
        self.invariant_total_ctl.SetToolTipString("Invariant in q range and extra\
                   polated range.")
        self.invariant_total_err_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,-1))
        self.invariant_total_err_ctl.SetEditable(False)
        self.invariant_total_err_ctl.SetToolTipString("Uncertainty on invariant.")
        invariant_total_units_txt = wx.StaticText(self, -1, unit_invariant)
        
        volume_txt = wx.StaticText(self, -1, 'Volume Fraction')
        self.volume_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,-1))
        self.volume_ctl.SetEditable(False)
        self.volume_ctl.SetToolTipString("volume fraction.")
        self.volume_err_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,-1))
        self.volume_err_ctl.SetEditable(False)
        self.volume_err_ctl.SetToolTipString("Uncertainty of volume fraction.")
        volume_units_txt = wx.StaticText(self, -1, unit_volume)
        
        surface_txt = wx.StaticText(self, -1, 'Surface')
        self.surface_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,-1))
        self.surface_ctl.SetEditable(False)
        self.surface_ctl.SetToolTipString("Surface.")
        self.surface_err_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,-1))
        self.surface_err_ctl.SetEditable(False)
        self.surface_err_ctl.SetToolTipString("Uncertainty of surface.")
        surface_units_txt = wx.StaticText(self, -1, unit_surface)
        
        invariant_low_txt = wx.StaticText(self, -1, 'Invariant in low Q')
        self.invariant_low_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,-1))
        self.invariant_low_ctl.SetEditable(False)
        self.invariant_low_ctl.SetToolTipString("Invariant compute in low Q")
        invariant_low_units_txt = wx.StaticText(self, -1,  unit_invariant)
        
        invariant_high_txt = wx.StaticText(self, -1, 'Invariant in high Q')
        self.invariant_high_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,-1))
        self.invariant_high_ctl.SetEditable(False)
        self.invariant_high_ctl.SetToolTipString("Invariant compute in high Q")
        invariant_high_units_txt = wx.StaticText(self, -1,  unit_invariant)
       
        iy = 0
        ix = 0
        sizer_output.Add(invariant_low_txt, (iy, ix), (1,1),
                             wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix +=1
        sizer_output.Add(self.invariant_low_ctl, (iy, ix), (1,1),
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix += 2
        sizer_output.Add(invariant_low_units_txt, (iy, ix), (1,1),
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        iy += 1
        ix = 0 
        sizer_output.Add(invariant_high_txt, (iy, ix), (1,1),
                             wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix +=1
        sizer_output.Add(self.invariant_high_ctl, (iy, ix), (1,1),
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix += 2
        sizer_output.Add(invariant_high_units_txt, (iy, ix), (1,1),
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        iy += 1
        ix = 0
        sizer_output.Add(invariant_txt,(iy, ix),(1,1),
                            wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1
        sizer_output.Add(self.invariant_ctl,(iy, ix),(1,1),
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        ix += 1
        sizer_output.Add( wx.StaticText(self, -1, uncertainty),
                         (iy, ix),(1,1),wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        ix +=1
        sizer_output.Add(self.invariant_err_ctl
                         ,(iy, ix),(1,1),wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        ix +=1
        sizer_output.Add(invariant_units_txt
                         ,(iy, ix),(1,1),wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        iy += 1
        ix = 0
        sizer_output.Add(invariant_total_txt,(iy, ix),(1,1),
                            wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1
        sizer_output.Add(self.invariant_total_ctl,(iy, ix),(1,1),
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        ix += 1
        sizer_output.Add( wx.StaticText(self, -1, uncertainty),
                         (iy, ix),(1,1),wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        ix +=1
        sizer_output.Add(self.invariant_total_err_ctl
                         ,(iy, ix),(1,1),wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        ix +=1
        sizer_output.Add(invariant_total_units_txt
                         ,(iy, ix),(1,1),wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        iy += 1
        ix = 0
        sizer_output.Add(volume_txt,(iy, ix),(1,1),
                             wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix +=1
        sizer_output.Add(self.volume_ctl,(iy, ix),(1,1),
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        ix +=1
        sizer_output.Add(wx.StaticText(self, -1, uncertainty)
                         ,(iy, ix),(1,1),wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix += 1
        sizer_output.Add(self.volume_err_ctl
                         ,(iy, ix),(1,1),wx.EXPAND|wx.ADJUST_MINSIZE, 0)  
        ix += 1
        sizer_output.Add(volume_units_txt
                         ,(iy, ix),(1,1),wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        iy += 1
        ix = 0
        sizer_output.Add(surface_txt,(iy, ix),(1,1),
                             wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix +=1
        sizer_output.Add(self.surface_ctl,(iy, ix),(1,1),
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        ix +=1
        sizer_output.Add(wx.StaticText(self, -1, uncertainty)
                         ,(iy, ix),(1,1),wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix += 1
        sizer_output.Add(self.surface_err_ctl
                         ,(iy, ix),(1,1),wx.EXPAND|wx.ADJUST_MINSIZE, 0)  
        ix +=1
        sizer_output.Add(surface_units_txt
                         ,(iy, ix),(1,1),wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        
        outputbox = wx.StaticBox(self, -1, "Output")
        boxsizer2 = wx.StaticBoxSizer(outputbox, wx.VERTICAL)
        boxsizer2.SetMinSize((_STATICBOX_WIDTH,-1))
        boxsizer2.Add( sizer_output )
        sizer2.Add(boxsizer2,0, wx.EXPAND|wx.ALL, 10)
        #-----Button  sizer------------
    
        id = wx.NewId()
        button_calculate = wx.Button(self, id, "Compute")
        button_calculate.SetToolTipString("Compute SlD of neutrons.")
        self.Bind(wx.EVT_BUTTON, self.compute_invariant, id = id)   
        
        sizer_button.Add((250, 20), 1, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        sizer_button.Add(button_calculate, 0, wx.RIGHT|wx.ADJUST_MINSIZE,20)
        sizer3.Add(sizer_button)
        #---------layout----------------
        vbox  = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(sizer1)
        vbox.Add(sizer2)
        vbox.Add(sizer3)
        vbox.Fit(self) 
        self.SetSizer(vbox)
    
    def compute_invariant(self, event):
        """
            compute invariant
        """
         
class InvariantDialog(wx.Dialog):
    def __init__(self, parent=None, id=1, title="Invariant",base=None):
        wx.Dialog.__init__(self, parent, id, title, size=( PANEL_WIDTH,
                                                             PANEL_HEIGHT))
        
        self.panel = InvariantPanel(self, base=base)
        self.Centre()
        self.Show(True)
        
class MyApp(wx.App):
    def OnInit(self):
        wx.InitAllImageHandlers()
       
        dialog = InvariantDialog(None)
        if dialog.ShowModal() == wx.ID_OK:
            pass
        dialog.Destroy()
        
        return 1
   
# end of class MyApp

if __name__ == "__main__":
    app = MyApp(0)
    app.MainLoop()