'''
Created on Nov 29, 2016

@author: wpotrzebowski
'''

import wx
import wx.richtext
import wx.lib.hyperlink
import os

from sas.sasgui.guiframe.documentation_window import DocumentationWindow

try:
    # Try to find a local config
    import imp
    path = os.getcwd()
    if(os.path.isfile("%s/%s.py" % (path, 'local_config'))) or \
      (os.path.isfile("%s/%s.pyc" % (path, 'local_config'))):
        fObj, path, descr = imp.find_module('local_config', [path])
        config = imp.load_module('local_config', fObj, path, descr)
    else:
        # Try simply importing local_config
        import local_config as config
except:
    # Didn't find local config, load the default
    import config


class GpuOptions(wx.Dialog):
    """
    "Acknowledgement" Dialog Box

    Shows the current method for acknowledging SasView in
    scholarly publications.

    """

    def __init__(self, *args, **kwds):

        kwds["style"] = wx.DEFAULT_DIALOG_STYLE
        wx.Dialog.__init__(self, *args, **kwds)

        clinfo = self._get_clinfo()
        self.panel1 = wx.Panel(self, -1)
        static_box1 = wx.StaticBox(self.panel1, -1, "Available OpenCL Options:")

        rows = len(clinfo)

        flexsizer = wx.FlexGridSizer(rows, 1, hgap=20, vgap=10)
        self.option_button = {}
        for index, fitter in enumerate(clinfo):
            button = wx.RadioButton(self.panel1, -1,
                    label=fitter, name=fitter)
            if fitter != "No OpenCL":
                self.option_button[fitter] = str(index)
            else:
                self.option_button[fitter] = "None"
            self.Bind(wx.EVT_RADIOBUTTON, self.OnRadio, id=button.GetId())
            flexsizer.Add(button, 0, 0)

        fit_hsizer = wx.StaticBoxSizer(static_box1, orient=wx.VERTICAL)
        fit_hsizer.Add(flexsizer, 0, wx.ALL, 5)

        self.panel1.SetSizer(fit_hsizer)

        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.panel1, 0, wx.ALL, 10)

        accept_btn = wx.Button(self, wx.ID_OK)
        accept_btn.SetToolTipString("Accept new options for GPU")

        help_btn = wx.Button(self, wx.ID_HELP, 'Help')
        #help_btn = wx.Button(self, wx.ID_ANY, 'Help')
        help_btn.SetToolTipString("Help on the GPU options")

        self.Bind(wx.EVT_BUTTON, self.OnAccept, accept_btn)
        #self.Bind(wx.EVT_BUTTON, self.OnCancel, cancel_btn)
        if help is not None:
            self.Bind(wx.EVT_BUTTON, self.OnHelp, help_btn)

        self.Bind(wx.EVT_CLOSE, self.OnClose)

        # Create the button sizer that will put the buttons in a row, right
        # justified, and with a fixed amount of space between them.  This
        # emulates the Windows convention for placing a set of buttons at the
        # bottom right of the window.
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.Add((10,20), 1)  # stretchable whitespace
        btn_sizer.Add(accept_btn, 0)
        #btn_sizer.Add((10,20), 0)  # non-stretchable whitespace
        #btn_sizer.Add(cancel_btn, 0)
        #btn_sizer.Add((10,20), 0)  # non-stretchable whitespace
        btn_sizer.Add((10,20), 0)  # non-stretchable whitespace
        btn_sizer.Add(help_btn, 0)

        # Add the button sizer to the main sizer.
        self.vbox.Add(btn_sizer, 0, wx.EXPAND|wx.ALL, 10)

        # Finalize the sizer and establish the dimensions of the dialog box.
        # The minimum width is explicitly set because the sizer is not able to
        # take into consideration the width of the enclosing frame's title.
        self.SetSizer(self.vbox)
        #self.vbox.SetMinSize((size[0], -1))
        self.vbox.Fit(self)

        self.Centre()

    def _get_clinfo(self):
        try:
            import pyopencl as cl
            devices = cl.get_platforms()[0].get_devices()
            clinfo = [dev.name for dev in devices]
            clinfo.append("No OpenCL")
        except:
            warnings.warn(str(exc))
            warnings.warn("pyopencl import failed")
            clinfo = None
        return clinfo

    def OnRadio(self, event):
        import sasmodels
        button = event.GetEventObject()
        os.environ["SAS_OPENCL"] = self.option_button[button.Name]
        sasmodels.kernelcl.ENV = None
        reload(sasmodels.core)

    def OnAccept(self, event):
        """
        Save the current fitter and options to the fit config.
        """
        event.Skip()

    def OnHelp(self, event):
        """
        Provide help on the selected fitter.
        """
        _TreeLocation = "user/gpu_computations.html"
        _anchor = "#device-selection"
        DocumentationWindow(self, -1,
                            _TreeLocation, _anchor, "OpenCL Options Help")

    def OnClose(self, event):
        """
        Don't close the window, just hide it.
        """
        event.Skip()

##### testing code ############################################################
class MyApp(wx.App):
    """
    Class for running module as stand alone for testing
    """
    def OnInit(self):
        """
        Defines an init when running as standalone
        """
        wx.InitAllImageHandlers()
        dialog = GpuOptions(None, -1, "")
        self.SetTopWindow(dialog)
        dialog.ShowModal()
        dialog.Destroy()
        return 1

# end of class MyApp

if __name__ == "__main__":
    app = MyApp(0)
    app.MainLoop()
