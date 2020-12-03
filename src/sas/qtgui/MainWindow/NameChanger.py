import os

from PyQt5 import QtWidgets, QtCore

from sas.qtgui.Utilities import GuiUtils

from .UI.ChangeNameUI import Ui_ChangeCategoryUI


class ChangeName(QtWidgets.QDialog, Ui_ChangeCategoryUI):
    def __init__(self, parent=None):
        super(ChangeName, self).__init__(parent)
        self.setupUi(self)

        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)

        self.setWindowTitle("Display Name Change")
        self._data = None
        self._model_item = None

        # Disable the inputs
        self.txtCurrentName.setEnabled(False)
        self.txtDataName.setEnabled(False)
        self.txtFileName.setEnabled(False)
        self.txtNewCategory.setEnabled(False)

        self.addActions()

    @property
    def model_item(self):
        return self._model_item

    @model_item.setter
    def model_item(self, val):
        assert isinstance(val, GuiUtils.HashableStandardItem)
        self._model_item = val
        self.data = GuiUtils.dataFromItem(self._model_item)

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, var=None):
        if var:
            self._data = var
            self.rbExisting.setChecked(True)
            self.txtCurrentName.setText(self._model_item.text())
            self.txtDataName.setText(self._data.title)
            self.txtFileName.setText(os.path.basename(self._data.filename))
            self.txtNewCategory.setText("")

    def addActions(self):
        """
        Add actions for buttons
        """
        # Close actions - return selected value on ok, otherwise just close
        self.cmdCancel.clicked.connect(lambda: self.close(False))
        self.cmdOK.clicked.connect(lambda: self.close(True))
        self.rbNew.toggled.connect(lambda: self.txtNewCategory.setEnabled(self.rbNew.isChecked()))

    def getNewText(self):
        """
        Find the radio button that is selected and find its associated textbox
        """
        buttonStates = [self.rbExisting.isChecked(), self.rbDataName.isChecked(),
                   self.rbFileName.isChecked(), self.rbNew.isChecked()]
        textValues = [self.txtCurrentName.text(), self.txtDataName.text(),
                      self.txtFileName.text(), self.txtNewCategory.text()]
        newValues = [textValues[i] for i, value in enumerate(textValues) if buttonStates[i]]
        name = newValues[0] if len(newValues) == 1 and newValues[0] else self.txtCurrentName.text()
        self._model_item.setText(name)

    def close(self, retVal=False):
        """
        Return a value - hide the window for now
        """
        self.hide()
        if retVal:
            self.getNewText()
