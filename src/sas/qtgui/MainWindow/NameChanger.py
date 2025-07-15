import os

from PySide6 import QtWidgets

from sas.qtgui.Utilities import GuiUtils

from .UI.ChangeNameUI import Ui_ChangeCategoryUI


class ChangeName(QtWidgets.QDialog, Ui_ChangeCategoryUI):
    def __init__(self, parent=None):
        super(ChangeName, self).__init__(parent)

        self._data = None
        self._model_item = None
        self.setupUi(self)

        self.setModal(True)

        self.parent = parent
        self.communicator = self.parent.communicator
        self.communicator.dataDeletedSignal.connect(self.removeData)
        self.manager = self.parent.manager

        self.setWindowTitle("Display Name Change")

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
    def model_item(self, val=None):
        # Explicit check for None or HashableStandardItem
        assert isinstance(val, (GuiUtils.HashableStandardItem, type(None)))
        self._model_item = val
        self.data = GuiUtils.dataFromItem(self._model_item)

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, val=None):
        self._data = val
        # Set values to base state
        self.txtCurrentName.setText("")
        self.txtDataName.setText("")
        self.txtFileName.setText("")
        self.txtNewCategory.setText("")
        if val:
            self.rbExisting.setChecked(True)
            self.txtCurrentName.setText(self._model_item.text())
            self.txtDataName.setText(self._data.title)
            self.txtFileName.setText(os.path.basename(self._data.filename))

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
        if self.rbExisting.isChecked() or (self.rbNew.isChecked() and not str(self.txtNewCategory.text())):
            # Do not attempt to change the name if existing name is selected or new string is blank
            return
        buttonStates = [self.rbDataName.isChecked(), self.rbFileName.isChecked(), self.rbNew.isChecked()]
        textValues = [self.txtDataName.text(), self.txtFileName.text(), self.txtNewCategory.text()]
        newValues = [textValues[i] for i, value in enumerate(textValues) if buttonStates[i]]
        # Only rename if there is a single value returned.
        if len(newValues) == 1:
            # Remove name from data name dictionary to prevent infinite [n] generation
            self.manager.remove_item_from_data_name_dict(self._data.name)
            # Create a unique name based on the value set
            new_name = self.manager.rename(newValues[0])
            self._data.name = new_name
            self._model_item.setData(self._data)
            self._model_item.setText(new_name)

    def removeData(self, data_list=None):
        """
        Safely remove data from the window in the unlikely event a data deletion signal is sent to the modal window
        """
        if not data_list or self._model_item not in data_list:
            return
        # Reset model_item and data to None and close the window
        self.model_item = None
        self.close()

    def close(self, retVal=False):
        """
        Return a value - hide the window for now
        """
        self.hide()
        if retVal:
            self.getNewText()
