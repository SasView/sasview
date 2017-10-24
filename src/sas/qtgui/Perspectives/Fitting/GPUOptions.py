# global

from PyQt4 import QtGui, QtCore
from sas.qtgui.Perspectives.Fitting.UI.GPUOptionsUI import Ui_GPUOptions

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

    def __init__(self, parent=None):
        super(GPUOptions, self).__init__(parent)
        self.setupUi(self)

        # Get list of openCL options and add to GUI
        cl_tuple = self._get_clinfo()
        i = 0
        for title, descr in cl_tuple:
            button = QtGui.QRadioButton(self.openCLButtonGroup)
            button.setGeometry(20, 20 + i, 351, 30)
            button.setObjectName(_fromUtf8(title))
            button.setText(_translate("GPUOptions", descr, None))
            # Expand group and shift items down as more are added
            self.openCLButtonGroup.resize(391, 60 + i)
            self.pushButton.setGeometry(QtCore.QRect(220, 90 + i, 93, 28))
            self.TestButton.setGeometry(QtCore.QRect(20, 90 + i, 193, 28))
            self.pushButton_2.setGeometry(QtCore.QRect(320, 90 + i, 93, 28))
            self.resize(440, 130 + i)
            i += 30

    def _get_clinfo(self):
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
