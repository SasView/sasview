from PyQt4 import QtGui
from PyQt4 import QtCore
from UI.KiessigPanel import Ui_KiessigPanel

# sas-global
from sas.sascalc.calculator.kiessig_calculator import KiessigThicknessCalculator


class KiessigPanel(QtGui.QDialog, Ui_KiessigPanel):
    def __init__(self, parent=None):
        super(KiessigPanel, self).__init__()
        self.setupUi(self)

        self.setWindowTitle("Kiessig Thickness Calculator")

        self.manager = parent
        self.thickness = KiessigThicknessCalculator()

        # signals
        self.helpButton.clicked.connect(self.on_help)
        self.computeButton.clicked.connect(self.on_compute)
        self.closeButton.clicked.connect(self.on_close)

        # no reason to have this widget resizable
        self.setFixedSize(self.minimumSizeHint())

    def on_help(self):
        """
        Bring up the Kiessig fringe calculator Documentation whenever
        the HELP button is clicked.
        Calls DocumentationWindow with the path of the location within the
        documentation tree (after /doc/ ....".
        """
        try:
            location = self.manager.HELP_DIRECTORY_LOCATION + \
                "/user/sasgui/perspectives/calculator/kiessig_calculator_help.html"

            self.manager._helpView.load(QtCore.QUrl(location))
            self.manager._helpView.show()
        except AttributeError:
            # No manager defined - testing and standalone runs
            pass

    def on_compute(self):
        """
        Execute the computation of thickness
        """
        try:
            self.thickness.set_deltaq(dq=float(self.deltaq_in.text()))
            kiessing_result = self.thickness.compute_thickness()
            float_as_str = "{:5.4f}".format(kiessing_result)
            self.lengthscale_out.setText(float_as_str)
        except (ArithmeticError, ValueError):
            self.lengthscale_out.setText("")

    def on_close(self):
        """
        close the window containing this panel
        """
        self.close()
