"""
This module provides the intelligence behind the gui interface for Corfunc.
"""
# pylint: disable=E1101

# global
from PyQt4 import QtCore
from PyQt4 import QtGui

# sas-global
# pylint: disable=import-error, no-name-in-module
import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.sascalc.corfunc.corfunc_calculator import CorfuncCalculator
# pylint: enable=import-error, no-name-in-module

# local
from UI.CorfuncPanel import Ui_CorfuncDialog
# from InvariantDetails import DetailsDialog
from CorfuncUtils import WIDGETS as W

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg \
    as FigureCanvas
from matplotlib.figure import Figure


class MyMplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""
    def __init__(self, model, width=5, height=4, dpi=100):
        self.model = model
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)

        FigureCanvas.__init__(self, self.fig)

        self.data = None
        self.extrap = None

    def draw_q_space(self):
        """Draw the Q space data in the plot window

        This draws the q space data in self.data, as well
        as the bounds set by self.qmin, self.qmax1, and self.qmax2.
        It will also plot the extrpolation in self.extrap, if it exists."""

        self.fig.clf()

        self.axes = self.fig.add_subplot(111)
        self.axes.set_xscale("log")
        self.axes.set_yscale("log")

        qmin = float(self.model.item(W.W_QMIN).text())
        qmax1 = float(self.model.item(W.W_QMAX).text())
        qmax2 = float(self.model.item(W.W_QCUTOFF).text())

        if self.data:
            self.axes.plot(self.data.x, self.data.y)
            self.axes.axvline(qmin)
            self.axes.axvline(qmax1)
            self.axes.axvline(qmax2)
            self.axes.set_xlim(min(self.data.x) / 2,
                               max(self.data.x) * 1.5 - 0.5 * min(self.data.x))
        if self.extrap:
            self.axes.plot(self.extrap.x, self.extrap.y)

        self.draw()

    def draw_real_space(self):
        """
        This function draws the real space data onto the plot

        The 1d correlation function in self.data, the 3d correlation function
        in self.data3, and the interface distribution function in self.data_idf
        are all draw in on the plot in linear cooredinates."""
        self.fig.clf()

        self.axes = self.fig.add_subplot(111)
        self.axes.set_xscale("linear")
        self.axes.set_yscale("linear")

        if self.data:
            data1, data3, data_idf = self.data
            self.axes.plot(data1.x, data1.y, label="1D Correlation")
            self.axes.plot(data3.x, data3.y, label="3D Correlation")
            self.axes.plot(data_idf.x, data_idf.y,
                           label="Interface Distribution Function")
            self.axes.set_xlim(min(data1.x), max(data1.x) / 4)
            self.axes.legend()

        self.draw()


class CorfuncWindow(QtGui.QDialog, Ui_CorfuncDialog):
    """Displays the correlation function analysis of sas data."""
    name = "Corfunc"  # For displaying in the combo box

# pylint: disable=unused-argument
    def __init__(self, parent=None):
        super(CorfuncWindow, self).__init__()
        self.setupUi(self)

        self.setWindowTitle("Corfunc Perspective")

        self.mapper = None
        self.model = QtGui.QStandardItemModel(self)
        self.communicate = GuiUtils.Communicate()
        self._calculator = CorfuncCalculator()
        self._allow_close = True

        self._canvas = MyMplCanvas(self.model)
        self._realplot = MyMplCanvas(self.model)
        self.verticalLayout_7.insertWidget(0, self._canvas)
        self.verticalLayout_7.insertWidget(1, self._realplot)

        # Connect buttons to slots.
        # Needs to be done early so default values propagate properly.
        self.setup_slots()

        # Set up the model.
        self.setup_model()

        # Set up the mapper
        self.setup_mapper()

    def setup_slots(self):
        """Connect the buttons to their appropriate slots."""
        self.extrapolateBtn.clicked.connect(self.extrapolate)
        self.extrapolateBtn.setEnabled(False)
        self.transformBtn.clicked.connect(self.transform)
        self.transformBtn.setEnabled(False)

        self.calculateBgBtn.clicked.connect(self.calculate_background)
        self.calculateBgBtn.setEnabled(False)

        self.model.itemChanged.connect(self.model_changed)

    def setup_model(self):
        """Populate the model with default data."""
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

    def model_changed(self, _):
        """Actions to perform when the data is updated"""
        if not self.mapper:
            return
        self.mapper.toFirst()
        self._canvas.draw_q_space()

    def _update_calculator(self):
        self._calculator.lowerq = float(self.model.item(W.W_QMIN).text())
        qmax1 = float(self.model.item(W.W_QMAX).text())
        qmax2 = float(self.model.item(W.W_QCUTOFF).text())
        self._calculator.upperq = (qmax1, qmax2)
        self._calculator.background = \
            float(self.model.item(W.W_BACKGROUND).text())

    def extrapolate(self):
        """Extend the experiemntal data with guinier and porod curves."""
        self._update_calculator()
        params, extrapolation, _ = self._calculator.compute_extrapolation()

        self.model.setItem(W.W_GUINIERA, QtGui.QStandardItem(str(params['A'])))
        self.model.setItem(W.W_GUINIERB, QtGui.QStandardItem(str(params['B'])))
        self.model.setItem(W.W_PORODK, QtGui.QStandardItem(str(params['K'])))
        self.model.setItem(W.W_PORODSIGMA,
                           QtGui.QStandardItem(str(params['sigma'])))

        self._canvas.extrap = extrapolation
        self._canvas.draw_q_space()
        self.transformBtn.setEnabled(True)

    def transform(self):
        """Calculate the real space version of the extrapolation."""
        method = str(self.model.item(W.W_TRANSFORM).text()).lower()

        extrap = self._canvas.extrap
        background = float(self.model.item(W.W_BACKGROUND).text())

        def updatefn(msg):
            """Report progress of transformation."""
            self.communicate.statusBarUpdateSignal.emit(msg)

        def completefn(transforms):
            """Extract the values from the transforms and plot"""
            self._realplot.data = transforms
            self._realplot.draw_real_space()
            params = self._calculator.extract_parameters(transforms[0])
            self.model.setItem(W.W_CORETHICK,
                               QtGui.QStandardItem(str(params['d0'])))
            self.model.setItem(W.W_INTTHICK,
                               QtGui.QStandardItem(str(params['dtr'])))
            self.model.setItem(W.W_HARDBLOCK,
                               QtGui.QStandardItem(str(params['Lc'])))
            self.model.setItem(W.W_CRYSTAL,
                               QtGui.QStandardItem(str(params['fill'])))
            self.model.setItem(W.W_POLY,
                               QtGui.QStandardItem(str(params['A'])))
            self.model.setItem(W.W_PERIOD,
                               QtGui.QStandardItem(str(params['max'])))

        self._update_calculator()
        self._calculator.compute_transform(extrap, method, background,
                                           completefn, updatefn)

    def setup_mapper(self):
        """Creating mapping between model and gui elements."""
        self.mapper = QtGui.QDataWidgetMapper(self)
        self.mapper.setOrientation(QtCore.Qt.Vertical)
        self.mapper.setModel(self.model)

        self.mapper.addMapping(self.qMin, W.W_QMIN)
        self.mapper.addMapping(self.qMax1, W.W_QMAX)
        self.mapper.addMapping(self.qMax2, W.W_QCUTOFF)
        self.mapper.addMapping(self.bg, W.W_BACKGROUND)
        self.mapper.addMapping(self.transformCombo, W.W_TRANSFORM)

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

    def calculate_background(self):
        """Find a good estimate of the background value."""
        self._update_calculator()
        background = self._calculator.compute_background()
        temp = QtGui.QStandardItem(str(background))
        self.model.setItem(W.W_BACKGROUND, temp)

    # pylint: disable=invalid-name
    @staticmethod
    def allowBatch():
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

        model_item = data_item[0]
        data = GuiUtils.dataFromItem(model_item)
        self._calculator.set_data(data)
        self.calculateBgBtn.setEnabled(True)
        self.extrapolateBtn.setEnabled(True)

        self._canvas.data = data
        self._canvas.draw_q_space()

        # self.model.item(WIDGETS.W_FILENAME).setData(QtCoreQVariant(self._model_item.text()))

    def setClosable(self, value=True):
        """
        Allow outsiders close this widget
        """
        assert isinstance(value, bool)

        self._allow_close = value
    # pylint: enable=invalid-name


if __name__ == "__main__":
    APPLICATION = QtGui.QApplication([])
    import qt4reactor
    qt4reactor.install()
    # DO NOT move the following import to the top!
    # (unless you know what you're doing)
    from twisted.internet import reactor
    DIALOG = CorfuncWindow(reactor)
    DIALOG.show()
    reactor.run()
