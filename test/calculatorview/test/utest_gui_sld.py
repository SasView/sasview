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
        from sas.sasgui.perspectives.calculator.sld_panel import SldWindow
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
        cp_bkg = self.sld_frame.panel.compound_ctl.GetBackgroundColour()
        self.assert_(cp_bkg.GetAsString() == 'white')
        ds_bkg = self.sld_frame.panel.density_ctl.GetBackgroundColour()
        self.assert_(ds_bkg.GetAsString() == 'white')
        wv_bkg = self.sld_frame.panel.wavelength_ctl.GetBackgroundColour()
        value = self.sld_frame.panel.wavelength_ctl.GetValue()
        self.assert_(wv_bkg.GetAsString() == 'white')
        self.assert_(float(value) == WAVELENGTH)
        sld_real = self.sld_frame.panel.neutron_sld_real_ctl.GetValue()
        sld_im = self.sld_frame.panel.neutron_sld_im_ctl.GetValue()
        mo_real = self.sld_frame.panel.mo_ka_sld_real_ctl.GetValue()
        mo_im = self.sld_frame.panel.mo_ka_sld_im_ctl.GetValue()
        cu_real = self.sld_frame.panel.cu_ka_sld_real_ctl.GetValue()
        cu_im = self.sld_frame.panel.cu_ka_sld_im_ctl.GetValue()
        abs = self.sld_frame.panel.neutron_abs_ctl.GetValue()
        incoh = self.sld_frame.panel.neutron_inc_ctl.GetValue()
        length = self.sld_frame.panel.neutron_length_ctl.GetValue()
        
        self.assertAlmostEquals(float(sld_real), 1.04e-6, 1)
        self.assertAlmostEquals(float(sld_im), -1.5e-7, 1)
        #test absorption value
        self.assertAlmostEquals(float(abs) , 0.0741, 2)
        self.assertAlmostEquals(float(incoh), 5.62, 2)
        #Test length
        self.assertAlmostEquals(float(length), 0.1755, 2)
        #test Cu sld
        self.assertAlmostEquals(float(cu_real), 9.46e-6, 1)
        self.assertAlmostEquals(float(cu_im), 3.01e-8)
        # test Mo sld
        self.assertAlmostEquals(float(mo_real), 9.43e-6)
        self.assertAlmostEquals(float(mo_im), 5.65e-7, 1)
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
