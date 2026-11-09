"""
The smearing tab: the smearing option offered for the data and the model, and its values.
The smearer itself is built per calculation from the document (``services.theory.build_smearer``).
"""
import logging

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Perspectives.Fitting.services.theory import resolution_of

# Local UI
from sas.qtgui.Perspectives.Fitting.UI.SmearingWidgetUI import Ui_SmearingWidgetUI
from sas.qtgui.Plotting.PlotterData import Data1D, Data2D

logger = logging.getLogger(__name__)


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

SMEARING_1D = ["Custom Pinhole Smear", "Custom Slit Smear"]
SMEARING_2D = ["Custom Pinhole Smear"]
SMEARING_SESANS = "Hankel Transform"
SMEARING_QD = "Use dQ Data"
MODEL = [
    'SMEARING',
    'PINHOLE_MIN',
    'PINHOLE_MAX',
    'ACCURACY']
ACCURACY_DICT={'Low': 'low',
               'Medium': 'med',
               'High': 'high',
               'Extra high': 'xhigh'}

DEFAULT_PINHOLE_UP=0.0
DEFAULT_PINHOLE_DOWN=0.0

class SmearingWidget(QtWidgets.QWidget, Ui_SmearingWidgetUI):
    smearingChangedSignal = QtCore.Signal()

    def __init__(self, parent=None):
        super(SmearingWidget, self).__init__()

        self.setupUi(self)

        # Set parent to read parameters from fitting widget
        self.parent = parent
        # Local model for holding data
        self.model = None
        # Mapper for model update
        self.mapper = None
        # Data from the widget
        self.data = None
        # A model is selected: the custom smearing options are offered
        self.has_model = False
        # dQ data variables
        self.smear_type = None
        self.dq_l = None
        self.dq_r = None

        # current pinhole/slot values
        self.pinhole = 0.0
        self.slit_height = 0.0
        self.slit_width = 0.0

        # current accuracy option
        self.accuracy = ""

        # Let only floats in the line edits
        self.txtSmearDown.setValidator(GuiUtils.DoubleValidator())
        self.txtSmearUp.setValidator(GuiUtils.DoubleValidator())

        # Attach slots
        self.cbSmearing.currentIndexChanged.connect(self.onIndexChange)
        self.cbSmearing.setCurrentIndex(0)
        self.txtSmearUp.setText(str(DEFAULT_PINHOLE_UP))
        self.txtSmearDown.setText(str(DEFAULT_PINHOLE_DOWN))

        self.initModel()
        self.initMapper()

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

        self.mapper.addMapping(self.txtSmearUp,   MODEL.index('PINHOLE_MIN'))
        self.mapper.addMapping(self.txtSmearDown, MODEL.index('PINHOLE_MAX'))
        self.mapper.addMapping(self.cbAccuracy,   MODEL.index('ACCURACY'))

        self.mapper.toFirst()

    def updateData(self, data=None):
        """
        Update control elements based on data and model passed
        """
        # retain the combobox index
        old_index = self.cbSmearing.currentIndex()
        self.gAccuracy.setVisible(False)
        self.data = data
        if data is None:
            self.setElementsVisibility(False)
        self.updateModel(self.has_model, keep_order=True, old_index=old_index)

    def updateModel(self, has_model=False, keep_order=False, old_index=None):
        """
        The options for the data and whether a model is selected
        """
        self.has_model = has_model
        # keep the original cbSmearing value, if already set
        index_to_show = self.cbSmearing.currentIndex()
        if old_index is not None:
            index_to_show = old_index

        self.cbSmearing.blockSignals(True)
        self.cbSmearing.clear()
        self.cbSmearing.addItem("None")
        if self.data is None:
            self.setElementsVisibility(False)
        # Find out if data has dQ or is SESANS
        self.setSmearInfo()
        if self.smear_type == "Hankel Transform":
            self.cbSmearing.addItem(SMEARING_SESANS)
            index_to_show = 1
        elif self.smear_type is not None:
            self.cbSmearing.addItem(SMEARING_QD)
            index_to_show = 1 if keep_order else index_to_show

        if self.has_model:
            # Only give custom smearing options after the model is defined, but always offer them
            #  regardless of the data state
            if isinstance(self.data, Data1D) or not self.parent.is2D:
                # 1D data smearing options
                self.cbSmearing.addItems(SMEARING_1D)
            else:
                # 2D smearing options
                self.cbSmearing.addItems(SMEARING_2D)

        self.cbSmearing.blockSignals(False)
        self.cbSmearing.setCurrentIndex(index_to_show if index_to_show >= 0 else 0)

    def onIndexChange(self, index):
        """
        Callback for smearing combobox index change
        """
        text = self.cbSmearing.currentText()
        # Ensure smearing selector is enabled initially in case swapped data from SESANS
        self.cbSmearing.setEnabled(True)
        if text == 'None':
            self.setElementsVisibility(False)
        elif text == "Use dQ Data":
            self.setElementsVisibility(True)
            self.setDQLabels()
        elif text == "Custom Pinhole Smear":
            self.setElementsVisibility(True)
            self.setPinholeLabels()
        elif text == "Custom Slit Smear":
            self.setElementsVisibility(True)
            self.setSlitLabels()
            if self.data:
                self.onSlitSmear()
        elif text == "Hankel Transform":
            self.setElementsVisibility(False)
            self.cbSmearing.setEnabled(False)  # turn off ability to change smearing; no other options for sesans
        self.smearingChangedSignal.emit()

    def onModelChange(self):
        """
        Respond to model change by notifying any listeners
        """
        # Recalculate the smearing
        index = self.cbSmearing.currentIndex()
        # update the backup values based on model choice
        smearing, accuracy, d_down, d_up = self.state()
        # don't save the state if dQ Data
        if smearing == "Custom Pinhole Smear":
            self.pinhole = d_up
        elif smearing == 'Custom Slit Smear':
            self.slit_height = d_up
            self.slit_width = d_down
        # check changes in accuracy
        if self.accuracy != accuracy:
            self.accuracy = accuracy
            if accuracy == 'High' or accuracy == 'Extra high':
                QtWidgets.QMessageBox.information(self, "Accuracy Warning",
                  "Higher accuracy is very expensive, \nso fitting can be very slow!")

        self.onIndexChange(index)

    def setElementsVisibility(self, visible):
        """
        Labels and linedits visibility control
        """
        self.lblSmearDown.setVisible(visible)
        self.lblSmearUp.setVisible(visible)
        self.txtSmearDown.setVisible(visible)
        self.txtSmearUp.setVisible(visible)
        self.lblUnitUp.setVisible(visible)
        self.lblUnitDown.setVisible(visible)
        self.setAccuracyVisibility()

    def setAccuracyVisibility(self):
        """
        Accuracy combobox visibility
        """
        if isinstance(self.data, Data2D) and self.cbSmearing.currentIndex() >= 1:
            self.gAccuracy.setVisible(True)
        else:
            self.gAccuracy.setVisible(False)

    def setPinholeLabels(self):
        """
        Use pinhole labels
        """
        self.txtSmearDown.setVisible(False)
        self.lblSmearDown.setText('')
        self.lblUnitDown.setText('')
        self.lblSmearUp.setText('<html><head/><body><p>dQ/Q</p></body></html>')
        self.lblUnitUp.setText('%')
        self.txtSmearUp.setText(str(self.pinhole))

        self.txtSmearDown.setEnabled(True)
        self.txtSmearUp.setEnabled(True)

    def setSlitLabels(self):
        """
        Use pinhole labels
        """
        self.lblSmearUp.setText('Slit length')
        self.lblSmearDown.setText('Slit width')
        self.lblUnitUp.setText('<html><head/><body><p>Å<span style=" vertical-align:super;">-1</span></p></body></html>')
        self.lblUnitDown.setText('<html><head/><body><p>Å<span style=" vertical-align:super;">-1</span></p></body></html>')
        self.txtSmearUp.setText(str(self.slit_height))
        self.txtSmearDown.setText(str(self.slit_width))
        self.txtSmearDown.setEnabled(True)
        self.txtSmearUp.setEnabled(True)

    def setDQLabels(self):
        """
        Use appropriate labels
        """
        if self.smear_type == "Pinhole":
            text_down = '<html><head/><body><p>[dQ/Q]<span style=" vertical-align:sub;">max</span></p></body></html>'
            text_up = '<html><head/><body><p>[dQ/Q]<span style=" vertical-align:sub;">min</span></p></body></html>'
            text_unit = '%'
        elif self.smear_type == "Slit":
            text_down = '<html><head/><body><p>Slit width</p></body></html>'
            text_up = '<html><head/><body><p>Slit length</p></body></html>'
            text_unit = '<html><head/><body><p>Å<span style=" vertical-align:super;">-1</span></p></body></html>'
        else:
            text_unit = '%'
            text_up = '<html><head/><body><p>&lsaquo;dQ/Q&rsaquo;<span style=" vertical-align:sub;">r</span></p></body></html>'
            text_down = '<html><head/><body><p>&lsaquo;dQ/Q&rsaquo;<span style=" vertical-align:sub;">&phi;</span></p></body></html>'

        self.lblSmearDown.setText(text_down)
        self.lblSmearUp.setText(text_up)

        self.lblUnitUp.setText(text_unit)
        self.lblUnitDown.setText(text_unit)

        self.txtSmearDown.setText(str(self.dq_r))
        self.txtSmearUp.setText(str(self.dq_l))
        self.txtSmearDown.setEnabled(False)
        self.txtSmearUp.setEnabled(False)

    def state(self):
        """
        Returns current state of controls
        """
        smearing = self.cbSmearing.currentText()
        accuracy = ""
        d_down = None
        d_up = None
        if smearing != "None":
            accuracy = str(self.model.item(MODEL.index('ACCURACY')).text())
            try:
                d_down = float(self.txtSmearDown.text())
            except ValueError:
                d_down = 0.0
            try:
                d_up = float(self.txtSmearUp.text())
            except ValueError:
                d_up = 0.0

        return (smearing, accuracy, d_down, d_up)

    def setState(self, accuracy, d_down, d_up):
        """
        Sets new values for the controls, as state() reads them (SettingsSync)
        """
        # Update the model -> controls update automatically. txtSmearDown shows PINHOLE_MAX.
        if accuracy is not None:
            self.model.item(MODEL.index('ACCURACY')).setText(accuracy)
        if d_down is not None:
            self.model.item(MODEL.index('PINHOLE_MAX')).setText(str(d_down))
        if d_up is not None:
            self.model.item(MODEL.index('PINHOLE_MIN')).setText(str(d_up))

    def onSlitSmear(self):
        """
        Warn about slit values that are not slit smearing (build_smearer swaps them if needed)
        """
        _, accuracy, d_width, d_length = self.state()

        # Check changes in slit width
        if d_width is None:
            d_width = 0.0
        if d_length is None:
            d_length = 0.0
        q_max = max(self.data.x)
        smearing_error_flag = False
        if d_length < d_width:
            msg = 'Length specified which is less than width. \n' \
                  'This is not slit-smearing, probably you switched the two parameters? \n' \
                  'I am internally using the smaller parameter as the width and larger as the length. \n' \
                  'This is the only mathematically valid version of this.'
            smearing_error_flag = True
            d_length, d_width = d_width, d_length
        elif d_length < 10 * d_width:
            msg = 'Slit length specified which is less than 10 x slit width. ' \
                  'This is not slit-smearing (at least not in the form we implement). \n' \
                  'Use pinhole smearing instead.'
            smearing_error_flag = True
        # elif d_length < q_max:
        #     msg = f'Length specified which is less than q_max for the data. \n' \
        #           f'This is not covered by existing smearing model. \n' \
        #           f'Use pinhole smearing instead. '
        #     smearing_error_flag = True
        # override all these errors if both values are zero (initial starting state)
        if d_length == 0 and d_width == 0:
            smearing_error_flag = False


        if smearing_error_flag:
            logger.critical(msg)
            errorbox = QtWidgets.QMessageBox()
            errorbox.setWindowTitle('Smearing Input Error')
            errorbox.setText(msg)
            errorbox.exec_()

        self.slit_width = d_width
        self.slit_length = d_length

    def setSmearInfo(self):
        """
        Set default smear_type, dq_l, and dq_r based on the q-resolution information found in the data.
        """
        # default
        self.smear_type = None
        self.dq_l = None
        self.dq_r = None
        data = self.data
        # The Hankel transform of SESANS data is treated like other resolution functions
        self.smear_type = resolution_of(data)
        if self.smear_type == "Pinhole2d":
            self.dq_l = GuiUtils.formatNumber(np.average(data.dqx_data/np.abs(data.qx_data))*100., high=True)
            self.dq_r = GuiUtils.formatNumber(np.average(data.dqy_data/np.abs(data.qy_data))*100., high=True)
        elif self.smear_type == "Pinhole":
            self.dq_r = GuiUtils.formatNumber(data.dx[0]/data.x[0] *100., high=True)
            self.dq_l = GuiUtils.formatNumber(data.dx[-1]/data.x[-1] *100., high=True)
        elif self.smear_type == "Slit":
            if data.dxl is not None and np.all(data.dxl, 0):
                self.dq_l = GuiUtils.formatNumber(data.dxl[0])
            if data.dxw is not None and np.all(data.dxw, 0):
                self.dq_r = GuiUtils.formatNumber(data.dxw[0])

    def resetSmearer(self):
        self.cbSmearing.blockSignals(True)
        self.cbSmearing.clear()
        self.cbSmearing.blockSignals(False)
