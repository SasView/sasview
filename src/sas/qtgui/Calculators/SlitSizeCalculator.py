"""
Slit Size Calculator Panel
"""
import os
import sys

from PyQt4 import QtGui
from PyQt4 import QtCore

from sas.qtgui.UI import main_resources_rc
import sas.qtgui.Utilities.GuiUtils as GuiUtils

from .UI.SlitSizeCalculator import Ui_SlitSizeCalculator
from sas.sascalc.dataloader.loader import Loader
from sas.sascalc.calculator.slit_length_calculator import SlitlengthCalculator


class SlitSizeCalculator(QtGui.QDialog, Ui_SlitSizeCalculator):
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
        try:
            location = GuiUtils.HELP_DIRECTORY_LOCATION + \
                "/user/sasgui/perspectives/calculator/slit_calculator_help.html"

            self._parent._helpView.load(QtCore.QUrl(location))
            self._parent._helpView.show()
        except AttributeError:
            # No manager defined - testing and standalone runs
            pass

    def onBrowse(self):
        """
        Browse the file and calculate slit lenght upon loading
        """
        path_str = self.chooseFile()
        if not path_str:
            return
        loader = Loader()
        data = loader.load(path_str)[0]

        self.data_file.setText(os.path.basename(path_str))
        self.calculateSlitSize(data)

    def chooseFile(self):
        """
        Shows the Open file dialog and returns the chosen path(s)
        """

        # Location is automatically saved - no need to keep track of the last dir
        # But only with Qt built-in dialog (non-platform native)
        path = QtGui.QFileDialog.getOpenFileName(self, "Choose a file", "",
                                                 "SAXSess 1D data (*.txt *.TXT *.dat *.DAT)",
                                                 QtGui.QFileDialog.DontUseNativeDialog)

        if path is None:
            return

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
            raise RuntimeError(msg)

        if data.__class__.__name__ == 'Data2D':
            self.clearResults()
            msg = "Slit Length cannot be computed for 2D Data"
            raise RuntimeError(msg)

        #compute the slit size
        try:
            xdata = data.x
            ydata = data.y
            if xdata == [] or xdata is None or ydata == [] or ydata is None:
                msg = "The current data is empty please check x and y"
                raise ValueError(msg)
            slit_length_calculator = SlitlengthCalculator()
            slit_length_calculator.set_data(x=xdata, y=ydata)
            slit_length = slit_length_calculator.calculate_slit_length()
        except:
            self.clearResults()
            msg = "Slit Size Calculator: %s" % (sys.exc_info()[1])
            raise RuntimeError(msg)

        slit_length_str = "{:.5f}".format(slit_length)
        self.slit_length_out.setText(slit_length_str)

        #Display unit, which most likely needs to be 1/Ang but needs to be confirmed
        self.unit_out.setText("[Unknown]")

