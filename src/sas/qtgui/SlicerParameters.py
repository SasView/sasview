"""
Allows users to modify the box slicer parameters.
"""
from PyQt4 import QtGui
from PyQt4 import QtCore

# Local UI
from sas.qtgui.UI.SlicerParametersUI import Ui_SlicerParametersUI

class SlicerParameters(QtGui.QDialog, Ui_SlicerParametersUI):
    """
    Interaction between the QTableView and the underlying model,
    passed from a slicer instance.
    """
    def __init__(self, parent=None, model=None):
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

class ProxyModel(QtGui.QIdentityProxyModel):
    """
    Trivial proxy model with custom column edit flag
    """
    def __init__(self, parent=None):
        super(ProxyModel, self).__init__(parent)
        self._columns = set()

    def columnReadOnly(self, column):
        return column in self._columns

    def setColumnReadOnly(self, column, readonly=True):
        if readonly:
            self._columns.add(column)
        else:
            self._columns.discard(column)

    def flags(self, index):
        flags = super(ProxyModel, self).flags(index)
        if self.columnReadOnly(index.column()):
            flags &= ~QtCore.Qt.ItemIsEditable
        return flags


class ValidatedItemDelegate(QtGui.QStyledItemDelegate):
    """
    Simple delegate enabling adding a validator to a cell editor.
    """
    def createEditor(self, widget, option, index):
        if not index.isValid():
            return 0
        if index.column() == 1: # Edir only cells in the second column
            editor = QtGui.QLineEdit(widget)
            validator = QtGui.QDoubleValidator()
            editor.setValidator(validator)
            return editor
        return super(ValidatedItemDelegate, self).createEditor(widget, option, index)
