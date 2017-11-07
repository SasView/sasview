"""
Widget/logic for smearing data.
"""
import numpy as np
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from sas.qtgui.Plotting.PlotterData import Data2D
import sas.qtgui.Utilities.GuiUtils as GuiUtils

# Local UI
from sas.qtgui.Perspectives.Fitting.UI.OptionsWidgetUI import Ui_tabOptions

QMIN_DEFAULT = 0.0005
QMAX_DEFAULT = 0.5
NPTS_DEFAULT = 50

MODEL = [
    'MIN_RANGE',
    'MAX_RANGE',
    'NPTS',
    'LOG_SPACED']

class DataWidgetMapper(QtWidgets.QDataWidgetMapper):
    """
    Custom version of the standard QDataWidgetMapper allowing for proper
    response to index change in comboboxes
    """
    def addMapping(self, widget, section, propertyName=None):
        if propertyName is None:
            super(DataWidgetMapper, self).addMapping(widget, section)
        else:
            super(DataWidgetMapper, self).addMapping(widget, section, propertyName)

        if isinstance(widget, QtWidgets.QComboBox):
            delegate = self.itemDelegate()
            widget.currentIndexChanged.connect(lambda: delegate.commitData.emit(widget))

        elif isinstance(widget, QtWidgets.QCheckBox):
            delegate = self.itemDelegate()
            widget.stateChanged.connect(lambda: delegate.commitData.emit(widget))

class OptionsWidget(QtWidgets.QWidget, Ui_tabOptions):
    plot_signal = QtCore.pyqtSignal()
    def __init__(self, parent=None, logic=None):
        super(OptionsWidget, self).__init__()

        self.setupUi(self)

        # Logic component
        self.logic = logic
        self.parent = parent

        # Weight radio box group
        self.weightingGroup = QtWidgets.QButtonGroup()
        self.weighting = 0

        # Group boxes
        self.boxWeighting.setEnabled(False)
        self.cmdMaskEdit.setEnabled(False)
        # Button groups
        self.weightingGroup.addButton(self.rbWeighting1)
        self.weightingGroup.addButton(self.rbWeighting2)
        self.weightingGroup.addButton(self.rbWeighting3)
        self.weightingGroup.addButton(self.rbWeighting4)

        # Let only floats in the range edits
        self.txtMinRange.setValidator(GuiUtils.DoubleValidator())
        self.txtMaxRange.setValidator(GuiUtils.DoubleValidator())
        # Let only ints in the number of points edit
        self.txtNpts.setValidator(QtGui.QIntValidator())

        # Attach slots
        self.cmdReset.clicked.connect(self.onRangeReset)
        self.cmdMaskEdit.clicked.connect(self.onMaskEdit)
        self.chkLogData.stateChanged.connect(self.toggleLogData)
        # Button groups
        self.weightingGroup.buttonClicked.connect(self.onWeightingChoice)

        self.initModel()
        self.initMapper()
        self.model.blockSignals(True)
        self.updateQRange(QMIN_DEFAULT, QMAX_DEFAULT, NPTS_DEFAULT)
        self.txtMaxRange.setText(str(QMAX_DEFAULT))
        self.txtMinRange.setText(str(QMIN_DEFAULT))
        self.txtNpts.setText(str(NPTS_DEFAULT))
        self.txtNptsFit.setText(str(NPTS_DEFAULT))
        self.model.blockSignals(False)

        new_font = 'font-family: -apple-system, "Helvetica Neue", "Ubuntu";'
        self.label_13.setStyleSheet(new_font)
        self.label_15.setStyleSheet(new_font)

    def initModel(self):
        """
        Initialize the state
        """
        self.model = QtGui.QStandardItemModel()
        for model_item in range(len(MODEL)):
            self.model.setItem(model_item, QtGui.QStandardItem())
        # Attach slot
        self.model.dataChanged.connect(self.onModelChange)

    def initMapper(self):
        """
        Initialize model item <-> UI element mapping
        """
        self.mapper = DataWidgetMapper(self)

        self.mapper.setModel(self.model)
        self.mapper.setOrientation(QtCore.Qt.Vertical)

        self.mapper.addMapping(self.txtMinRange, MODEL.index('MIN_RANGE'))
        self.mapper.addMapping(self.txtMaxRange, MODEL.index('MAX_RANGE'))
        self.mapper.addMapping(self.txtNpts,     MODEL.index('NPTS'))
        self.mapper.addMapping(self.chkLogData,  MODEL.index('LOG_SPACED'))
        # FIXME DOESNT WORK WITH QT5
        #self.mapper.toFirst()

    def toggleLogData(self, isChecked):
        """ Toggles between log and linear data sets """
        pass

    def onMaskEdit(self):
        """
        Callback for running the mask editor
        """
        pass

    def onRangeReset(self):
        """
        Callback for resetting qmin/qmax
        """
        self.updateQRange(QMIN_DEFAULT, QMAX_DEFAULT, NPTS_DEFAULT)

    def onWeightingChoice(self, button):
        """
        Update weighting in the fit state
        """
        button_id = button.group().checkedId()
        self.weighting = abs(button_id + 2)
        #self.fitPage.weighting = button_id

    def onModelChange(self, top, bottom):
        """
        Respond to model change by updating the plot
        """
        # "bottom" is unused
        # update if there's something to update
        if str(self.model.item(top.row()).text()):
            self.plot_signal.emit()

    def setEnablementOnDataLoad(self):
        """
        Enable/disable various UI elements based on data loaded
        """
        self.boxWeighting.setEnabled(True)
        self.cmdMaskEdit.setEnabled(True)
        # Switch off txtNpts related controls
        self.txtNpts.setEnabled(False)
        self.txtNptsFit.setEnabled(False)
        self.chkLogData.setEnabled(False)
        # Weighting controls
        if isinstance(self.logic.data, Data2D):
            if self.logic.data.err_data is None or\
                    np.all(err == 1 for err in self.logic.data.err_data) or \
                    not np.any(self.logic.data.err_data):
                self.rbWeighting2.setEnabled(False)
                self.rbWeighting1.setChecked(True)
            else:
                self.rbWeighting2.setEnabled(True)
                self.rbWeighting2.setChecked(True)
        else:
            if self.logic.data.dy is None or\
                    np.all(self.logic.data.dy == 1) or\
                    not np.any(self.logic.data.dy):
                self.rbWeighting2.setEnabled(False)
                self.rbWeighting1.setChecked(True)
            else:
                self.rbWeighting2.setEnabled(True)
                self.rbWeighting2.setChecked(True)

    def updateQRange(self, q_range_min, q_range_max, npts):
        """
        Update the local model based on calculated values
        """
        self.model.item(MODEL.index('MIN_RANGE')).setText(str(q_range_min))
        self.model.item(MODEL.index('MAX_RANGE')).setText(str(q_range_max))
        self.model.item(MODEL.index('NPTS')).setText(str(npts))

    def state(self):
        """
        Returns current state of controls
        """
        q_range_min = float(self.model.item(MODEL.index('MIN_RANGE')).text())
        q_range_max = float(self.model.item(MODEL.index('MAX_RANGE')).text())
        npts = int(self.model.item(MODEL.index('NPTS')).text())
        log_points = str(self.model.item(MODEL.index('LOG_SPACED')).text()) == 'true'

        return (q_range_min, q_range_max, npts, log_points, self.weighting)
