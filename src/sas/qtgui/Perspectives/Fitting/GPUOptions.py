# global
import os
import sys
import sasmodels
import json
import platform

from PyQt4 import QtGui, QtCore, QtWebKit
from sas.qtgui.Perspectives.Fitting.UI.GPUOptionsUI import Ui_GPUOptions
from sas.qtgui.Perspectives.Fitting.UI.GPUTestResultsUI import Ui_GPUTestResults

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)


class GPUOptions(QtGui.QDialog, Ui_GPUOptions):
    """
    OpenCL Dialog to modify the OpenCL options
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
        i = 0
        self.sas_open_cl = os.environ.get("SAS_OPENCL", "")
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.CustomizeWindowHint)
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowCloseButtonHint)
        for title, descr in cl_tuple:
            checkBox = QtGui.QCheckBox(self.openCLCheckBoxGroup)
            checkBox.setGeometry(20, 20 + i, 351, 30)
            checkBox.setObjectName(_fromUtf8(descr))
            checkBox.setText(_translate("GPUOptions", descr, None))
            if (descr == self.sas_open_cl) or (title == "None" and not self.clicked):
                checkBox.click()
                self.clicked = True
            # Expand group and shift items down as more are added
            self.openCLCheckBoxGroup.resize(391, 60 + i)
            self.label.setGeometry(QtCore.QRect(20, 90 + i, 391, 37))
            self.okButton.setGeometry(QtCore.QRect(20, 127 + i, 93, 28))
            self.resetButton.setGeometry(QtCore.QRect(120, 127 + i, 93, 28))
            self.testButton.setGeometry(QtCore.QRect(220, 127 + i, 93, 28))
            self.helpButton.setGeometry(QtCore.QRect(320, 127 + i, 93, 28))
            self.resize(440, 167 + i)
            i += 30

    def createLinks(self):
        """
        Link actions to function calls
        """
        self.testButton.clicked.connect(lambda: self.testButtonClicked())
        self.helpButton.clicked.connect(lambda: self.helpButtonClicked())
        for item in self.openCLCheckBoxGroup.findChildren(QtGui.QCheckBox):
            item.clicked.connect(lambda: self.checked())

    def checked(self):
        """
        Action triggered when box is selected
        """
        checked = None
        for box in self.openCLCheckBoxGroup.findChildren(QtGui.QCheckBox):
            if box.isChecked() and (str(box.text()) == self.sas_open_cl or (
                            str(box.text()) == "No OpenCL" and self.sas_open_cl == "")):
                box.setChecked(False)
            elif not box.isChecked():
                pass
            else:
                checked = box
        if hasattr(checked, "text"):
            self.sas_open_cl = str(checked.text())
        else:
            self.sas_open_cl = None

    def set_sas_open_cl(self):
        """
        Set openCL value when tests run or OK button clicked
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

        msg_info = 'OpenCL tests results'

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
        GPUTestResults(self, msg, msg_info)

    def helpButtonClicked(self):
        """
        Open the help menu when the help button is clicked
        """
        tree_location = "user/sasgui/perspectives/fitting/gpu_setup.html"
        anchor = "#device-selection"
        self.helpView = QtWebKit.QWebView()
        help_location = tree_location + anchor
        self.helpView.load(QtCore.QUrl(help_location))
        self.helpView.show()

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


class GPUTestResults(QtGui.QDialog, Ui_GPUTestResults):
    """
    OpenCL Dialog to modify the OpenCL options
    """
    def __init__(self, parent, msg, title):
        super(GPUTestResults, self).__init__(parent)
        self.setupUi(self)
        self.resultsText.setText(_translate("GPUTestResults", msg, None))
        self.open()


def _get_clinfo():
    """
    Reading in information about available OpenCL infrastructure
    :return:
    """
    clinfo = []
    platforms = []
    try:
        import pyopencl as cl
        platforms = cl.get_platforms()
    except ImportError:
        print("pyopencl import failed. Using only CPU computations")

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
