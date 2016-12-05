'''
Module provides dialog for setting SAS_OPENCL variable, which defines
device choice for OpenCL calculation

Created on Nov 29, 2016

@author: wpotrzebowski
'''

import os
import warnings
import wx

from sas.sasgui.guiframe.documentation_window import DocumentationWindow

class GpuOptions(wx.Dialog):
    """
    "OpenCL options" Dialog Box

    Provides dialog for setting SAS_OPENCL variable, which defines
    device choice for OpenCL calculation

    """

    def __init__(self, *args, **kwds):

        kwds["style"] = wx.DEFAULT_DIALOG_STYLE
        wx.Dialog.__init__(self, *args, **kwds)

        clinfo = self._get_clinfo()

        self.panel1 = wx.Panel(self, -1)
        static_box1 = wx.StaticBox(self.panel1, -1, "Available OpenCL Options:")

        boxsizer = wx.BoxSizer(orient=wx.VERTICAL)
        self.option_button = {}
        self.buttons = []
        #Check if SAS_OPENCL is already set
        self.sas_opencl = os.environ.get("SAS_OPENCL","")
        for index, clopt in enumerate(clinfo):
            button = wx.CheckBox(self.panel1, -1, label=clopt, name=clopt)

            if clopt != "No OpenCL":
                self.option_button[clopt] = str(index)
                if self.sas_opencl == str(index):
                    button.SetValue(1)
            else:
                self.option_button[clopt] = "None"
                if self.sas_opencl.lower() == "none" :
                    button.SetValue(1)

            self.Bind(wx.EVT_CHECKBOX, self.on_check, id=button.GetId())
            self.buttons.append(button)
            boxsizer.Add(button, 0, 0)

        fit_hsizer = wx.StaticBoxSizer(static_box1, orient=wx.VERTICAL)
        fit_hsizer.Add(boxsizer, 0, wx.ALL, 5)

        self.panel1.SetSizer(fit_hsizer)

        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.panel1, 0, wx.ALL, 10)

        accept_btn = wx.Button(self, wx.ID_OK)
        accept_btn.SetToolTipString("Accept new OpenCL settings. This will"
                                    " overwrite SAS_OPENCL variable if set")

        help_id = wx.NewId()
        help_btn = wx.Button(self, help_id, 'Help')
        help_btn.SetToolTipString("Help on the GPU options")

        reset_id = wx.NewId()
        reset_btn = wx.Button(self, reset_id, 'Reset')
        reset_btn.SetToolTipString("Restore initial settings")

        self.Bind(wx.EVT_BUTTON, self.on_OK, accept_btn)
        self.Bind(wx.EVT_BUTTON, self.on_reset, reset_btn)
        self.Bind(wx.EVT_BUTTON, self.on_help, help_btn)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.Add((10, 20), 1) # stretchable whitespace
        btn_sizer.Add(accept_btn, 0)
        btn_sizer.Add((10, 20), 0) # non-stretchable whitespace
        btn_sizer.Add(reset_btn, 0)
        btn_sizer.Add((10, 20), 0) # non-stretchable whitespace
        btn_sizer.Add(help_btn, 0)

        # Add the button sizer to the main sizer.
        self.vbox.Add(btn_sizer, 0, wx.EXPAND|wx.ALL, 10)

        self.SetSizer(self.vbox)
        self.vbox.Fit(self)
        self.SetTitle("OpenCL options")
        self.Centre()

    def _get_clinfo(self):
        """
        Reading in information about available OpenCL infrastructure
        :return:
        """
        clinfo = []
        try:
            import pyopencl as cl
            for platform in cl.get_platforms():
                for device in platform.get_devices():
                    clinfo.append(":".join([platform.name,device.name]))
        except ImportError:
            warnings.warn("pyopencl import failed. Using only CPU computations")

        clinfo.append("No OpenCL")
        return clinfo

    def on_check(self, event):
        """
        Action triggered when button is selected
        :param event:
        :return:
        """
        selected_button = event.GetEventObject()
        for btn in self.buttons:
            if btn != selected_button:
                btn.SetValue(0)
        if selected_button.GetValue():
            self.sas_opencl = self.option_button[selected_button.Name]
        else:
            self.sas_opencl = None

    def on_OK(self, event):
        """
        Close window on accpetance
        """
        import sasmodels
        #If statement added to handle Reset
        if self.sas_opencl:
            os.environ["SAS_OPENCL"] = self.sas_opencl
        else:
            if "SAS_OPENCL" in os.environ:
                del(os.environ["SAS_OPENCL"])
        sasmodels.kernelcl.ENV = None
        #Need to reload sasmodels.core module to account SAS_OPENCL = "None"
        reload(sasmodels.core)
        event.Skip()

    def on_reset(self, event):
        """
        Close window on accpetance
        """
        for btn in self.buttons:
            btn.SetValue(0)
        self.sas_opencl=None

    def on_help(self, event):
        """
        Provide help on opencl options.
        """
        TreeLocation = "user/gpu_computations.html"
        anchor = "#device-selection"
        DocumentationWindow(self, -1,
                            TreeLocation, anchor, "OpenCL Options Help")
