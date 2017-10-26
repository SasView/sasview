from PyQt4 import QtGui

# sas-global
from sas.sascalc.invariant import invariant
from sas.qtgui.Plotting.PlotterData import Data1D
import sas.qtgui.Utilities.GuiUtils as GuiUtils

# pr inversion gui elements
from sas.qtgui.Perspectives.PrInversion.UI.TabbedPrInversionUI import Ui_PrInversion

class PrInversionWindow(QtGui.QTabWidget, Ui_PrInversion):
    """
    """

    name = "PrInversion"

    def __init__(self, parent=None, data=None):
        super(PrInversionWindow, self).__init__()
        self.setupUi(self)

        self.setWindowTitle("P(r) Inversion Perspective")

        self.parent = parent
        self._data = data

        # The tabs need to be closeable
        self._allow_close = False

        self.communicate = self.parent.communicator()