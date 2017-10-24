# global
import sys
from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import QtWebKit

from twisted.internet import threads
from twisted.internet import reactor

# sas-global
from sas.qtgui.Plotting.PlotterData import Data1D
import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.sascalc.corfunc.corfunc_calculator import CorfuncCalculator

# local
from UI.CorfuncPanel import Ui_CorfuncDialog
# from InvariantDetails import DetailsDialog
from CorfuncUtils import WIDGETS as W


class CorfuncWindow(QtGui.QDialog, Ui_CorfuncDialog):
    # The controller which is responsible for managing signal slots connections
    # for the gui and providing an interface to the data model.
    name = "Corfunc" # For displaying in the combo box
    #def __init__(self, manager=None, parent=None):
    def __init__(self, parent=None):
        #super(InvariantWindow, self).__init__(parent)
        super(CorfuncWindow, self).__init__()
        self.setupUi(self)

        self.setWindowTitle("Corfunc Perspective")

        self.model = QtGui.QStandardItemModel(self)
        self.communicate = GuiUtils.Communicate()
        self._calculator = CorfuncCalculator()

        # Connect buttons to slots.
        # Needs to be done early so default values propagate properly.
        self.setupSlots()

        # Set up the model.
        self.setupModel()

        # Set up the mapper
        self.setupMapper()

    def setupSlots(self):
        self.extractBtn.clicked.connect(self.action)
        self.extrapolateBtn.clicked.connect(self.extrapolate)
        self.transformBtn.clicked.connect(self.action)

        self.calculateBgBtn.clicked.connect(self.calculateBackground)

        self.hilbertBtn.clicked.connect(self.action)
        self.fourierBtn.clicked.connect(self.action)

        self.model.itemChanged.connect(self.modelChanged)

    def setupModel(self):
        self.model.setItem(W.W_QMIN,
                           QtGui.QStandardItem("0"))
        self.model.setItem(W.W_QMAX,
                           QtGui.QStandardItem("0"))
        self.model.setItem(W.W_QCUTOFF,
                           QtGui.QStandardItem("0"))
        self.model.setItem(W.W_BACKGROUND,
                           QtGui.QStandardItem("0"))
        self.model.setItem(W.W_TRANSFORM,
                           QtGui.QStandardItem("Fourier"))

    def modelChanged(self, item):
        if item.row() == W.W_QMIN:
            value = float(self.model.item(W.W_QMIN).text())
            self.qMin.setValue(value)
            self._calculator.lowerq = value
        elif item.row() == W.W_QMAX:
            value = float(self.model.item(W.W_QMAX).text())
            self.qMax1.setValue(value)
            self._calculator.upperq = (value, self._calculator.upperq[1])
        elif item.row() == W.W_QCUTOFF:
            value = float(self.model.item(W.W_QCUTOFF).text())
            self.qMax2.setValue(value)
            self._calculator.upperq = (self._calculator.upperq[0], value)
        elif item.row() == W.W_BACKGROUND:
            value = float(self.model.item(W.W_BACKGROUND).text())
            self.bg.setValue(value)
            self._calculator.background = value
        else:
            print("{} Changed".format(item))


    def extrapolate(self):
        params, extrapolation = self._calculator.compute_extrapolation()
        self.guinierA.setValue(params['A'])
        self.guinierB.setValue(params['B'])
        self.porodK.setValue(params['K'])
        self.porodSigma.setValue(params['sigma'])
        print(params)



    def setupMapper(self):
        self.mapper = QtGui.QDataWidgetMapper(self)
        self.mapper.setOrientation(QtCore.Qt.Vertical)
        self.mapper.setModel(self.model)

        self.mapper.addMapping(self.qMin, W.W_QMIN)
        self.mapper.addMapping(self.qMax1, W.W_QMAX)
        self.mapper.addMapping(self.qMax2, W.W_QCUTOFF)
        self.mapper.addMapping(self.bg, W.W_BACKGROUND)

        self.mapper.toFirst()

    def calculateBackground(self):
        bg = self._calculator.compute_background()
        print(bg)
        self.model.setItem(W.W_BACKGROUND, QtGui.QStandardItem(str(bg)))

    def action(self):
        print("Called an action!")
        print(self.model)
        print(self.mapper)

    def allowBatch(self):
        """
        We cannot perform corfunc analysis in batch at this time.
        """
        return False

    def setData(self, data_item, is_batch=False):
        """
        Obtain a QStandardItem object and dissect it to get Data1D/2D
        Pass it over to the calculator
        """
        if not isinstance(data_item, list):
            msg = "Incorrect type passed to the Corfunc Perpsective"
            raise AttributeError(msg)

        if not isinstance(data_item[0], QtGui.QStandardItem):
            msg = "Incorrect type passed to the Corfunc Perspective"
            raise AttributeError(msg)

        self._model_item = data_item[0]
        data = GuiUtils.dataFromItem(self._model_item)
        self._calculator.lowerq = 1e-3
        self._calculator.upperq = (2e-1, 3e-1)
        self._calculator.set_data(data)

        # self.model.item(WIDGETS.W_FILENAME).setData(QtCoreQVariant(self._model_item.text()))

    def setClosable(self, value=True):
        """
        Allow outsiders close this widget
        """
        assert isinstance(value, bool)

        self._allow_close = value


if __name__ == "__main__":
    app = QtGui.QApplication([])
    import qt4reactor
    # qt4reactor.install()
    # DO NOT move the following import to the top!
    # (unless you know what you're doing)
    from twisted.internet import reactor
    dlg = CorfuncWindow(reactor)
    print(dlg)
    dlg.show()
    # print(reactor)
    # reactor.run()
    sys.exit(app.exec_())
