# global
import sys
import os
import types

from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import QtWebKit
from sas.qtgui.Perspectives.Fitting.UI.GPUOptionsUI import Ui_GPUOptions

from bumps import fitters
import bumps.options

# Set the default optimizer
fitters.FIT_DEFAULT_ID = 'lm'


class GPUOptions(QtGui.QDialog, Ui_GPUOptions):
    """
    OpenCL Dialog to modify the OpenCL options
    """

    def __init__(self, parent=None):
        super(GPUOptions, self).__init__(parent)
        self.setupUi(self)


def main():
    app = QtGui.QApplication(sys.argv)

    w = GPUOptions()
    w.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()