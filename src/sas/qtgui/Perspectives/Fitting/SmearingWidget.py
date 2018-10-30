"""
Widget/logic for smearing data.
"""
import copy
import numpy as np
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from sas.sascalc.fit.qsmearing import smear_selection
from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Plotting.PlotterData import Data2D
import sas.qtgui.Utilities.GuiUtils as GuiUtils

# Local UI
from sas.qtgui.Perspectives.Fitting.UI.SmearingWidgetUI import Ui_SmearingWidgetUI

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
    smearingChangedSignal = QtCore.pyqtSignal()
    def __init__(self, parent=None):
        super(SmearingWidget, self).__init__()

        self.setupUi(self)

        # Local model for holding data
        self.model = None
        # Mapper for model update
        self.mapper = None
        # Data from the widget
        self.data = None
        self.current_smearer = None
        self.kernel_model = None
        # dQ data variables
        smear_type = None
        dq_l = None
        dq_r = None
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
        self.cbSmearing.clear()
        self.cbSmearing.addItem("None")
        self.gAccuracy.setVisible(False)
        self.data = data
        if data is None:
            self.setElementsVisibility(False)
        if self.kernel_model is not None:
            # model already present - recalculate
            model = self.kernel_model
            self.updateKernelModel(model)

    def updateKernelModel(self, kernel_model=None):
        """
        Update the model
        """
        self.kernel_model = kernel_model
        self.cbSmearing.blockSignals(True)
        self.cbSmearing.clear()
        self.cbSmearing.addItem("None")
        if self.data is None:
            self.setElementsVisibility(False)
            return
        if self.kernel_model is None:
            return
        # Find out if data has dQ
        (self.smear_type, self.dq_l, self.dq_r) = self.getSmearInfo()
        index_to_show = 0
        if self.smear_type is not None:
            self.cbSmearing.addItem(SMEARING_QD)
            index_to_show = 1
        if isinstance(self.data, Data1D):
            self.cbSmearing.addItems(SMEARING_1D)
        else:
            self.cbSmearing.addItems(SMEARING_2D)
        self.cbSmearing.blockSignals(False)
        self.cbSmearing.setCurrentIndex(index_to_show)

    def smearer(self):
        """ Returns the current smearer """
        return self.current_smearer

    def onIndexChange(self, index):
        """
        Callback for smearing combobox index change
        """
        text = self.cbSmearing.currentText()
        if text == 'None':
            self.setElementsVisibility(False)
            self.current_smearer = None
        elif text == "Use dQ Data":
            self.setElementsVisibility(True)
            self.setDQLabels()
            if self.smear_type == "Pinhole":
                self.onPinholeSmear()
            else:
                self.onSlitSmear()
        elif text == "Custom Pinhole Smear":
            self.setElementsVisibility(True)
            self.setPinholeLabels()
            self.onPinholeSmear()
        elif text == "Custom Slit Smear":
            self.setElementsVisibility(True)
            self.setSlitLabels()
            self.onSlitSmear()
        self.smearingChangedSignal.emit()

    def onModelChange(self):
        """
        Respond to model change by notifying any listeners
        """
        # Recalculate the smearing
        index = self.cbSmearing.currentIndex()
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
        if isinstance(self.data, Data2D) and self.cbSmearing.currentIndex() == 1:
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
        if isinstance(self.data, Data2D):
            self.lblUnitUp.setText('<html><head/><body><p>Å<span style=" vertical-align:super;">-1</span></p></body></html>')
            self.lblSmearUp.setText('<html><head/><body><p>&lt;dQ<span style=" vertical-align:sub;">low</span>&gt;</p></body></html>')
        else:
            self.lblSmearUp.setText('<html><head/><body><p>dQ<span style=" vertical-align:sub;">%</span></p></body></html>')
            self.lblUnitUp.setText('%')
        self.txtSmearDown.setEnabled(True)
        self.txtSmearUp.setEnabled(True)
        #self.txtSmearDown.setText(str(0.0))
        #self.txtSmearUp.setText(str(0.0))

    def setSlitLabels(self):
        """
        Use pinhole labels
        """
        self.lblSmearUp.setText('Slit height')
        self.lblSmearDown.setText('Slit width')
        self.lblUnitUp.setText('<html><head/><body><p>Å<span style=" vertical-align:super;">-1</span></p></body></html>')
        self.lblUnitDown.setText('<html><head/><body><p>Å<span style=" vertical-align:super;">-1</span></p></body></html>')
        self.txtSmearDown.setEnabled(True)
        self.txtSmearUp.setEnabled(True)
        #self.txtSmearDown.setText(str(0.0))
        #self.txtSmearUp.setText(str(0.0))

    def setDQLabels(self):
        """
        Use pinhole labels
        """
        if self.smear_type == "Pinhole":
            self.lblSmearDown.setText('<html><head/><body><p>dQ<span style=" vertical-align:sub;">high</span></p></body></html>')
            self.lblSmearUp.setText('<html><head/><body><p>dQ<span style=" vertical-align:sub;">low</span></p></body></html>')
        else:
            self.lblSmearUp.setText('<dQp>')
            self.lblSmearDown.setText('<dQs>')
        self.lblUnitUp.setText('<html><head/><body><p>Å<span style=" vertical-align:super;">-1</span></p></body></html>')
        self.lblUnitDown.setText('<html><head/><body><p>Å<span style=" vertical-align:super;">-1</span></p></body></html>')
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
                d_down = float(self.model.item(MODEL.index('PINHOLE_MIN')).text())
            except ValueError:
                d_down = None
            try:
                d_up = float(self.model.item(MODEL.index('PINHOLE_MAX')).text())
            except ValueError:
                d_up = None

        return (smearing, accuracy, d_down, d_up)

    def setState(self, smearing, accuracy, d_down, d_up):
        """
        Sets new values for the controls
        """
        # Update the model -> controls update automatically
        #if smearing is not None:
            #self.model.item(MODEL.index('SMEARING')).setText(smearing)
        if accuracy is not None:
            self.model.item(MODEL.index('ACCURACY')).setText(accuracy)
        if d_down is not None:
            self.model.item(MODEL.index('PINHOLE_MIN')).setText(d_down)
        if d_up is not None:
            self.model.item(MODEL.index('PINHOLE_MAX')).setText(d_up)

    def onPinholeSmear(self):
        """
        Create a custom pinhole smear object that will change the way residuals
        are compute when fitting
        """
        _, accuracy, d_percent, _ = self.state()
        if d_percent is None or d_percent == 0.0:
            self.current_smearer=None
            return
        percent = d_percent/100.0
        # copy data
        data = copy.deepcopy(self.data)
        if isinstance(self.data, Data2D):
            len_data = len(data.data)
            data.dqx_data = np.zeros(len_data)
            data.dqy_data = np.zeros(len_data)
            data.dqx_data[data.dqx_data == 0] = percent * data.qx_data
            data.dqy_data[data.dqy_data == 0] = percent * data.qy_data
        else:
            len_data = len(data.x)
            data.dx = np.zeros(len_data)
            data.dx = percent * data.x
            data.dxl = None
            data.dxw = None

        self.current_smearer = smear_selection(data, self.kernel_model)
        # need to set accuracy for 2D
        if isinstance(self.data, Data2D):
            backend_accuracy = ACCURACY_DICT.get(accuracy)
            if backend_accuracy:
                self.current_smearer.set_accuracy(accuracy=backend_accuracy)

    def onSlitSmear(self):
        """
        Create a custom slit smear object that will change the way residuals
        are compute when fitting
        """
        _, accuracy, d_height, d_width = self.state()

        # Check changes in slit width
        if d_width is None:
            d_width = 0.0
        if d_height is None:
            d_height = 0.0

        if isinstance(self.data, Data2D):
            self.current_smearer = smear_selection(self.data, self.kernel_model)
            return
        # make sure once more if it is smearer
        data = copy.deepcopy(self.data)
        data_len = len(data.x)
        data.dx = None
        data.dxl = None
        data.dxw = None

        try:
            self.dxl = d_height
            data.dxl = self.dxl * np.ones(data_len)
        except:
            self.dxl = None
            data.dxl = np.zeros(data_len)
        try:
            self.dxw = d_width
            data.dxw = self.dxw * np.ones(data_len)
        except:
            self.dxw = None
            data.dxw = np.zeros(data_len)

        self.current_smearer = smear_selection(data, self.kernel_model)

    def getSmearInfo(self):
        """
        Get the smear info from data.

        :return: self.smear_type, self.dq_l and self.dq_r,
            respectively the type of the smear, dq_min and
            dq_max for pinhole smear data
            while dxl and dxw for slit smear
        """
        # default
        smear_type = None
        dq_l = None
        dq_r = None
        data = self.data
        if self.data is None:
            return smear_type, dq_l, dq_r
        elif isinstance(data, Data2D):
            if data.dqx_data is None or data.dqy_data is None:
                return smear_type, dq_l, dq_r
            elif data.dqx_data.any() != 0 and data.dqx_data.any() != 0:
                smear_type = "Pinhole2d"
                dq_l = GuiUtils.formatNumber(np.average(data.dqx_data))
                dq_r = GuiUtils.formatNumber(np.average(data.dqy_data))
                return smear_type, dq_l, dq_r
            else:
                return smear_type, dq_l, dq_r
        # check if it is pinhole smear and get min max if it is.
        if data.dx is not None and np.any(data.dx):
            smear_type = "Pinhole"
            dq_l = data.dx[0]
            dq_r = data.dx[-1]

        # check if it is slit smear and get min max if it is.
        elif data.dxl is not None or data.dxw is not None:
            smear_type = "Slit"
            if data.dxl is not None and np.all(data.dxl, 0):
                dq_l = data.dxl[0]
            if data.dxw is not None and np.all(data.dxw, 0):
                dq_r = data.dxw[0]

        return smear_type, dq_l, dq_r
