import logging
import os.path

from PySide6 import QtCore, QtGui, QtWidgets

from sas.qtgui.Utilities import GuiUtils
from sas.qtgui.Utilities.ModelEditors.TabbedEditor.UI.PluginDefinitionUI import Ui_PluginDefinition
from sas.system.user import find_plugins_dir

MODEL_TEXT = """intensity = q

return intensity
"""

VOLUME_TEXT = """volume = M_4PI_3 * {0}**3

return volume
"""


def remove_empty_table_rows(tbl: QtWidgets.QTableWidget):
    """A helper function to remove empty rows in a PySide Table, if there are more than two empty rows at the end.
    This function ensures there is always an empty row in the table.

    :param tbl: A QTableWidget on i rows and j columns.
    """
    for i in range(tbl.rowCount() -1, -1 , -1):
        for j in range(0, tbl.columnCount()):
            cell_contents = tbl.item(i, j)
            if cell_contents is None or cell_contents.text() == "":
                # cell_contents may be None: Ensure this check remains, otherwise the .text() call may throw an error
                pass
            else:
                break
        else:
            tbl.removeRow(i)
    tbl.insertRow(tbl.rowCount())


class PluginDefinition(QtWidgets.QDialog, Ui_PluginDefinition):
    """
    Class describing the "simple" plugin editor.
    This is a simple series of widgets allowing for specifying
    model form and parameters.
    """
    modelModified = QtCore.Signal()
    omitPolydisperseFuncsSignal = QtCore.Signal()
    includePolydisperseFuncsSignal = QtCore.Signal()
    enablePyCheckboxSignal = QtCore.Signal()
    sendNewParamSignal = QtCore.Signal(list)
    sendNewDescriptionSignal = QtCore.Signal(str)
    sendNewIqSignal = QtCore.Signal(str)
    sendNewFormVolumeSignal = QtCore.Signal(str)

    def __init__(self, parent: QtWidgets.QWidget = None):
        super(PluginDefinition, self).__init__(parent)

        self.setupUi(self)

        self.infoLabel.setVisible(False)

        # globals
        self.initializeModel()
        # internal representation of the parameter list
        # {<row>: (<parameter>, <value>)}
        self.parameter_dict = {}
        self.pd_parameter_dict = {}
        self.displayed_default_form_volume = False

        # Initialize widgets
        self.addWidgets()

        # Wait for all widgets to finish processing
        QtWidgets.QApplication.processEvents()

        # Initialize signals
        self.addSignals()

    def addTooltips(self):
        """
        Add the default tooltips to the Iq and form_volume function text boxes
        """
        hint_function = "This function returns the scattering intensity for a given q.\n"
        hint_function += "Example:\n\n"
        hint_function += "if q <= 0:\n"
        hint_function += "    intensity = A + B\n"
        hint_function += "else:\n"
        hint_function += "    intensity = A + B * cos(2 * pi * q)\n"
        hint_function += "return intensity\n"
        self.txtFunction.setToolTip(hint_function)
        hint_function = "This function returns the volume of the particle.\n"
        hint_function += "Example:\n\n"
        hint_function += "volume = (4 / 3) * pi * R**3\n"
        hint_function += "return volume\n"
        self.txtFormVolumeFunction.setToolTip(hint_function)

    def addWidgets(self):
        """
        Initialize various widgets in the dialog
        """
        self.addTooltips()

        # Initial text in the function table
        text = MODEL_TEXT
        self.model['func_text'] = text
        self.txtFunction.insertPlainText(text)
        self.txtFunction.setFont(GuiUtils.getMonospaceFont())

        self.txtFormVolumeFunction.setFont(GuiUtils.getMonospaceFont())

        # Validators
        rx = QtCore.QRegularExpression("^[A-Za-z0-9_]*$")

        txt_validator = QtGui.QRegularExpressionValidator(rx)
        self.txtName.setValidator(txt_validator)
        # Weird import location - workaround for a bug in Sphinx choking on
        # importing QSyntaxHighlighter
        # DO NOT MOVE TO TOP
        from sas.qtgui.Utilities.PythonSyntax import PythonHighlighter
        self.highlightFunction = PythonHighlighter(self.txtFunction.document())
        self.highlightFormVolumeFunction = PythonHighlighter(self.txtFormVolumeFunction.document())

        self.setModelTypeCheckBoxEnabledState("")

    def initializeModel(self):
        """
        Define the dictionary for internal data representation
        """
        # Define the keys
        self.model = {
            'filename':'',
            'overwrite':False,
            'gen_python':True,
            'gen_c':False,
            'description':'',
            'parameters':{},
            'pd_parameters':{},
            'func_text':'',
            'form_volume_text':''
            }

    def addSignals(self):
        """
        Define slots for widget signals
        """
        self.txtName.textChanged.connect(self.onPluginNameChanged)
        self.txtDescription.textChanged.connect(self.onDescriptionChanged)
        self.tblParams.cellChanged.connect(self.onParamsChanged)
        self.tblParamsPD.cellChanged.connect(self.onParamsPDChanged)
        # QTextEdit doesn't have a signal for edit finish, so we respond to text changed.
        # Possibly a slight overkill.
        self.txtFunction.textChanged.connect(self.onFunctionChanged)
        self.txtFormVolumeFunction.textChanged.connect(self.onFormVolumeFunctionChanged)
        self.chkOverwrite.toggled.connect(self.onOverwrite)
        self.chkGenPython.toggled.connect(self.onGenPython)
        self.chkGenC.toggled.connect(self.onGenC)
        self.enablePyCheckboxSignal.connect(lambda: self.checkPyModelExists(self.model['filename']))
        self.sendNewParamSignal.connect(self.updateParamTableFromEditor)
        self.sendNewDescriptionSignal.connect(lambda description: self.txtDescription.setText(description))
        self.sendNewIqSignal.connect(lambda iq: self.txtFunction.setPlainText(iq))
        self.sendNewFormVolumeSignal.connect(lambda form_volume: self.txtFormVolumeFunction.setPlainText(form_volume))

        #Boolean flags
        self.chkSingle.clicked.connect(self.modelModified.emit)
        self.chkOpenCL.clicked.connect(self.modelModified.emit)
        self.chkStructure.clicked.connect(self.modelModified.emit)
        self.chkFQ.clicked.connect(self.modelModified.emit)

    def onPluginNameChanged(self):
        """
        Respond to changes in plugin name
        """
        self.model['filename'] = self.txtName.text()

        self.checkPyModelExists(self.model['filename'])

        self.modelModified.emit()

    def onDescriptionChanged(self):
        """
        Respond to changes in plugin description
        """
        self.model['description'] = self.txtDescription.text()
        self.modelModified.emit()

    def onParamsChanged(self, row: int, column: int):
        """
        Respond to changes in non-polydisperse parameter table
        """
        param = value = None
        if self.tblParams.item(row, 0):
            param = self.tblParams.item(row, 0).data(0)
        if self.tblParams.item(row, 1):
            value = self.tblParams.item(row, 1).data(0)

        # If modified, just update the dict
        self.parameter_dict[row] = (param, value)
        self.model['parameters'] = self.parameter_dict

        # Check if there are empty rows.
        remove_empty_table_rows(self.tblParams)

        self.modelModified.emit()

    def onParamsPDChanged(self, row: int, column: int):
        """
        Respond to changes in polydisperse parameter table
        """
        param = value = None
        if self.tblParamsPD.item(row, 0):
            param = self.tblParamsPD.item(row, 0).data(0)
        if self.tblParamsPD.item(row, 1):
            value = self.tblParamsPD.item(row, 1).data(0)

        # If modified, just update the dict
        self.pd_parameter_dict[row] = (param, value)
        self.model['pd_parameters'] = self.pd_parameter_dict

        # Check if there are empty rows.
        remove_empty_table_rows(self.tblParamsPD)

        # Check to see if there is any polydisperse parameter text presen
        for row in range(self.tblParamsPD.rowCount()):
            if any(self._checkCell(row, column) for column in range(self.tblParamsPD.columnCount())):
                break

        self.modelModified.emit()

    def _checkCell(self, row: int, column: int) -> bool:
        """Check the cell at the particular location (row, column) to see if it has any value."""
        table_cell_contents = self.tblParamsPD.item(row, column)
        if table_cell_contents and table_cell_contents.text():
            # There is text in at least one cell
            if not self.displayed_default_form_volume:
                text = VOLUME_TEXT.format(self.model['pd_parameters'][0][0])
                self.model['form_volume_text'] = text
                self.txtFormVolumeFunction.insertPlainText(text)
                self.displayed_default_form_volume = True

            self.formFunctionBox.setVisible(True)
            self.includePolydisperseFuncsSignal.emit()
        else:
            # Hide the Form Function box because there are no polydisperse parameters
            self.formFunctionBox.setVisible(False)
            self.omitPolydisperseFuncsSignal.emit()
        return (table_cell_contents and table_cell_contents.text())

    def onFunctionChanged(self):
        """
        Respond to changes in function body
        """
        # keep in mind that this is called every time the text changes.
        # mind the performance!
        new_text = self.txtFunction.toPlainText().lstrip().rstrip()
        if new_text != self.model['func_text']:
            self.model['func_text'] = new_text
            self.modelModified.emit()

    def onFormVolumeFunctionChanged(self):
        """
        Respond to changes in form volume function body
        """
        # keep in mind that this is called every time the text changes.
        # mind the performance!
        new_text = self.txtFormVolumeFunction.toPlainText().lstrip().rstrip()
        if new_text != self.model['form_volume_text']:
            self.model['form_volume_text'] = new_text
            self.modelModified.emit()

    def onOverwrite(self):
        """
        Respond to change in file overwrite checkbox
        """
        self.model['overwrite'] = self.chkOverwrite.isChecked()
        self.modelModified.emit()

    def onGenPython(self):
        """
        Respond to change in generate Python checkbox
        """
        self.model['gen_python'] = self.chkGenPython.isChecked()
        self.modelModified.emit()

    def onGenC(self):
        """
        Respond to change in generate C checkbox
        """
        self.model['gen_c'] = self.chkGenC.isChecked()
        self.modelModified.emit()

    def setModelTypeCheckBoxEnabledState(self, filename: str):
        if not os.path.exists(os.path.join(find_plugins_dir(), filename + '.py')):
            # If the user has not yet created a Python file for a specific filename, then force them to create one
            self.chkGenPython.setChecked(True)
            self.chkGenPython.setEnabled(False)
            self.infoLabel.setText("No Python model of the same name detected. Generating Python model is required.")
            self.infoLabel.setVisible(True)
        else:
            self.infoLabel.setVisible(False)
            self.chkGenPython.setEnabled(True)

    def checkPyModelExists(self, filename: str) -> bool:
        """
        Checks if a Python model exists in the user plugin directory and forces enabling Python checkbox if not
        :param filename: name of the file (without extension)
        """
        self.setModelTypeCheckBoxEnabledState(filename)
        return os.path.exists(os.path.join(find_plugins_dir(), filename + '.py'))

    def updateParamTableFromEditor(self, param_list: []):
        """Add parameters sent from model editor to the parameter tables

        :param param_list: list of parameters to add to the parameter tables [name, default_value, type]
        """
        updated_params_non_pd = [param for param in param_list if param[2] != 'volume']
        updated_params_pd = [param for param in param_list if param[2] == 'volume']

        # Prepare the table for updating
        self._updateParamTable(updated_params_non_pd, self.tblParams)
        self._updateParamTable(updated_params_pd, self.tblParamsPD)

    def _updateParamTable(self, param_list: [], param_table: QtWidgets.QTableWidget):
        """Add subset of parameters sent from model editor to a specific parameter table

        :param param_list: list of parameters to add to the parameter tables [name, default_value, type]
        :param param_table: A QTableWidget that will be updated with the params from param_list
        """
        param_table.blockSignals(True)
        param_table.clearContents()
        param_table.setRowCount(len(param_list) + 1)

        # Iterate over cells and add the new parameters to them
        for row, param in enumerate(param_list):
            for column in range(2):
                if column < len(param):  # Check if the column index is within the bounds of param length
                    item = QtWidgets.QTableWidgetItem(str(param[column]))
                    param_table.setItem(row, column, item)
                else:
                    logging.info(f"Missing data for Row {row}, Column {column}")

        param_table.blockSignals(False)

    def getModel(self) -> dict:
        """
        Return the current plugin model
        """
        return self.model
