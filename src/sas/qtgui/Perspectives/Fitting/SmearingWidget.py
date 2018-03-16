"""
Widget/logic for smearing data.
"""
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

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

MODEL = [
    'SMEARING',
    'PINHOLE_MIN',
    'PINHOLE_MAX',
    'ACCURACY']

class SmearingWidget(QtWidgets.QWidget, Ui_SmearingWidgetUI):
    def __init__(self, parent=None):
        super(SmearingWidget, self).__init__()

        self.setupUi(self)

        # Have we loaded data yet? If so, what kind
        self.have_data = None
        # Local model for holding data
        self.model = None
        # Mapper for model update
        self.mapper = None

        self.parent = parent
        # Let only floats in the line edits
        self.txtSmearDown.setValidator(GuiUtils.DoubleValidator())
        self.txtSmearUp.setValidator(GuiUtils.DoubleValidator())

        # Attach slots
        self.cbSmearing.currentIndexChanged.connect(self.onIndexChange)
        self.cbSmearing.setCurrentIndex(0)

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
        self.mapper.addMapping(self.cbSmearing,   MODEL.index('SMEARING'))
        self.mapper.addMapping(self.cbAccuracy,   MODEL.index('ACCURACY'))

        # FIXME DOESNT WORK WITH QT5
        #self.mapper.toFirst()

    def updateSmearing(self, data=None):
        """
        Update control elements based on data passed
        """
        self.cbSmearing.clear()
        self.cbSmearing.addItem("None")
        self.cbAccuracy.setVisible(False)

        if data is None:
            self.setElementsVisibility(False)
        elif isinstance(data, Data1D):
            self.cbSmearing.addItems(SMEARING_1D)
            self.have_data = Data1D
        else:
            self.cbSmearing.addItems(SMEARING_2D)
            self.have_data = Data2D
        self.cbSmearing.setCurrentIndex(0)

    def onIndexChange(self, index):
        """
        Callback for smearing combobox index change
        """
        if index == 0:
            self.setElementsVisibility(False)
            return
        elif index == 1:
            self.setElementsVisibility(True)
            self.setPinholeLabels()
        elif index == 2:
            self.setElementsVisibility(True)
            self.setSlitLabels()

    def onModelChange(self, top, bottom):
        """
        Respond to model change by updating
        """
        #print "MODEL CHANGED for property: %s. The value is now: %s" % \
        #    (MODEL[top.row()], str(self.model.item(top.row()).text()))
        pass

    def setElementsVisibility(self, visible):
        """
        Labels and linedits visibility control
        """
        self.lblSmearDown.setVisible(visible)
        self.lblSmearUp.setVisible(visible)
        self.txtSmearDown.setVisible(visible)
        self.txtSmearUp.setVisible(visible)
        self.label_14.setVisible(visible)
        self.label_15.setVisible(visible)
        self.setAccuracyVisibility()

    def setAccuracyVisibility(self):
        """
        Accuracy combobox visibility
        """
        if self.have_data == Data2D and self.cbSmearing.currentIndex() == 1:
            self.cbAccuracy.setVisible(True)
        else:
            self.cbAccuracy.setVisible(False)

    def setPinholeLabels(self):
        """
        Use pinhole labels
        """
        self.lblSmearUp.setText('<html><head/><body><p>dQ<span style=" vertical-align:sub;">low</span></p></body></html>')
        self.lblSmearDown.setText('<html><head/><body><p>dQ<span style=" vertical-align:sub;">high</span></p></body></html>')

    def setSlitLabels(self):
        """
        Use pinhole labels
        """
        self.lblSmearUp.setText('Slit height')
        self.lblSmearDown.setText('Slit width')

    def state(self):
        """
        Returns current state of controls
        """
        # or model-held values
        smearing = str(self.model.item(MODEL.index('SMEARING')).text())
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
        if smearing is not None:
            self.model.item(MODEL.index('SMEARING')).setText(smearing)
        if accuracy is not None:
            self.model.item(MODEL.index('ACCURACY')).setText(accuracy)
        if d_down is not None:
            self.model.item(MODEL.index('PINHOLE_MIN')).setText(d_down)
        if d_up is not None:
            self.model.item(MODEL.index('PINHOLE_MAX')).setText(d_up)

