from PyQt4 import QtGui
from PyQt4 import QtCore
from UI.SlitSizeCalculator import Ui_SlitSizeCalculator
from sas.sascalc.dataloader.loader import Loader
from sas.sasgui.guiframe.dataFitting import Data1D
from sas.sasgui.guiframe.dataFitting import Data2D
from sas.sascalc.calculator.slit_length_calculator import SlitlengthCalculator

import sys

class SlitSizeCalculator(QtGui.QDialog, Ui_SlitSizeCalculator):
    def __init__(self, parent=None, guimanager=None, manager=None):
        super(SlitSizeCalculator, self).__init__()
        self.setupUi(self)

        self.setWindowTitle("Slit Size Calculator")
        self._parent = parent
        self._guimanager = guimanager
        self._manager = manager

        self.thickness = SlitlengthCalculator()

        # signals
        self.helpButton.clicked.connect(self.onHelp)
        self.browseButton.clicked.connect(self.onBrowse)
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
        try:
            location = self._parent.HELP_DIRECTORY_LOCATION + \
                "/user/sasgui/perspectives/calculator/slit_calculator_help.html"

            self._parent._helpView.load(QtCore.QUrl(location))
            self._parent._helpView.show()
        except AttributeError:
            # No manager defined - testing and standalone runs
            pass

    def onBrowse(self):
        """
        Execute the computation of thickness
        """
        path_str = self.chooseFile()
        if not path_str:
            return
        loader = Loader()
        data = loader.load(path_str)

        self.deltaq_in.setText(path_str)
        #We are loading data for one model only therefor index 0
        self.complete_loading(data)
        #Complete loading here

    def chooseFile(self):
        """
        Shows the Open file dialog and returns the chosen path(s)
        """

        # Location is automatically saved - no need to keep track of the last dir
        # But only with Qt built-in dialog (non-platform native)
        path = QtGui.QFileDialog.getOpenFileName(self, "Choose a file", "",
                "SAS data 1D (*.txt *.TXT *.dat *.DAT)", None,
                QtGui.QFileDialog.DontUseNativeDialog)
        if path is None:
            return

        if isinstance(path, QtCore.QString):
            path = str(path)

        return path

    def onClose(self):
        """
        close the window containing this panel
        """
        self.close()

    def complete_loading(self, data=None):
        """
            Complete the loading and compute the slit size
        """

        if data is None:
            msg = "ERROR: Data hasn't been loaded correctly"
            raise RuntimeError, msg

        if isinstance(data, Data2D):
            msg = "Slit Length cannot be computed for 2D Data"
            raise Exception, msg

        #compute the slit size
        try:
             x = data.x
             y = data.y
             if x == [] or  x is None or y == [] or y is None:
                 msg = "The current data is empty please check x and y"
                 raise ValueError, msg
             slit_length_calculator = SlitlengthCalculator()
             slit_length_calculator.set_data(x=x, y=y)
             slit_length = slit_length_calculator.calculate_slit_length()
        except:
             msg = "Slit Size Calculator: %s" % (sys.exc_value)
             raise RuntimeError, msg

        print("Slit lenght", slit_length)
        self.lengthscale_out.setText(str(slit_length))
        #Display unit
        self.lineEdit.setText("[UNKNOWN]")

