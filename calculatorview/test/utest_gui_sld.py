"""
test gui for sld calculator
"""

import unittest
import wx

H2O_DENSITY = 1.0
WAVELENGTH = 6.0

class testTextCtrl(unittest.TestCase):
    """
    txtctrl should have a pink background when the result are incorrect
    and white when reset or correct value
    """
    def setUp(self):
        """
        Create an Sld calculator
        """
        self.app = wx.App()
        from sans.perspectives.calculator.sld_panel import SldWindow
        self.sld_frame = SldWindow()
       
    def testCompoundTextCtrl(self):
        """
        Test Compund textCtrl
        """
        #add  invalid value for compound
        self.sld_frame.panel.compound_ctl.SetValue("String not in table")
        self.sld_frame.panel.density_ctl.SetValue(str(H2O_DENSITY))
        id = self.sld_frame.panel.button_calculate.GetId()
        clickEvent = wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED, id)
        self.sld_frame.panel.ProcessEvent(clickEvent)
        bkg = self.sld_frame.panel.compound_ctl.GetBackgroundColour()
        self.assert_(bkg.GetAsString() == 'pink')
        #compute invariant without entering a value for compound
        self.sld_frame.panel.compound_ctl.SetValue("")
        self.sld_frame.panel.density_ctl.SetValue(str(H2O_DENSITY))
        self.sld_frame.panel.ProcessEvent(clickEvent)
        bkg = self.sld_frame.panel.compound_ctl.GetBackgroundColour()
        self.assert_(bkg.GetAsString() == 'pink')
        #compute invariant without entering a value for compound
        self.sld_frame.panel.compound_ctl.SetValue("H2O")
        self.sld_frame.panel.density_ctl.SetValue(str(H2O_DENSITY))
        self.sld_frame.panel.ProcessEvent(clickEvent)
        bkg = self.sld_frame.panel.compound_ctl.GetBackgroundColour()
        self.assert_(bkg.GetAsString() == 'white')
       
    def testDensityTextCtrl(self):
        """
        Test Density textCtrl
        
        """
        #add  invalid value for density
        self.sld_frame.panel.compound_ctl.SetValue("H2O")
        self.sld_frame.panel.density_ctl.SetValue("invalid density")
        id = self.sld_frame.panel.button_calculate.GetId()
        clickEvent = wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED, id)
        self.sld_frame.panel.ProcessEvent(clickEvent)
        bkg = self.sld_frame.panel.density_ctl.GetBackgroundColour()
        self.assert_(bkg.GetAsString() == 'pink')
        #compute invariant without entering a value for density
        self.sld_frame.panel.compound_ctl.SetValue("H2O")
        self.sld_frame.panel.density_ctl.SetValue("")
        self.sld_frame.panel.ProcessEvent(clickEvent)
        bkg = self.sld_frame.panel.density_ctl.GetBackgroundColour()
        self.assert_(bkg.GetAsString() == 'pink')
        #compute invariant without entering a value for density
        self.sld_frame.panel.compound_ctl.SetValue("H2O")
        self.sld_frame.panel.density_ctl.SetValue(str(H2O_DENSITY))
        self.sld_frame.panel.ProcessEvent(clickEvent)
        bkg = self.sld_frame.panel.density_ctl.GetBackgroundColour()
        self.assert_(bkg.GetAsString() == 'white')
        
    def testWavelengthTextCtrl(self):
        """
        Test wavelength textCtrl
        
        """
        #add  invalid value for wavelength
        self.sld_frame.panel.compound_ctl.SetValue("H2O")
        self.sld_frame.panel.density_ctl.SetValue(str(H2O_DENSITY))
        self.sld_frame.panel.wavelength_ctl.SetValue("invalid wavelength")
        id = self.sld_frame.panel.button_calculate.GetId()
        clickEvent = wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED, id)
        self.sld_frame.panel.ProcessEvent(clickEvent)
        bkg = self.sld_frame.panel.wavelength_ctl.GetBackgroundColour()
        self.assert_(bkg.GetAsString() == 'pink')
        #compute invariant without entering a value for wavelegnth
        self.sld_frame.panel.compound_ctl.SetValue("H2O")
        self.sld_frame.panel.density_ctl.SetValue(str(H2O_DENSITY))
        self.sld_frame.panel.wavelength_ctl.SetValue("")
        self.sld_frame.panel.ProcessEvent(clickEvent)
        bkg = self.sld_frame.panel.wavelength_ctl.GetBackgroundColour()
        value = self.sld_frame.panel.wavelength_ctl.GetValue()
        self.assert_(bkg.GetAsString() == 'white')
        self.assert_(float(value) == WAVELENGTH)
        #compute invariant with all correct inputs value
        self.sld_frame.panel.compound_ctl.SetValue("H2O")
        self.sld_frame.panel.density_ctl.SetValue(str(H2O_DENSITY))
        self.sld_frame.panel.wavelength_ctl.SetValue(str(WAVELENGTH/2))
        self.sld_frame.panel.ProcessEvent(clickEvent)
        bkg = self.sld_frame.panel.wavelength_ctl.GetBackgroundColour()
        value = self.sld_frame.panel.wavelength_ctl.GetValue()
        self.assert_(bkg.GetAsString() == 'white')
        self.assert_(float(value) == WAVELENGTH/2)
        
    def testSomeCombination(self):
        """
        Test other error
        """
        #only wavelength is invalid
        self.sld_frame.panel.compound_ctl.SetValue("H2O")
        self.sld_frame.panel.density_ctl.SetValue(str(H2O_DENSITY))
        self.sld_frame.panel.wavelength_ctl.SetValue("invalid wavelength")
        id = self.sld_frame.panel.button_calculate.GetId()
        clickEvent = wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED, id)
        self.sld_frame.panel.ProcessEvent(clickEvent)
        cp_bkg = self.sld_frame.panel.compound_ctl.GetBackgroundColour()
        self.assert_(cp_bkg.GetAsString() == 'white')
        ds_bkg = self.sld_frame.panel.density_ctl.GetBackgroundColour()
        self.assert_(ds_bkg.GetAsString() == 'white')
        wv_bkg = self.sld_frame.panel.wavelength_ctl.GetBackgroundColour()
        self.assert_(wv_bkg.GetAsString() == 'pink')
        #density, wavelength is invalid
        self.sld_frame.panel.compound_ctl.SetValue("H2O")
        self.sld_frame.panel.density_ctl.SetValue("invalid density")
        self.sld_frame.panel.wavelength_ctl.SetValue("invalid wavelength")
        id = self.sld_frame.panel.button_calculate.GetId()
        clickEvent = wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED, id)
        self.sld_frame.panel.ProcessEvent(clickEvent)
        cp_bkg = self.sld_frame.panel.compound_ctl.GetBackgroundColour()
        self.assert_(cp_bkg.GetAsString() == 'white')
        ds_bkg = self.sld_frame.panel.density_ctl.GetBackgroundColour()
        self.assert_(ds_bkg.GetAsString() == 'pink')
        wv_bkg = self.sld_frame.panel.wavelength_ctl.GetBackgroundColour()
        self.assert_(wv_bkg.GetAsString() == 'pink')
        #density, wavelength is invalid
        self.sld_frame.panel.compound_ctl.SetValue("invalid compound")
        self.sld_frame.panel.density_ctl.SetValue("invalid density")
        self.sld_frame.panel.wavelength_ctl.SetValue("")
        id = self.sld_frame.panel.button_calculate.GetId()
        clickEvent = wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED, id)
        self.sld_frame.panel.ProcessEvent(clickEvent)
        cp_bkg = self.sld_frame.panel.compound_ctl.GetBackgroundColour()
        self.assert_(cp_bkg.GetAsString() == 'pink')
        ds_bkg = self.sld_frame.panel.density_ctl.GetBackgroundColour()
        self.assert_(ds_bkg.GetAsString() == 'pink')
        wv_bkg = self.sld_frame.panel.wavelength_ctl.GetBackgroundColour()
        self.assert_(wv_bkg.GetAsString() == 'white')
        value = self.sld_frame.panel.wavelength_ctl.GetValue()
        self.assert_(float(value) == WAVELENGTH)

        
        
    def tearDown(self):
        """
        Destroy the sld calculator frame
        """
        self.sld_frame.Close()
        self.app.MainLoop()
        
if __name__ == "__main__":
    unittest.main()