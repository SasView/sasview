from PySide6 import QtCore
from PySide6 import QtGui
from PySide6 import QtWidgets

from sas.qtgui.Utilities.UI.PluginDefinitionUI import Ui_PluginDefinition
from sas.qtgui.Utilities import GuiUtils

# txtName
# txtDescription
# chkOverwrite
# tblParams
# tblParamsPD
# txtFunction

class PluginDefinition(QtWidgets.QDialog, Ui_PluginDefinition):
    """
    Class describing the "simple" plugin editor.
    This is a simple series of widgets allowing for specifying
    model form and parameters.
    """
    modelModified = QtCore.Signal()
    omitPolydisperseFuncsSignal = QtCore.Signal()
    includePolydisperseFuncsSignal = QtCore.Signal()
    def __init__(self, parent=None):
        super(PluginDefinition, self).__init__(parent)
        self.setupUi(self)

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
        text = \
"""intensity = q

return intensity
"""
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

    def initializeModel(self):
        """
        Define the dictionary for internal data representation
        """
        # Define the keys
        self.model = {
            'filename':'',
            'overwrite':False,
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
        self.txtName.editingFinished.connect(self.onPluginNameChanged)
        self.txtDescription.editingFinished.connect(self.onDescriptionChanged)
        self.tblParams.cellChanged.connect(self.onParamsChanged)
        self.tblParamsPD.cellChanged.connect(self.onParamsPDChanged)
        # QTextEdit doesn't have a signal for edit finish, so we respond to text changed.
        # Possibly a slight overkill.
        self.txtFunction.textChanged.connect(self.onFunctionChanged)
        self.txtFormVolumeFunction.textChanged.connect(self.onFormVolumeFunctionChanged)
        self.chkOverwrite.toggled.connect(self.onOverwrite)

    def onPluginNameChanged(self):
        """
        Respond to changes in plugin name
        """
        self.model['filename'] = self.txtName.text()
        self.modelModified.emit()

    def onDescriptionChanged(self):
        """
        Respond to changes in plugin description
        """
        self.model['description'] = self.txtDescription.text()
        self.modelModified.emit()

    def onParamsChanged(self, row, column):
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

        # Check if the update was Value for last row. If so, add a new row
        if column == 1 and row == self.tblParams.rowCount()-1:
            # Add a row
            self.tblParams.insertRow(self.tblParams.rowCount())
        self.modelModified.emit()

    def onParamsPDChanged(self, row, column):
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

        # Check if the update was Value for last row. If so, add a new row
        if column == 1 and row == self.tblParamsPD.rowCount() - 1:
            # Add a row
            self.tblParamsPD.insertRow(self.tblParamsPD.rowCount())
        
        # Check to see if there is any polydisperse parameter text present
        any_text_present = False
        for row in range(self.tblParamsPD.rowCount()):
            for column in range(self.tblParamsPD.columnCount()):
                table_cell_contents = self.tblParamsPD.item(row, column)
                if table_cell_contents and table_cell_contents.text():
                    # There is text in at least one cell
                    any_text_present = True
                    break
            if any_text_present:
                # Display the Form Function box because there are polydisperse parameters
                # First insert the first user-specified parameter into sample form volume function
                if not self.displayed_default_form_volume:
                    text = \
"""volume = {0} * 0.0

return volume
""".format(self.model['pd_parameters'][0][0])
                    self.model['form_volume_text'] = text
                    self.txtFormVolumeFunction.insertPlainText(text)
                    self.displayed_default_form_volume = True

                self.formFunctionBox.setVisible(True)
                self.includePolydisperseFuncsSignal.emit()
                break
            else:
                # Hide the Form Function box because there are no polydisperse parameters
                self.formFunctionBox.setVisible(False)
                self.omitPolydisperseFuncsSignal.emit()
    
        self.modelModified.emit()


    def onFunctionChanged(self):
        """
        Respond to changes in function body
        """
        # keep in mind that this is called every time the text changes.
        # mind the performance!
        #self.addTooltip()
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
        #self.addTooltip()
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

    def getModel(self):
        """
        Return the current plugin model
        """
        return self.model
