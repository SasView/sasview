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
    QMIN_DEFAULT = 0.0005
    QMAX_DEFAULT = 0.5
    NPTS_DEFAULT = 50
    MODEL = [
        'MIN_RANGE',
        'MAX_RANGE',
        'NPTS',
        'LOG_SPACED']

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

        self.qmin = self.QMIN_DEFAULT
        self.qmax = self.QMAX_DEFAULT
        self.npts = self.NPTS_DEFAULT
        if self.logic.data_is_loaded:
            self.qmin, self.qmax, self.npts = self.logic.computeDataRange()
        self.initModel()
        self.initMapper()
        self.model.blockSignals(True)
        self.updateQRange(self.qmin, self.qmax, self.npts)
        self.txtMaxRange.setText(GuiUtils.formatNumber(self.qmax, high=True))
        self.txtMinRange.setText(GuiUtils.formatNumber(self.qmin, high=True))
        self.txtNpts.setText(str(self.npts))
        self.txtNptsFit.setText(str(self.npts))
        self.model.blockSignals(False)

        new_font = 'font-family: -apple-system, "Helvetica Neue", "Ubuntu";'
        self.label_13.setStyleSheet(new_font)
        self.label_15.setStyleSheet(new_font)

    def initModel(self):
        """
        Initialize the state
        """
        self.model = QtGui.QStandardItemModel()
        for model_item in range(len(self.MODEL)):
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

        self.mapper.addMapping(self.txtMinRange, self.MODEL.index('MIN_RANGE'))
        self.mapper.addMapping(self.txtMaxRange, self.MODEL.index('MAX_RANGE'))
        self.mapper.addMapping(self.txtNpts,     self.MODEL.index('NPTS'))
        self.mapper.addMapping(self.chkLogData,  self.MODEL.index('LOG_SPACED'))

        self.mapper.toFirst()

    def toggleLogData(self, isChecked):
        """ Toggles between log and linear data sets """
        pass

    def onMaskEdit(self):
        """
        Callback for running the mask editor
        """
        if isinstance(self.logic.data, Data2D):
            self.parent.communicate.maskEditorSignal.emit(self.logic.data)

    def onRangeReset(self):
        """
        Callback for resetting qmin/qmax
        """
        self.updateQRange(self.qmin, self.qmax, self.npts)

    def onWeightingChoice(self, button):
        """
        Update weighting in the fit state
        """
        button_id = button.group().checkedId()
        self.weighting = abs(button_id + 2)
        self.plot_signal.emit()

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
        is2Ddata = isinstance(self.logic.data, Data2D)
        self.boxWeighting.setEnabled(True)
        self.cmdMaskEdit.setEnabled(is2Ddata)
        # Switch off txtNpts related controls
        self.txtNpts.setEnabled(False)
        self.txtNptsFit.setEnabled(False)
        self.chkLogData.setEnabled(False)
        # Weighting controls
        if self.logic.di_flag:
            self.rbWeighting2.setEnabled(True)
            self.rbWeighting2.setChecked(True)
            self.onWeightingChoice(self.rbWeighting2)
        else:
            self.rbWeighting2.setEnabled(False)
            self.rbWeighting1.setChecked(True)
            self.onWeightingChoice(self.rbWeighting1)

    def updateQRange(self, q_range_min, q_range_max, npts):
        """
        Update the local model based on calculated values
        """
        qmax = GuiUtils.formatNumber(self.qmax, high=True)
        qmin = GuiUtils.formatNumber(self.qmin, high=True)
        self.model.item(self.MODEL.index('MIN_RANGE')).setText(qmin)
        self.model.item(self.MODEL.index('MAX_RANGE')).setText(qmax)
        self.model.item(self.MODEL.index('NPTS')).setText(str(npts))
        self.qmin, self.qmax, self.npts = q_range_min, q_range_max, npts

    def state(self):
        """
        Returns current state of controls
        """
        q_range_min = float(self.model.item(self.MODEL.index('MIN_RANGE')).text())
        q_range_max = float(self.model.item(self.MODEL.index('MAX_RANGE')).text())
        npts = int(self.model.item(self.MODEL.index('NPTS')).text())
        log_points = str(self.model.item(self.MODEL.index('LOG_SPACED')).text()) == 'true'

        return (q_range_min, q_range_max, npts, log_points, self.weighting)
