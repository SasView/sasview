'''
Module provides dialog for setting SAS_OPENCL variable, which defines
device choice for OpenCL calculation

Created on Nov 29, 2016

@author: wpotrzebowski
'''

import json
import platform
import logging
import os
import sys

import wx

# TODO: move device query functions to sasmodels
try:
    import pyopencl as cl
except ImportError:
    cl = None

import sasmodels
import sasmodels.model_test
import sasmodels.sasview_model
from sasmodels.generate import F32, F64

from sas.sasgui.guiframe.documentation_window import DocumentationWindow

logger = logging.getLogger(__name__)

class CustomMessageBox(wx.Dialog):
    """
    Custom message box for OpenCL results
    """
    def __init__(self, parent, msg, title):

        wx.Dialog.__init__(self, parent, title=title)

        self.static_box = wx.StaticBox(self, -1, "OpenCL test completed!")
        self.boxsizer = wx.BoxSizer(orient=wx.VERTICAL)

        self.text = wx.TextCtrl(self, -1, size=(500, 300),
                                style=wx.TE_MULTILINE|wx.TE_READONLY)
        self.text.SetValue(msg)
        self.text.SetBackgroundColour(self.GetBackgroundColour())
        self.text.SetFocus()
        self.text.SetInsertionPoint(self.text.GetLastPosition())
        self.boxsizer.Add(self.text, proportion=1, flag=wx.EXPAND)

        self.fit_hsizer = wx.StaticBoxSizer(self.static_box, orient=wx.VERTICAL)
        self.fit_hsizer.Add(self.boxsizer, 0, wx.ALL, 5)

        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.fit_hsizer, 0, wx.ALL, 10)

        self.message_text = wx.StaticText(self, -1, "If tests fail on OpenCL devices, "
                                                    "please select No OpenCL option.\n\n"
                                                    "In case of large number of failing tests, "
                                                    "please consider sending\n"
                                                    "above report to help@sasview.org.")

        self.vbox.Add(self.message_text, 0, wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 10)

        self.ok_btn = wx.Button(self, wx.ID_OK)

        self.btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_sizer.Add((10, 20), 1) # stretchable whitespace
        self.btn_sizer.Add(self.ok_btn, 0)

        self.vbox.Add(self.btn_sizer, 0, wx.EXPAND|wx.ALL, 10)

        self.SetSizer(self.vbox)
        self.vbox.Fit(self)

        self.SetAutoLayout(True)


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
        #Check if SAS_OPENCL is already set as environment variable
        self.sas_opencl = os.environ.get("SAS_OPENCL", "")

        for clopt in clinfo:
            button = wx.CheckBox(self.panel1, -1, label=clopt[1], name=clopt[1])

            if clopt != "No OpenCL":
                self.option_button[clopt[1]] = clopt[0]
                if self.sas_opencl == clopt[0]:
                    button.SetValue(1)
            else:
                self.option_button[clopt] = "None"
                if self.sas_opencl.lower() == "none":
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
                                    " override SAS_OPENCL variable if set")

        help_id = wx.NewId()
        help_btn = wx.Button(self, help_id, 'Help')
        help_btn.SetToolTipString("Help on the GPU options")

        reset_id = wx.NewId()
        reset_btn = wx.Button(self, reset_id, 'Reset')
        reset_btn.SetToolTipString("Restore initial settings")

        test_id = wx.NewId()
        test_btn = wx.Button(self, test_id, 'Test')
        test_btn.SetToolTipString("Test if models compile on the given infrastructure")
        self.test_btn = test_btn

        self.Bind(wx.EVT_BUTTON, self.on_OK, accept_btn)
        self.Bind(wx.EVT_BUTTON, self.on_test, test_btn)
        self.Bind(wx.EVT_BUTTON, self.on_reset, reset_btn)
        self.Bind(wx.EVT_BUTTON, self.on_help, help_btn)

        test_text = wx.StaticText(self, -1, "WARNING: Running tests can take a few minutes!")
        test_text2 = wx.StaticText(self, -1, "NOTE: No test will run if No OpenCL is checked")
        test_text.SetForegroundColour(wx.RED)
        self.vbox.Add(test_text2, 0, wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 10)
        self.vbox.Add(test_text, 0, wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 10)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.Add((10, 20), 1) # stretchable whitespace
        btn_sizer.Add(accept_btn, 0)
        btn_sizer.Add((10, 20), 0) # non-stretchable whitespace
        btn_sizer.Add(test_btn, 0)
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
        # TODO: Include cuda platforms if available.
        clinfo = []
        platforms = []

        if cl is None:
            logger.warn("Unable to import the pyopencl package.  It may not "
                        "have been installed.  If you wish to use OpenCL, try "
                        "running pip install --user pyopencl")
        else:
            try:
                platforms = cl.get_platforms()
            except cl.LogicError as err:
                logger.warn("Unable to fetch the OpenCL platforms.  This likely "
                            "means that the opencl drivers for your system are "
                            "not installed.")
                logger.warn(err)

        p_index = 0
        for platform in platforms:
            d_index = 0
            devices = platform.get_devices()
            for device in devices:
                if len(devices) > 1 and len(platforms) > 1:
                    combined_index = ":".join([str(p_index), str(d_index)])
                elif len(platforms) > 1:
                    combined_index = str(p_index)
                else:
                    combined_index = str(d_index)
                clinfo.append((combined_index, ":".join([platform.name, device.name])))
                d_index += 1
            p_index += 1

        clinfo.append(("None", "No OpenCL"))
        return clinfo

    def on_check(self, event):
        """
        Action triggered when box is selected
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

        #If statement added to handle Reset
        if self.sas_opencl:
            os.environ["SAS_OPENCL"] = self.sas_opencl
        else:
            if "SAS_OPENCL" in os.environ:
                del os.environ["SAS_OPENCL"]
        sasmodels.sasview_model.reset_environment()
        event.Skip()

    def on_reset(self, event):
        """
        Resets selected values
        """
        for btn in self.buttons:
            btn.SetValue(0)

        self.sas_opencl = None

    def on_test(self, event):
        """
        Run sasmodels check from here and report results from
        """
        #The same block of code as for OK but it is needed if we want to have
        #active response to Test button

        no_opencl_msg = False
        if self.sas_opencl:
            os.environ["SAS_OPENCL"] = self.sas_opencl
            if self.sas_opencl.lower() == "none":
                no_opencl_msg = True
        else:
            if "SAS_OPENCL" in os.environ:
                del os.environ["SAS_OPENCL"]
        # CRUFT: next version of reset_environment() will return env
        env = sasmodels.sasview_model.reset_environment()

        try:
            env = sasmodels.kernelcl.environment()
            clinfo = {}
            if env.context[F64] is None:
                clinfo['double'] = "None"
            else:
                ctx64 = env.context[F64].devices[0]
                clinfo['double'] = ", ".join((
                    ctx64.platform.vendor,
                    ctx64.platform.version,
                    ctx64.vendor,
                    ctx64.name,
                    ctx64.version))
            if env.context[F32] is None:
                clinfo['single'] = "None"
            else:
                ctx32 = env.context[F32].devices[0]
                clinfo['single'] = ", ".join((
                    ctx32.platform.vendor,
                    ctx32.platform.version,
                    ctx32.vendor,
                    ctx32.name,
                    ctx32.version))
            # If the same device is used for single and double precision, then
            # say so. Whether double is the same as single or single is the
            # same as double depends on the order they are listed below.
            if env.context[F32] == env.context[F64]:
                clinfo['double'] = "same as single precision"
        except Exception as exc:
            logger.debug("exc %s", str(exc))
            clinfo = {'double': "None", 'single': "None"}

        msg = "\nPlatform Details:\n\n"
        msg += "Sasmodels version: "
        msg += sasmodels.__version__ + "\n"
        msg += "\nPlatform used: "
        msg += json.dumps(platform.uname()) + "\n"
        if no_opencl_msg:
            msg += "\nOpenCL driver: None\n"
        else:
            msg += "\nOpenCL driver:\n"
            msg += "   single precision: " + clinfo['single'] + "\n"
            msg += "   double precision: " + clinfo['double'] + "\n"

        msg_title = 'OpenCL tests results'
        running = msg + "\nRunning tests.  This may take several minutes.\n\n"
        msg_dialog = CustomMessageBox(self.panel1, running, msg_title)
        msg_dialog.Show()

        failures = []
        tests_completed = 0
        self.test_btn.Disable()
        tests = sasmodels.model_test.make_suite('opencl', ['all'])
        for test in tests:
            try:
                wx.Yield()
                test.run_all()
                msg_dialog.text.AppendText('.')
            except Exception as exc:
                logger.debug("%s failed with %s", test.test_name, str(exc))
                msg_dialog.text.AppendText('\nFail: ' + test.test_name)
                failures.append(test.test_name)
            tests_completed += 1
            # TODO: Put a stop button in CustomDialog and test it here.
            #if tests_completed > 5: break

        status = 'Failed %d of %d' % (len(failures), tests_completed)
        msg_dialog.text.AppendText('\n\n' + status + '\n')
        self.test_btn.Enable()
        msg_dialog.ShowModal()
        msg_dialog.Destroy()

    def on_help(self, event):
        """
        Provide help on opencl options.
        """
        TreeLocation = "user/sasgui/perspectives/fitting/gpu_setup.html"
        anchor = "#device-selection"
        DocumentationWindow(self, -1,
                            TreeLocation, anchor, "OpenCL Options Help")
