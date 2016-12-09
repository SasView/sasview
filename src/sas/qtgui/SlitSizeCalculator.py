from PyQt4 import QtGui
from PyQt4 import QtCore
from UI.SlitSizeCalculator import Ui_SlitSizeCalculator

# sas-global
from sas.sascalc.calculator.slit_length_calculator import SlitlengthCalculator


class SlitSizeCalculator(QtGui.QDialog, Ui_SlitSizeCalculator):
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
        Bring up the Kiessig fringe calculator Documentation whenever
        the HELP button is clicked.
        Calls DocumentationWindow with the path of the location within the
        documentation tree (after /doc/ ....".
        """
        try:
            location = self._parent.HELP_DIRECTORY_LOCATION + \
                "/user/sasgui/perspectives/calculator/slit_lenght_calculator.html"

            self._parent._helpView.load(QtCore.QUrl(location))
            self._parent._helpView.show()
        except AttributeError:
            # No manager defined - testing and standalone runs
            pass

    def onBrowse(self):
        """
        Execute the computation of thickness
        """
        path_str = self.chooseFiles()
        if not path_str:
            return
        self.loadFromURL(path_str)

    def loadFromURL(self, url):
        """
        Threaded file load
        """
        load_thread = threads.deferToThread(self.readData, url)
        load_thread.addCallback(self.loadComplete)

    def chooseFiles(self):
        """
        Shows the Open file dialog and returns the chosen path(s)
        """

        # Location is automatically saved - no need to keep track of the last dir
        # But only with Qt built-in dialog (non-platform native)
        paths = QtGui.QFileDialog.getOpenFileNames(self, "Choose a file", "",
                "Scattering data (*.DAT, *.dat)", None, QtGui.QFileDialog.DontUseNativeDialog)
        if paths is None:
            return

        if isinstance(paths, QtCore.QStringList):
            paths = [str(f) for f in paths]

        if not isinstance(paths, list):
            paths = [paths]

        return paths

    def onClose(self):
        """
        close the window containing this panel
        """
        self.close()
