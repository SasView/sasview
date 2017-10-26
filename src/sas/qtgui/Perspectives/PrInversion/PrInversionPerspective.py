from PyQt4 import QtGui, QtCore, QtWebKit

# sas-global
#import sas.qtgui.Utilities.GuiUtils as GuiUtils

# pr inversion gui elements
from sas.qtgui.Perspectives.PrInversion.UI.TabbedPrInversionUI import \
    Ui_PrInversion

class PrInversionWindow(QtGui.QTabWidget, Ui_PrInversion):
    """
    """

    name = "PrInversion"

    def __init__(self, parent=None, data=None):
        super(PrInversionWindow, self).__init__()
        self.setupUi(self)

        self.setWindowTitle("P(r) Inversion Perspective")

        self._manager = parent

        self._model_item = QtGui.QStandardItem()
        self._helpView = QtWebKit.QWebView()
        self._data = data

        # The tabs need to be closeable
        self._allow_close = False

        # Let's choose the Standard Item Model.
        self.model = QtGui.QStandardItemModel(self)

    def allowBatch(self):
        return False

    def setClosable(self, value=True):
        """
        Allow outsiders close this widget
        """
        assert isinstance(value, bool)
        self._allow_close = value

    def closeEvent(self, event):
        """
        Overwrite QDialog close method to allow for custom widget close
        """
        if self._allow_close:
            # reset the closability flag
            self.setClosable(value=False)
            event.accept()
        else:
            event.ignore()
            # Maybe we should just minimize
            self.setWindowState(QtCore.Qt.WindowMinimized)
