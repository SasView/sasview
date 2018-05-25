from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from sas.qtgui.UI import main_resources_rc
from .UI.KiessigPanel import Ui_KiessigPanel
import sas.qtgui.Utilities.GuiUtils as GuiUtils

# sas-global
from sas.sascalc.calculator.kiessig_calculator import KiessigThicknessCalculator


class KiessigPanel(QtWidgets.QDialog, Ui_KiessigPanel):
    def __init__(self, parent=None):
        super(KiessigPanel, self).__init__()
        self.setupUi(self)

        self.setWindowTitle("Kiessig Thickness Calculator")

        self.manager = parent
        self.thickness = KiessigThicknessCalculator()

        self.deltaq_in.setText("0.05")

        # signals
        self.helpButton.clicked.connect(self.onHelp)
        self.computeButton.clicked.connect(self.onCompute)
        self.closeButton.clicked.connect(self.onClose)

        # no reason to have this widget resizable
        self.setFixedSize(self.minimumSizeHint())

    def onHelp(self):
        """
        Bring up the Kiessig fringe calculator Documentation whenever
        the HELP button is clicked.
        Calls DocumentationWindow with the path of the location within the
        documentation tree (after /doc/ ....".
        """
        location = "/user/qtgui/Calculators/kiessig_calculator_help.html"
        self.manager.showHelp(location)

    def onCompute(self):
        """
        Execute the computation of thickness
        """
        try:
            self.thickness.set_deltaq(dq=float(self.deltaq_in.text()))
            kiessing_result = self.thickness.compute_thickness()
            if kiessing_result:
                float_as_str = "{:.3f}".format(kiessing_result)
                self.lengthscale_out.setText(float_as_str)
            else:
                # error or division by zero
                self.lengthscale_out.setText("")

        except (ArithmeticError, ValueError):
            self.lengthscale_out.setText("")

    def onClose(self):
        """
        close the window containing this panel
        """
        self.close()
