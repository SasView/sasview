# global
import os
import sys
import json
import platform
import webbrowser
import logging
from twisted.internet import threads
from twisted.internet import reactor

import sasmodels
import sasmodels.model_test
import sasmodels.kernelcl
from sasmodels.generate import F32, F64

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from PyQt5 import QtGui, QtCore, QtWidgets
from sas.qtgui.Perspectives.Fitting.UI.GPUOptionsUI import Ui_GPUOptions
from sas.qtgui.Perspectives.Fitting.UI.GPUTestResultsUI import Ui_GPUTestResults

from sas import config
from sas.system import lib

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

logger = logging.getLogger(__name__)

class GPUOptions(QtWidgets.QDialog, Ui_GPUOptions):
    """
    OpenCL Dialog to select the desired OpenCL driver
    """

    cl_options = None
    testingDoneSignal = QtCore.pyqtSignal(str)
    testingFailedSignal = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(GPUOptions, self).__init__(parent)
        self.parent = parent
        self.setupUi(self)

        self.radio_buttons = []

        # disable the context help icon
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        self.add_options()
        self.progressBar.setVisible(False)
        self.progressBar.setFormat(" Test %v / %m")

        self.testButton.clicked.connect(self.testButtonClicked)
        self.helpButton.clicked.connect(self.helpButtonClicked)
        self.testingDoneSignal.connect(self.testCompleted)
        self.testingFailedSignal.connect(self.testFailed)


    def add_options(self):
        """
        Populate the window with a list of OpenCL options
        """
        # Get list of openCL options and add to GUI
        cl_tuple = _get_clinfo()

        self.cl_options = {}


        for title, descr in cl_tuple:

            # Create an item for each openCL option
            radio_button = QtWidgets.QRadioButton()
            radio_button.setObjectName(_fromUtf8(descr))
            radio_button.setText(_translate("GPUOptions", descr, None))
            self.optionsLayout.addWidget(radio_button)

            if title.lower() == config.SAS_OPENCL.lower():

                radio_button.setChecked(True)

            self.cl_options[descr] = title
            self.radio_buttons.append(radio_button)

        self.openCLCheckBoxGroup.setMinimumWidth(self.optionsLayout.sizeHint().width()+10)

    def set_sas_open_cl(self):
        """
        Set SAS_OPENCL value when tests run or OK button clicked
        """

        checked = None
        for box in self.radio_buttons:
            if box.isChecked():
                checked = box

        if checked is None:
            raise RuntimeError("Error: No radio button selected somehow")

        sas_open_cl = self.cl_options[str(checked.text())]
        no_opencl_msg = sas_open_cl.lower() == "none"
        lib.reset_sasmodels(sas_open_cl)

        return no_opencl_msg

    def testButtonClicked(self):
        """
        Run sasmodels check from here and report results from
        """
        self.model_tests = sasmodels.model_test.make_suite('opencl', ['all'])
        number_of_tests = len(self.model_tests._tests)
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(number_of_tests)
        self.progressBar.setVisible(True)
        self.testButton.setEnabled(False)
        self.okButton.setEnabled(False)
        self.resetButton.setEnabled(False)
        no_opencl_msg = self.set_sas_open_cl()

        test_thread = threads.deferToThread(self.testThread, no_opencl_msg)
        test_thread.addCallback(self.testComplete)
        test_thread.addErrback(self.testFail)

    def testThread(self, no_opencl_msg):
        """
        Testing in another thread
        """
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

        failures = []
        tests_completed = 0
        for counter, test in enumerate(self.model_tests):
            # update the progress bar
            reactor.callFromThread(self.updateCounter, counter)
            try:
                test.run_all()
            except Exception:
                failures.append(test.test_name)
            tests_completed += 1

        info = {
            'version': sasmodels.__version__,
            'platform': platform.uname(),
            'opencl_single': clinfo['single'],
            'opencl_double': clinfo['double'],
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
            msg += "   single precision: " + json.dumps(info['opencl_single']) + "\n"
            msg += "   double precision: " + json.dumps(info['opencl_double']) + "\n"

        return msg

    def updateCounter(self, step):
        """
        Update progress bar with current value
        """
        self.progressBar.setValue(step)
        return

    def testComplete(self, msg):
        """
        Testing done: send signal to main thread with update
        """
        self.testingDoneSignal.emit(msg)

    def testFail(self, msg):
        """
        Testing failed: log the reason
        """
        from twisted.python.failure import Failure
        if isinstance(msg, Failure):
            msg = msg.getErrorMessage()

        self.testingFailedSignal.emit(msg)

    def testFailed(self, msg):
        """
        Testing failed: log the reason
        """
        self.progressBar.setVisible(False)
        self.testButton.setEnabled(True)
        self.okButton.setEnabled(True)
        self.resetButton.setEnabled(True)

        logging.error(str(msg))

    def testCompleted(self, msg):
        """
        Respond to successful test completion
        """
        self.progressBar.setVisible(False)
        self.testButton.setEnabled(True)
        self.okButton.setEnabled(True)
        self.resetButton.setEnabled(True)

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
    except ImportError:
        cl = None

    if cl is None:
        logger.warn("Unable to import the pyopencl package.  It may not "
                    "have been installed.  If you wish to use OpenCL, try "
                    "running pip install --user pyopencl")
    else:
        try:
            cl_platforms = cl.get_platforms()
        except cl.LogicError as err:
            logger.warn("Unable to fetch the OpenCL platforms.  This likely "
                        "means that the opencl drivers for your system are "
                        "not installed.")
            logger.warn(err)

    p_index = 0
    for cl_platform in cl_platforms:
        d_index = 0
        cl_devices = cl_platform.get_devices()
        for cl_device in cl_devices:
            if len(cl_platforms) > 1 and len(cl_devices) > 1:
                combined_index = ":".join([str(p_index), str(d_index)])
            elif len(cl_platforms) > 1:
                combined_index = str(p_index)
            else:
                combined_index = str(d_index)
            clinfo.append((combined_index, ": ".join([cl_platform.name,
                                                     cl_device.name])))
            d_index += 1
        p_index += 1

    clinfo.append(("none", "No OpenCL"))
    return clinfo
