"""
Slit Size Calculator Panel
"""
import logging
import os
import sys

from PySide6 import QtWidgets

from sasdata import dataset_types
from sasdata.data import SasData
from sasdata.data_io.importers.import_ascii import load_data_default_params

from sas.qtgui.Calculators.calculator_tool import CalculatorTool
from sas.qtgui.UI import main_resources_rc  # noqa: F401
from sas.sascalc.calculator.slit_length_calculator import SlitlengthCalculator

from .UI.SlitSizeCalculator import Ui_SlitSizeCalculator

logger = logging.getLogger(__name__)


class SlitSizeCalculator(CalculatorTool, QtWidgets.QDialog, Ui_SlitSizeCalculator):
    """
    Provides the slit length calculator GUI.
    """
    help_url = "/user/qtgui/Calculators/slit_calculator_help.html"

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.setupUi(self)

        self.setWindowTitle("Slit Size Calculator")

        self.thickness = SlitlengthCalculator()

        # signals
        self.helpButton.clicked.connect(self.onHelp)
        self.browseButton.clicked.connect(self.onBrowse)
        self.closeButton.clicked.connect(self.onClose)

        # no reason to have this widget resizable
        self.setFixedSize(self.minimumSizeHint())


    def onBrowse(self):
        """
        Browse the file and calculate slit lenght upon loading
        """
        path_str = self.chooseFile()
        if not path_str:
            return
        try:
            data = self.loadFile(path_str)
        # Can return multiple exceptions - gather them all under one umbrella and complain
        except Exception as ex:
            logger.error(ex)
            return

        self.data_file.setText(os.path.basename(path_str))
        self.calculateSlitSize(data)

    @staticmethod
    def loadFile(path: str) -> SasData:
        """Load a beam profile (e.g. a SAXSess .DAT/.TXT export) with the sasdata ASCII importer.

        The file's columns, header length and 1D/2D type are guessed by sasdata.
        """
        return load_data_default_params(path)[0]

    def chooseFile(self):
        """
        Shows the Open file dialog and returns the chosen path(s)
        """

        # Location is automatically saved - no need to keep track of the last dir
        # But only with Qt built-in dialog (non-platform native)
        path = QtWidgets.QFileDialog.getOpenFileName(self, "Choose a file", "",
                                                 "SAXSess 1D data (*.txt *.TXT *.dat *.DAT)",
                                                 None)[0]
        return path

    def onClose(self):
        """
        close the window containing this panel
        """
        self.close()

    def clearResults(self):
        """
        Clear the content of output LineEdits
        """
        self.slit_length_out.setText("ERROR!")
        self.unit_out.clear()

    def calculateSlitSize(self, data: SasData | None = None):
        """
        Computes slit length from given 1D data
        """
        if data is None:
            self.clearResults()
            msg = "ERROR: Data hasn't been loaded correctly"
            logger.error(msg)
            return

        if data.dataset_type != dataset_types.one_dim:
            self.clearResults()
            msg = "Slit Length cannot be computed for 2D Data"
            logger.error(msg)
            return

        #compute the slit size
        try:
            xdata = data.abscissae.axes[0].value
            ydata = data.ordinate.value
            if xdata is None or len(xdata) == 0 or ydata is None or len(ydata) == 0:
                # Don't leave the previous file's result on display.
                self.clearResults()
                msg = "The current data is empty please check x and y"
                logger.error(msg)
                return
            slit_length_calculator = SlitlengthCalculator()
            slit_length_calculator.set_data(x=xdata, y=ydata)
            slit_length = slit_length_calculator.calculate_slit_length()
        except:
            self.clearResults()
            msg = "Slit Size Calculator: %s" % (sys.exc_info()[1])
            logger.error(msg)
            return

        slit_length_str = f"{slit_length:.5f}"
        self.slit_length_out.setText(slit_length_str)

        # The file doesn't state its Q unit, and the importer's unit is only its
        # default guess, so don't claim one.
        self.unit_out.setText("[Unknown]")

