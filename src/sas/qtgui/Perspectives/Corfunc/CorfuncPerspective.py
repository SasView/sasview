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

from matplotlib.backends import qt_compat
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class MyMplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)

        FigureCanvas.__init__(self, self.fig)
        # self.reparent(parent, QPoint(0, 0))

        # FigureCanvas.setSizePolicy(self,
        #                            QSizePolicy.Expanding,
        #                            QSizePolicy.Expanding)
        # FigureCanvas.updateGeometry(self)

        self.data = None
        self.qmin = None
        self.qmax1 = None
        self.qmax2 = None
        self.extrap = None

    def drawQSpace(self):
        self.fig.clf()

        self.axes = self.fig.add_subplot(111)
        self.axes.set_xscale("log")
        self.axes.set_yscale("log")

        if self.data:
            self.axes.plot(self.data.x, self.data.y)
        if self.qmin:
            self.axes.axvline(self.qmin)
        if self.qmax1:
            self.axes.axvline(self.qmax1)
        if self.qmax2:
            self.axes.axvline(self.qmax2)
        if self.extrap:
            self.axes.plot(self.extrap.x, self.extrap.y)

        self.draw()

    def drawRealSpace(self):
        self.fig.clf()

        self.axes = self.fig.add_subplot(111)
        self.axes.set_xscale("linear")
        self.axes.set_yscale("linear")

        if self.data:
            self.axes.plot(self.data.x, self.data.y)

        self.draw()


    # def sizeHint(self):
    #     w, h = self.get_width_height()
    #     return QSize(w, h)

    # def minimumSizeHint(self):
    #     return QSize(10, 10)


class CorfuncWindow(QtGui.QDialog, Ui_CorfuncDialog):
    # The controller which is responsible for managing signal slots connections
    # for the gui and providing an interface to the data model.
    name = "Corfunc" # For displaying in the combo box
    #def __init__(self, manager=None, parent=None):
    def __init__(self, parent=None):
        super(CorfuncWindow, self).__init__()
        self.setupUi(self)

        self.setWindowTitle("Corfunc Perspective")

        self.model = QtGui.QStandardItemModel(self)
        self.communicate = GuiUtils.Communicate()
        self._calculator = CorfuncCalculator()

        self._canvas = MyMplCanvas(self)
        self._realplot = MyMplCanvas(self)
        self.verticalLayout_7.insertWidget(0, self._canvas)
        self.verticalLayout_7.insertWidget(1, self._realplot)

        # Connect buttons to slots.
        # Needs to be done early so default values propagate properly.
        self.setupSlots()

        # Set up the model.
        self.setupModel()

        # Set up the mapper
        self.setupMapper()

    def setupSlots(self):
        self.extrapolateBtn.clicked.connect(self.extrapolate)
        self.transformBtn.clicked.connect(self.transform)

        self.calculateBgBtn.clicked.connect(self.calculateBackground)

        self.model.itemChanged.connect(self.modelChanged)

    def setupModel(self):
        self.model.setItem(W.W_QMIN,
                           QtGui.QStandardItem("0.01"))
        self.model.setItem(W.W_QMAX,
                           QtGui.QStandardItem("0.20"))
        self.model.setItem(W.W_QCUTOFF,
                           QtGui.QStandardItem("0.22"))
        self.model.setItem(W.W_BACKGROUND,
                           QtGui.QStandardItem("0"))
        self.model.setItem(W.W_TRANSFORM,
                           QtGui.QStandardItem("Fourier"))
        self.model.setItem(W.W_GUINIERA,
                           QtGui.QStandardItem("0.0"))
        self.model.setItem(W.W_GUINIERB,
                           QtGui.QStandardItem("0.0"))
        self.model.setItem(W.W_PORODK,
                           QtGui.QStandardItem("0.0"))
        self.model.setItem(W.W_PORODSIGMA,
                           QtGui.QStandardItem("0.0"))
        self.model.setItem(W.W_CORETHICK, QtGui.QStandardItem(str(0)))
        self.model.setItem(W.W_INTTHICK, QtGui.QStandardItem(str(0)))
        self.model.setItem(W.W_HARDBLOCK, QtGui.QStandardItem(str(0)))
        self.model.setItem(W.W_CRYSTAL, QtGui.QStandardItem(str(0)))
        self.model.setItem(W.W_POLY, QtGui.QStandardItem(str(0)))
        self.model.setItem(W.W_PERIOD, QtGui.QStandardItem(str(0)))

    def modelChanged(self, item):
        if item.row() == W.W_QMIN:
            value = float(self.model.item(W.W_QMIN).text())
            self._canvas.qmin = value
        elif item.row() == W.W_QMAX or item.row() == W.W_QCUTOFF:
            a = float(self.model.item(W.W_QMAX).text())
            b = float(self.model.item(W.W_QCUTOFF).text())
            self._canvas.qmax1 = a
            self._canvas.qmax2 = b
        else:
            print("{} Changed".format(item))

        self._update_calculator()
        self.mapper.toFirst()
        self._canvas.drawQSpace()

    def _update_calculator(self):
        self._calculator.lowerq = float(self.model.item(W.W_QMIN).text())
        qmax1 = float(self.model.item(W.W_QMAX).text())
        qmax2 = float(self.model.item(W.W_QCUTOFF).text())
        self._calculator.upperq = (qmax1, qmax2)
        self._calculator.background = float(self.model.item(W.W_BACKGROUND).text())

    def extrapolate(self):
        params, extrapolation = self._calculator.compute_extrapolation()

        self.model.setItem(W.W_GUINIERA, QtGui.QStandardItem(str(params['A'])))
        self.model.setItem(W.W_GUINIERB, QtGui.QStandardItem(str(params['B'])))
        self.model.setItem(W.W_PORODK, QtGui.QStandardItem(str(params['K'])))
        self.model.setItem(W.W_PORODSIGMA, QtGui.QStandardItem(str(params['sigma'])))

        self._canvas.extrap = extrapolation
        self._canvas.drawQSpace()


    def transform(self):
        if self.fourierBtn.isChecked():
            method = "fourier"
        elif self.hilbertBtn.isChecked():
            method = "hilbert"

        extrap = self._canvas.extrap
        bg = float(self.model.item(W.W_BACKGROUND).text())
        def updatefn(*args, **kwargs):
            pass

        def completefn(transform):
            self._realplot.data = transform
            self._realplot.drawRealSpace()
            params = self._calculator.extract_parameters(transform)
            self.model.setItem(W.W_CORETHICK, QtGui.QStandardItem(str(params['d0'])))
            self.model.setItem(W.W_INTTHICK, QtGui.QStandardItem(str(params['dtr'])))
            self.model.setItem(W.W_HARDBLOCK, QtGui.QStandardItem(str(params['Lc'])))
            self.model.setItem(W.W_CRYSTAL, QtGui.QStandardItem(str(params['fill'])))
            self.model.setItem(W.W_POLY, QtGui.QStandardItem(str(params['A'])))
            self.model.setItem(W.W_PERIOD, QtGui.QStandardItem(str(params['max'])))

        self._calculator.compute_transform(extrap, method, bg, completefn, updatefn)


    def setupMapper(self):
        self.mapper = QtGui.QDataWidgetMapper(self)
        self.mapper.setOrientation(QtCore.Qt.Vertical)
        self.mapper.setModel(self.model)

        self.mapper.addMapping(self.qMin, W.W_QMIN)
        self.mapper.addMapping(self.qMax1, W.W_QMAX)
        self.mapper.addMapping(self.qMax2, W.W_QCUTOFF)
        self.mapper.addMapping(self.bg, W.W_BACKGROUND)

        self.mapper.addMapping(self.guinierA, W.W_GUINIERA)
        self.mapper.addMapping(self.guinierB, W.W_GUINIERB)
        self.mapper.addMapping(self.porodK, W.W_PORODK)
        self.mapper.addMapping(self.porodSigma, W.W_PORODSIGMA)

        self.mapper.addMapping(self.avgCoreThick, W.W_CORETHICK)
        self.mapper.addMapping(self.avgIntThick, W.W_INTTHICK)
        self.mapper.addMapping(self.avgHardBlock, W.W_HARDBLOCK)
        self.mapper.addMapping(self.polydisp, W.W_POLY)
        self.mapper.addMapping(self.longPeriod, W.W_PERIOD)
        self.mapper.addMapping(self.localCrystal, W.W_CRYSTAL)

        self.mapper.toFirst()

    def calculateBackground(self):
        bg = self._calculator.compute_background()
        temp = QtGui.QStandardItem(str(bg))
        self.model.setItem(W.W_BACKGROUND, temp)

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
        self._calculator.set_data(data)

        self._canvas.data = data
        self._canvas.drawQSpace()

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
