"""
Slit Size Calculator Panel
"""
import os
import sys
import logging

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from sas.qtgui.UI import main_resources_rc
import sas.qtgui.Utilities.GuiUtils as GuiUtils

from .UI.SlitSizeCalculator import Ui_SlitSizeCalculator
from sas.sascalc.dataloader.loader import Loader
from sas.sascalc.calculator.slit_length_calculator import SlitlengthCalculator


class SlitSizeCalculator(QtWidgets.QDialog, Ui_SlitSizeCalculator):
    """
    Provides the slit length calculator GUI.
    """
    def __init__(self, parent=None):
        super(SlitSizeCalculator, self).__init__()
        self.setupUi(self)

        self.setWindowTitle("Slit Size Calculator")
        self._parent = parent

        self.thickness = SlitlengthCalculator()

        # signals
        self.helpButton.clicked.connect(self.onHelp)
        self.browseButton.clicked.connect(self.onBrowse)
        self.closeButton.clicked.connect(self.onClose)

        # no reason to have this widget resizable
        self.setFixedSize(self.minimumSizeHint())


    def onHelp(self):
        """
        Bring up the Slit Size Calculator calculator Documentation whenever
        the HELP button is clicked.
        Calls DocumentationWindow with the path of the location within the
        documentation tree (after /doc/ ....".
        """
        location = "/user/sasgui/perspectives/calculator/slit_calculator_help.html"
        self._parent.showHelp(location)

    def onBrowse(self):
        """
        Browse the file and calculate slit lenght upon loading
        """
        path_str = self.chooseFile()
        if not path_str:
            return
        loader = Loader()
        try:
            data = loader.load(path_str)
            data = data[0]
        # Can return multiple exceptions - gather them all under one umbrella and complain
        except Exception as ex:
            logging.error(ex)
            return

        self.data_file.setText(os.path.basename(path_str))
        self.calculateSlitSize(data)

    def chooseFile(self):
        """
        Shows the Open file dialog and returns the chosen path(s)
        """

        # Location is automatically saved - no need to keep track of the last dir
        # But only with Qt built-in dialog (non-platform native)
        path = QtWidgets.QFileDialog.getOpenFileName(self, "Choose a file", "",
                                                 "SAXSess 1D data (*.txt *.TXT *.dat *.DAT)",
                                                 None,
                                                 QtWidgets.QFileDialog.DontUseNativeDialog)[0]
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

    def calculateSlitSize(self, data=None):
        """
        Computes slit lenght from given 1D data
        """
        if data is None:
            self.clearResults()
            msg = "ERROR: Data hasn't been loaded correctly"
            logging.error(msg)
            return

        if data.__class__.__name__ == 'Data2D':
            self.clearResults()
            msg = "Slit Length cannot be computed for 2D Data"
            logging.error(msg)
            return

        #compute the slit size
        try:
            xdata = data.x
            ydata = data.y
            #if xdata == [] or xdata is None or ydata == [] or ydata is None:
            if (not xdata or xdata is None) or (not ydata or ydata is None):
                msg = "The current data is empty please check x and y"
                logging.error(msg)
                return
            slit_length_calculator = SlitlengthCalculator()
            slit_length_calculator.set_data(x=xdata, y=ydata)
            slit_length = slit_length_calculator.calculate_slit_length()
        except:
            self.clearResults()
            msg = "Slit Size Calculator: %s" % (sys.exc_info()[1])
            logging.error(msg)
            return

        slit_length_str = "{:.5f}".format(slit_length)
        self.slit_length_out.setText(slit_length_str)

        #Display unit, which most likely needs to be 1/Ang but needs to be confirmed
        self.unit_out.setText("[Unknown]")

