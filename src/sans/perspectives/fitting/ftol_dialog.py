"""
Dialog to set ftol for Scipy

    ftol(float): Relative error desired in the sum of squares.
"""
################################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation.
#
#See the license text in license.txt
#
#copyright 2009, University of Tennessee
################################################################################
import wx
import sys
# default ftol
F_TOL = 1.49012e-08
SANS_F_TOL = 5e-05

if sys.platform.count("win32") > 0:
    PANEL_WIDTH = 270
    PANEL_HEIGHT = 265
    FONT_VARIANT = 0
else:
    PANEL_WIDTH = 285
    PANEL_HEIGHT = 265
    FONT_VARIANT = 1
    
    
class ChangeFtol(wx.Dialog):
    """
    Dialog to select ftol
    """
    def __init__(self, parent, base, id=-1, title="FTolerance"):
        wx.Dialog.__init__(self, parent, id, title,
                           size=(PANEL_WIDTH, PANEL_HEIGHT))
        # font size
        self.SetWindowVariant(variant=FONT_VARIANT)
        # build layout
        panel = wx.Panel(self, -1)
        vbox = wx.BoxSizer(wx.VERTICAL)
        wx.StaticBox(panel, -1, 'FTol selection (Leastsq)', (5, 6), (PANEL_WIDTH * 0.9, PANEL_HEIGHT * 0.7))
        self.default_bt = wx.RadioButton(panel, -1, 'SansView Default (5e-05)', (15, 30), style=wx.RB_GROUP)
        self.default_bt.SetValue(True)
        self.default_bt.Bind(wx.EVT_RADIOBUTTON, self.OnFtolSelection)
        self.sci_default_bt = wx.RadioButton(panel, -1, 'Scipy Default (1.49012e-08)', (15, 55))
        self.sci_default_bt.SetValue(False)
        self.sci_default_bt.Bind(wx.EVT_RADIOBUTTON, self.OnFtolSelection)
        self.high_bt = wx.RadioButton(panel, -1, '1e-06', (15, 80))
        self.high_bt.SetValue(False)
        self.high_bt.Bind(wx.EVT_RADIOBUTTON, self.OnFtolSelection)
        self.mid_bt = wx.RadioButton(panel, -1, '1e-05', (15, 105))
        self.mid_bt.SetValue(False)
        self.mid_bt.Bind(wx.EVT_RADIOBUTTON, self.OnFtolSelection)
        self.low_bt = wx.RadioButton(panel, -1, '1e-04', (15, 130))
        self.low_bt.SetValue(False)
        self.low_bt.Bind(wx.EVT_RADIOBUTTON, self.OnFtolSelection)
        self.custom_bt = wx.RadioButton(panel, -1, 'Custom', (15, 155))
        self.custom_bt.SetValue(False)
        self.custom_bt.Bind(wx.EVT_RADIOBUTTON, self.OnFtolSelection)
        self.custombox = wx.TextCtrl(panel, -1, '', (95, 155))
        self.custombox.Disable()
        
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        okButton = wx.Button(self, wx.ID_OK, 'Set', size=(70, 30))
        closeButton = wx.Button(self,wx.ID_CANCEL, 'Cancel', size=(70, 30))
        hbox.Add(okButton, 1, wx.RIGHT, 5)
        hbox.Add(closeButton, 1, wx.RIGHT, 5)
        vbox.Add(panel, 1, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 10)
        vbox.Add(hbox, 1, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 10)
        
        self.SetSizer(vbox)

    def OnFtolSelection(self, event=None):
        """
           Changes the ftol on selection of the radio button
        """
        self.custombox.Enable(self.custom_bt.GetValue())
        
    def get_ftol(self):
        """
            Get the ftol value
        """
        if self.default_bt.GetValue():
            return SANS_F_TOL
        elif self.sci_default_bt.GetValue():
            return F_TOL
        elif self.low_bt.GetValue():
            return 1.0e-4
        elif self.mid_bt.GetValue():
            return 1.0e-5
        elif self.high_bt.GetValue():
            return 1.0e-6
        if self.custom_bt.GetValue():
            try:
                return float(self.custombox.GetValue())
            except:
                return None
        return SANS_F_TOL
