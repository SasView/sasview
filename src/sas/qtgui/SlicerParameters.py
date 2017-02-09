"""
Allows users to modify the box slicer parameters.
"""
import functools
from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4 import QtWebKit

# Local UI
from sas.qtgui.UI.SlicerParametersUI import Ui_SlicerParametersUI

class SlicerParameters(QtGui.QDialog, Ui_SlicerParametersUI):
    """
    Interaction between the QTableView and the underlying model,
    passed from a slicer instance.
    """
    close_signal = QtCore.pyqtSignal()
    def __init__(self, model=None):
        super(SlicerParameters, self).__init__()

        self.setupUi(self)
        assert isinstance(model, QtGui.QStandardItemModel)

        self.model = model

        # Define a proxy model so cell enablement can be finegrained.
        self.proxy = ProxyModel(self)
        self.proxy.setSourceModel(self.model)

        # Set the proxy model for display in the Table View.
        self.lstParams.setModel(self.proxy)

        # Disallow edit of the parameter name column.
        self.lstParams.model().setColumnReadOnly(0, True)

        # Specify the validator on the parameter value column.
        self.lstParams.setItemDelegate(ValidatedItemDelegate())

        # Display Help on clicking the button
        self.buttonBox.button(QtGui.QDialogButtonBox.Help).clicked.connect(self.onHelp)

        # Close doesn't trigger closeEvent automatically, so force it
        self.buttonBox.button(QtGui.QDialogButtonBox.Close).clicked.connect(functools.partial(self.closeEvent, None))

        # Disable row number display
        self.lstParams.verticalHeader().setVisible(False)
        self.lstParams.setAlternatingRowColors(True)
        self.lstParams.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Expanding)

        # Header properties for nicer display
        header = self.lstParams.horizontalHeader()
        header.setResizeMode(QtGui.QHeaderView.Stretch)
        header.setStretchLastSection(True)


    def setModel(self, model):
        """ Model setter """
        self.model = model
        self.proxy.setSourceModel(self.model)

    def closeEvent(self, event):
        """
        Overwritten close widget method in order to send the close
        signal to the parent.
        """
        self.close_signal.emit()
        if event:
            event.accept()

    def onHelp(self):
        """
        Display generic data averaging help
        """
        location = "docs/sphinx-docs/build/html" + \
            "/user/sasgui/guiframe/graph_help.html#d-data-averaging"
        self.helpView = QtWebKit.QWebView()
        self.helpView.load(QtCore.QUrl(location))
        self.helpView.show()


class ProxyModel(QtGui.QIdentityProxyModel):
    """
    Trivial proxy model with custom column edit flag
    """
    def __init__(self, parent=None):
        super(ProxyModel, self).__init__(parent)
        self._columns = set()

    def columnReadOnly(self, column):
        '''Returns True if column is read only, false otherwise'''
        return column in self._columns

    def setColumnReadOnly(self, column, readonly=True):
        '''Add/removes a column from the readonly list'''
        if readonly:
            self._columns.add(column)
        else:
            self._columns.discard(column)

    def flags(self, index):
        '''Sets column flags'''
        flags = super(ProxyModel, self).flags(index)
        if self.columnReadOnly(index.column()):
            flags &= ~QtCore.Qt.ItemIsEditable
        return flags


class ValidatedItemDelegate(QtGui.QStyledItemDelegate):
    """
    Simple delegate enabling adding a validator to a cell editor.
    """
    def createEditor(self, widget, option, index):
        '''Overwrite default editor'''
        if not index.isValid():
            return 0
        if index.column() == 1: # Edir only cells in the second column
            editor = QtGui.QLineEdit(widget)
            validator = QtGui.QDoubleValidator()
            # Don't use the scientific notation, cause 'e'.
            validator.setNotation(QtGui.QDoubleValidator.StandardNotation)
            editor.setValidator(validator)
            return editor
        return super(ValidatedItemDelegate, self).createEditor(widget, option, index)
