# global
import os
import sys
import sasmodels
import json
import platform
import webbrowser

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from PyQt5 import QtGui, QtCore, QtWidgets
from sas.qtgui.Perspectives.Fitting.UI.GPUOptionsUI import Ui_GPUOptions
from sas.qtgui.Perspectives.Fitting.UI.GPUTestResultsUI import Ui_GPUTestResults

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtWidgets.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig)


class GPUOptions(QtWidgets.QDialog, Ui_GPUOptions):
    """
    OpenCL Dialog to select the desired OpenCL driver
    """

    clicked = False
    sas_open_cl = None

    def __init__(self, parent=None):
        super(GPUOptions, self).__init__(parent)
        self.parent = parent
        self.setupUi(self)
        self.addOpenCLOptions()
        self.createLinks()

    def addOpenCLOptions(self):
        """
        Populate the window with a list of OpenCL options
        """
        # Get list of openCL options and add to GUI
        cl_tuple = _get_clinfo()
        self.sas_open_cl = os.environ.get("SAS_OPENCL", "")
        for title, descr in cl_tuple:
            # Create an item for each openCL option
            check_box = QtWidgets.QCheckBox()
            check_box.setObjectName(_fromUtf8(descr))
            check_box.setText(_translate("GPUOptions", descr, None))
            self.optionsLayout.addWidget(check_box)
            if (descr == self.sas_open_cl) or (
                            title == "None" and not self.clicked):
                check_box.click()
                self.clicked = True
        self.openCLCheckBoxGroup.setMinimumWidth(self.optionsLayout.sizeHint().width()+10)

    def createLinks(self):
        """
        Link user interactions to function calls
        """
        self.testButton.clicked.connect(self.testButtonClicked)
        self.helpButton.clicked.connect(self.helpButtonClicked)
        for item in self.openCLCheckBoxGroup.findChildren(QtWidgets.QCheckBox):
            item.clicked.connect(self.checked)

    def checked(self):
        """
        Only allow a single check box to be selected. Uncheck others.
        """
        checked = None
        for box in self.openCLCheckBoxGroup.findChildren(QtWidgets.QCheckBox):
            if box.isChecked() and (str(box.text()) == self.sas_open_cl or (
                    str(box.text()) == "No OpenCL" and self.sas_open_cl == "")):
                box.setChecked(False)
            elif box.isChecked():
                checked = box
        if hasattr(checked, "text"):
            self.sas_open_cl = str(checked.text())
        else:
            self.sas_open_cl = None

    def set_sas_open_cl(self):
        """
        Set SAS_OPENCL value when tests run or OK button clicked
        """
        no_opencl_msg = False
        if self.sas_open_cl:
            os.environ["SAS_OPENCL"] = self.sas_open_cl
            if self.sas_open_cl.lower() == "none":
                no_opencl_msg = True
        else:
            if "SAS_OPENCL" in os.environ:
                del os.environ["SAS_OPENCL"]
        # Sasmodels kernelcl doesn't exist when initiated with None
        if 'sasmodels.kernelcl' in sys.modules:
            sasmodels.kernelcl.ENV = None
        from importlib import reload # assumed Python > 3.3
        reload(sasmodels.core)
        return no_opencl_msg

    def testButtonClicked(self):
        """
        Run sasmodels check from here and report results from
        """

        no_opencl_msg = self.set_sas_open_cl()

        # Only import when tests are run
        from sasmodels.model_test import model_tests

        try:
            from sasmodels.kernelcl import environment
            env = environment()
            clinfo = [(ctx.devices[0].platform.vendor,
                       ctx.devices[0].platform.version,
                       ctx.devices[0].vendor,
                       ctx.devices[0].name,
                       ctx.devices[0].version)
                      for ctx in env.context]
        except ImportError:
            clinfo = None

        failures = []
        tests_completed = 0
        for test in model_tests():
            try:
                test()
            except Exception:
                failures.append(test.description)

            tests_completed += 1

        info = {
            'version': sasmodels.__version__,
            'platform': platform.uname(),
            'opencl': clinfo,
            'failing tests': failures,
        }

        msg = str(tests_completed) + ' tests completed.\n'
        if len(failures) > 0:
            msg += str(len(failures)) + ' tests failed.\n'
            msg += 'Failing tests: '
            msg += json.dumps(info['failing tests'])
            msg += "\n"
        else:
            msg += "All tests passed!\n"

        msg += "\nPlatform Details:\n\n"
        msg += "Sasmodels version: "
        msg += info['version'] + "\n"
        msg += "\nPlatform used: "
        msg += json.dumps(info['platform']) + "\n"
        if no_opencl_msg:
            msg += "\nOpenCL driver: None"
        else:
            msg += "\nOpenCL driver: "
            msg += json.dumps(info['opencl']) + "\n"
        GPUTestResults(self, msg)

    def helpButtonClicked(self):
        """
        Open the help menu when the help button is clicked
        """
        help_location = GuiUtils.HELP_DIRECTORY_LOCATION
        help_location += "/user/qtgui/Perspectives/Fitting/gpu_setup.html"
        help_location += "#device-selection"
        # Display the page in default browser
        webbrowser.open('file://' + os.path.realpath(help_location))

    def reject(self):
        """
        Close the window without modifying SAS_OPENCL
        """
        self.closeEvent(None)
        self.parent.gpu_options_widget.open()

    def accept(self):
        """
        Close the window after modifying the SAS_OPENCL value
        """
        self.set_sas_open_cl()
        self.closeEvent(None)

    def closeEvent(self, event):
        """
        Overwrite QDialog close method to allow for custom widget close
        """
        self.close()
        self.parent.gpu_options_widget = GPUOptions(self.parent)


class GPUTestResults(QtWidgets.QDialog, Ui_GPUTestResults):
    """
    OpenCL Dialog to modify the OpenCL options
    """
    def __init__(self, parent, msg):
        super(GPUTestResults, self).__init__(parent)
        self.setupUi(self)
        self.resultsText.setText(_translate("GPUTestResults", msg, None))
        #self.setFixedSize(self.size())
        self.open()


def _get_clinfo():
    """
    Read in information about available OpenCL infrastructure
    """
    clinfo = []
    cl_platforms = []
    try:
        import pyopencl as cl
        cl_platforms = cl.get_platforms()
    except ImportError:
        print("pyopencl import failed. Using only CPU computations")
    except cl.LogicError as e:
        print(e.value)

    p_index = 0
    for cl_platform in cl_platforms:
        d_index = 0
        cl_platforms = cl_platform.get_devices()
        for cl_platform in cl_platforms:
            if len(cl_platforms) > 1 and len(cl_platforms) > 1:
                combined_index = ":".join([str(p_index), str(d_index)])
            elif len(cl_platforms) > 1:
                combined_index = str(p_index)
            else:
                combined_index = str(d_index)
            clinfo.append((combined_index, ":".join([cl_platform.name,
                                                     cl_platform.name])))
            d_index += 1
        p_index += 1

    clinfo.append(("None", "No OpenCL"))
    return clinfo
