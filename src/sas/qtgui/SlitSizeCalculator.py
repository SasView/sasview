from PyQt4 import QtGui
from PyQt4 import QtCore
from UI.SlitSizeCalculator import Ui_SlitSizeCalculator
from twisted.internet import threads
import logging

# sas-global
from sas.sascalc.calculator.slit_length_calculator import SlitlengthCalculator
from DataExplorer import DataExplorerWindow

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
        path_str = self.chooseFiles()
        if not path_str:
            return
        self.loadFromURL(path_str)
        #Path_str is a list - it needs to be changed, so that only one file can be uploaded
        self.deltaq_in.setText(path_str[0])

    def loadFromURL(self, url):
        """
        Threaded file load
        """
        data_explorer = DataExplorerWindow(parent=self._parent, guimanager=self._guimanager)
        load_thread = threads.deferToThread(data_explorer.readData, url)
        load_thread.addCallback(data_explorer.loadComplete)
        #On complete loading

    def chooseFiles(self):
        """
        Shows the Open file dialog and returns the chosen path(s)
        """

        # Location is automatically saved - no need to keep track of the last dir
        # But only with Qt built-in dialog (non-platform native)
        paths = QtGui.QFileDialog.getOpenFileNames(self, "Choose a file", "",
                "SAXSess Data 1D (*.txt *.TXT *.dat *.DAT)", None,
                QtGui.QFileDialog.DontUseNativeDialog)
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

    def complete_loading(self, data=None):
        """
            Complete the loading and compute the slit size
        """
        #TODO: Provided we have an access to data then it should be fairly easy
        index = self.treeView.selectedIndexes()[0]
        model_item = self.model.itemFromIndex(self.data_proxy.mapToSource(index))
        data = GuiUtils.dataFromItem(model_item)

        if data is None or isinstance(data, Data2D):
            #I guess this doesn't apply
            if self.parent.parent is None:
                return
            msg = "Slit Length cannot be computed for 2D Data"
            logging.info(msg)
            return
        self.data_name_tcl.SetValue(str(data.filename))
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
            if self.parent.parent is None:
                return
            msg = "Slit Size Calculator: %s" % (sys.exc_value)
            logging.info(msg)
            return
        self.slit_size_tcl.SetValue(str(slit_length))
        #Display unit
        self.slit_size_unit_tcl.SetValue('[Unknown]')
        if self.parent.parent is None:
            return
        msg = "Load Complete"
        logging.info(msg)

