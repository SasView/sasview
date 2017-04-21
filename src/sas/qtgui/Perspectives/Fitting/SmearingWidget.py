"""
Widget/logic for smearing data.
"""
from PyQt4 import QtGui
from PyQt4 import QtCore

from sas.sasgui.guiframe.dataFitting import Data1D
from sas.sasgui.guiframe.dataFitting import Data2D

# Local UI
from UI.SmearingWidgetUI import Ui_SmearingWidgetUI

class DataWidgetMapper(QtGui.QDataWidgetMapper):
    def addMapping(self, widget, section, propertyName=None):
        if propertyName is None:
            super(DataWidgetMapper, self).addMapping(widget, section)
        else:
            super(DataWidgetMapper, self).addMapping(widget, section, propertyName)

        if isinstance(widget, QtGui.QComboBox):
            delegate = self.itemDelegate()
            widget.currentIndexChanged.connect(lambda: delegate.commitData.emit(widget))

SMEARING_1D = ["Custom Pinhole Smear", "Custom Slit Smear"]
SMEARING_2D = ["Custom Pinhole Smear"]

MODEL = [
    'SMEARING',
    'PINHOLE_MIN',
    'PINHOLE_MAX',
    'ACCURACY']

class SmearingWidget(QtGui.QWidget, Ui_SmearingWidgetUI):
    def __init__(self, parent=None):
        super(SmearingWidget, self).__init__()

        self.setupUi(self)
        self.cbSmearing.currentIndexChanged.connect(self.onIndexChange)
        self.cbSmearing.setCurrentIndex(0)
        self.is_data = None
        self.model = None
        self.mapper = None

        self.initModel()
        self.initMapper()

    def initModel(self):
        """
        Initialize the state
        """
        self.model = QtGui.QStandardItemModel()
        for model_item in xrange(len(MODEL)):
            self.model.setItem(model_item, QtGui.QStandardItem())

        self.model.dataChanged.connect(self.onModelChange)

        ##self.modelReset()

    def initMapper(self):
        """
        Initialize model item <-> UI element mapping
        """
        #self.mapper = QtGui.QDataWidgetMapper(self)
        self.mapper = DataWidgetMapper(self)

        self.mapper.setModel(self.model)
        self.mapper.setOrientation(QtCore.Qt.Vertical)

        self.mapper.addMapping(self.txtSmearUp,   MODEL.index('PINHOLE_MIN'))
        self.mapper.addMapping(self.txtSmearDown, MODEL.index('PINHOLE_MAX'))
        self.mapper.addMapping(self.cbSmearing,   MODEL.index('SMEARING'))
        self.mapper.addMapping(self.cbAccuracy,   MODEL.index('ACCURACY'))
        self.mapper.toFirst()

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
            self.is_data = Data1D
        else:
            self.cbSmearing.addItems(SMEARING_2D)
            self.is_data = Data2D
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
        """
        print "MODEL CHANGED: ", top, bottom
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
        if self.is_data == Data2D and self.cbSmearing.currentIndex() == 1:
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
        
