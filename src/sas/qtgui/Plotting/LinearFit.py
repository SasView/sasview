"""
Adds a linear fit plot to the chart
"""
import re

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Plotting import DataTransform, Fittings
from sas.qtgui.Plotting.LineModel import LineModel
from sas.qtgui.Plotting.PlotterBase import PlotterBase
from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Plotting.QRangeSlider import QRangeSlider

# Local UI
from sas.qtgui.Plotting.UI.LinearFitUI import Ui_LinearFitUI
from sas.qtgui.Utilities.GuiUtils import DoubleValidator, formatNumber, xyTransform


class LinearFit(QtWidgets.QDialog, Ui_LinearFitUI):
    updatePlot = QtCore.Signal(np.ndarray, np.ndarray)

    def __init__(self, parent: PlotterBase | None = None,
                 data: Data1D | None = None,
                 max_range: tuple = (0.0, 0.0),
                 fit_range: tuple = (0.0, 0.0),
                 xlabel: str = "",
                 ylabel: str = ""):
        super(LinearFit, self).__init__(parent)

        self.setupUi(self)

        assert isinstance(max_range, tuple)
        assert isinstance(fit_range, tuple)

        self.data: Data1D | None = data
        self.parent: PlotterBase | None = parent

        self.max_range: tuple = max_range
        # Set fit minimum to 0.0 if below zero
        if fit_range[0] < 0.0:
            fit_range = (0.0, fit_range[1])
        self.fit_range: tuple = fit_range
        self.xLabel: str = xlabel
        self.yLabel: str = ylabel

        self.rg_on: bool = False
        self.rg_yx: bool = False
        self.bg_on: bool = False

        # Scale dependent content
        self.guinier_box.setVisible(False)
        if (self.yLabel == "ln(y)" or self.yLabel == "ln(y*x)") and \
                (self.xLabel == "x^(2)"):
            if self.yLabel == "ln(y*x)":
                self.label_12.setText('<html><head/><body><p>Rod diameter [Å]</p></body></html>')
                self.rg_yx = True
            self.rg_on = True
            self.guinier_box.setVisible(True)

        if (self.xLabel == "x^(4)") and (self.yLabel == "y*x^(4)"):
            self.bg_on = True
            self.label_3.setText('Background')

        self.x_is_log = self.xLabel == "log10(x)"
        self.y_is_log = self.yLabel == "log10(y)"

        self.txtFitRangeMin.setValidator(DoubleValidator())
        self.txtFitRangeMax.setValidator(DoubleValidator())

        # Default values in the line edits
        self.txtA.setText("1")
        self.txtB.setText("1")
        self.txtAerr.setText("0")
        self.txtBerr.setText("0")
        self.txtChi2.setText("0")

        # Initial ranges
        tr_min = GuiUtils.formatNumber(max_range[0])
        tr_max = GuiUtils.formatNumber(max_range[1])
        self.txtRangeMin.setText(str(tr_min))
        self.txtRangeMax.setText(str(tr_max))
        # Assure nice display of ranges
        fr_min = GuiUtils.formatNumber(fit_range[0])
        fr_max = GuiUtils.formatNumber(fit_range[1])
        self.txtFitRangeMin.setText(str(fr_min))
        self.txtFitRangeMax.setText(str(fr_max))
        self.xminFit: float | None = None
        self.xmaxFit: float | None = None

        # cast xLabel into html
        label = re.sub(r'\^\((.)\)(.*)', r'<span style=" vertical-align:super;">\1</span>\2',
                       str(self.xLabel).rstrip())
        self.lblRange.setText('Fit range of ' + label)

        self.model = LineModel()
        # Display the fittings values
        self.default_A: float = self.model.getParam('A')
        self.default_B: float = self.model.getParam('B')
        self.cstA: Fittings.Parameter = Fittings.Parameter(self.model, 'A', self.default_A)
        self.cstB: Fittings.Parameter = Fittings.Parameter(self.model, 'B', self.default_B)
        self.transform = DataTransform

        self.q_sliders: QRangeSlider | None = None
        self.drawSliders()

        self.setFixedSize(self.minimumSizeHint())

        # connect Fit button
        self.cmdFit.clicked.connect(self.fit)
        self.parent.installEventFilter(self)

    def eventFilter(self, watched: PlotterBase, event: QtCore.QEvent) -> bool:
        if watched is self.parent and event.type() == QtCore.QEvent.Close:
            self.q_sliders = None
            self.close()
        return super(LinearFit, self).eventFilter(watched, event)

    def setRangeLabel(self, label: str = ""):
        """
        Overwrite default fit range label to correspond to actual unit
        """
        assert isinstance(label, str)
        self.lblRange.setText(label)

    def range(self) -> tuple:
        return (float(self.txtFitRangeMin.text()) if float(self.txtFitRangeMin.text()) > 0 else 0.0,
                float(self.txtFitRangeMax.text()))

    def fit(self, event: QtCore.QEvent):
        """
        Performs the fit. Receive an event when clicking on
        the button Fit.Computes chisqr ,
        A and B parameters of the best linear fit y=Ax +B
        Push a plottable to the caller
        """
        # Checks to assure data correctness
        if len(self.data.view.x) < 2:
            return
        if not self.checkFitValues(self.txtFitRangeMin):
            return

        self.xminFit, self.xmaxFit = self.range()

        xmin = self.xminFit
        xmax = self.xmaxFit
        xminView = xmin
        xmaxView = xmax

        # Set the qmin and qmax in the panel that matches the
        # transformed min and max
        value_xmin = self.floatInvTransform(xmin)
        value_xmax = self.floatInvTransform(xmax)
        self.txtRangeMin.setText(formatNumber(value_xmin))
        self.txtRangeMax.setText(formatNumber(value_xmax))

        tempx, tempy, tempdy = self.origData()

        # Find the fitting parameters
        self.cstA = Fittings.Parameter(self.model, 'A', self.default_A)
        self.cstB = Fittings.Parameter(self.model, 'B', self.default_B)
        tempdy = np.asarray(tempdy)
        tempdy[tempdy == 0] = 1

        if self.x_is_log:
            xmin = np.log10(xmin)
            xmax = np.log10(xmax)

        chisqr, out, cov = Fittings.sasfit(self.model,
                                           [self.cstA, self.cstB],
                                           tempx, tempy, tempdy,
                                           xmin, xmax)
        # Use chi2/dof
        if len(tempx) > 0:
            chisqr = chisqr / len(tempx)

        # Check that cov and out are iterable before displaying them
        errA = np.sqrt(cov[0][0]) if cov is not None else 0
        errB = np.sqrt(cov[1][1]) if cov is not None else 0
        cstA = out[0] if out is not None else 0.0
        cstB = out[1] if out is not None else 0.0

        # Reset model with the right values of A and B
        self.model.setParam('A', float(cstA))
        self.model.setParam('B', float(cstB))

        tempx = []
        tempy = []
        y_model = 0.0

        # load tempy with the minimum transformation
        y_model = self.model.run(xmin)
        tempx.append(xminView)
        tempy.append(np.power(10.0, y_model) if self.y_is_log else y_model)

        # load tempy with the maximum transformation
        y_model = self.model.run(xmax)
        tempx.append(xmaxView)
        tempy.append(np.power(10.0, y_model) if self.y_is_log else y_model)

        # Set the fit parameter display when  FitDialog is opened again
        self.Avalue: float = cstA
        self.Bvalue: float = cstB
        self.ErrAvalue: float = errA
        self.ErrBvalue: float = errB
        self.Chivalue: float = chisqr

        # Update the widget
        self.txtA.setText(formatNumber(self.Avalue))
        self.txtAerr.setText(formatNumber(self.ErrAvalue))
        self.txtB.setText(formatNumber(self.Bvalue))
        self.txtBerr.setText(formatNumber(self.ErrBvalue))
        self.txtChi2.setText(formatNumber(self.Chivalue))

        # Possibly Guinier analysis
        i0 = np.exp(cstB)
        self.txtGuinier_1.setText(formatNumber(i0))
        err = np.abs(np.exp(cstB) * errB)
        self.txtGuinier1_Err.setText(formatNumber(err))

        if self.rg_yx:
            rg = np.sqrt(-2 * float(cstA))
            diam = 4 * np.sqrt(-float(cstA))
            value = formatNumber(diam)
            if rg is not None and rg != 0:
                err = formatNumber(8 * float(errA) / diam)
            else:
                err = ''
        else:
            rg = np.sqrt(-3 * float(cstA))
            value = formatNumber(rg)

            if rg is not None and rg != 0:
                err = formatNumber(3 * float(errA) / (2 * rg))
            else:
                err = ''

        self.txtGuinier_2.setText(value)
        self.txtGuinier2_Err.setText(err)

        value = formatNumber(rg * self.floatInvTransform(self.xminFit))
        self.txtGuinier_4.setText(value)
        value = formatNumber(rg * self.floatInvTransform(self.xmaxFit))
        self.txtGuinier_3.setText(value)

        tempx = np.array(tempx)
        tempy = np.array(tempy)

        self.drawSliders()
        self.updatePlot.emit(tempx, tempy)

    def origData(self) -> (np.ndarray, np.ndarray, np.ndarray):
        # Store the transformed values of view x, y and dy before the fit
        xmin_check = np.log10(self.xminFit)
        # Local shortcuts
        x = self.data.view.x
        y = self.data.view.y
        dy = self.data.view.dy

        if self.y_is_log:
            if self.x_is_log:
                tempy  = [np.log10(y[i])
                         for i in range(len(x)) if x[i] >= xmin_check]
                tempdy = [DataTransform.errToLogX(y[i], 0, dy[i], 0)
                         for i in range(len(x)) if x[i] >= xmin_check]
            else:
                tempy = list(map(np.log10, y))
                tempdy = list(map(lambda t1,t2:DataTransform.errToLogX(t1,0,t2,0),y,dy))
        else:
            tempy = y
            tempdy = dy

        if self.x_is_log:
            tempx = [np.log10(x) for x in self.data.view.x if x > xmin_check]
        else:
            tempx = x

        return np.array(tempx), np.array(tempy), np.array(tempdy)

    def checkFitValues(self, item: QtWidgets.QLineEdit) -> bool:
        """
        Check the validity of input values
        """
        flag = True
        value = item.text()
        p_white = item.palette()
        p_white.setColor(item.backgroundRole(), QtCore.Qt.white)
        p_pink = item.palette()
        p_pink.setColor(item.backgroundRole(), QtGui.QColor(255, 128, 128))
        item.setAutoFillBackground(True)
        # Check for possible values entered
        if self.x_is_log:
            if float(value) > 0:
                item.setPalette(p_white)
            else:
                flag = False
                item.setPalette(p_pink)
        return flag

    def floatInvTransform(self, x: float) -> float:
        """
        transform a float.It is used to determine the x.View min and x.View
        max for values not in x.  Also used to properly calculate RgQmin,
        RgQmax and to update qmin and qmax in the linear range boxes on the
        panel.

        """
        xyTransform(self.data, self.xLabel, self.yLabel)
        match self.xLabel:
            case "x^(2)":
                return np.sqrt(x)
            case "x^(4)":
                return np.sqrt(np.sqrt(x))
            case "log10(x)":
                return np.power(10.0, x)
            case "ln(x)":
                return np.exp(x)
            case "log10(x^(4))":
                return np.sqrt(np.sqrt(np.power(10.0, x)))
            case _:
                return x

    def drawSliders(self):
        """Show new Q-range sliders"""
        # Always remove the previous slider before drawing new ones
        self.clearSliders()
        self.data.show_q_range_sliders = True
        self.q_sliders = QRangeSlider(self.parent, self.parent.ax, data=self.data)
        self.q_sliders.line_min.input = self.txtFitRangeMin
        self.q_sliders.line_max.input = self.txtFitRangeMax

    def clearSliders(self):
        """Clear existing sliders"""
        if self.q_sliders:
            self.q_sliders.clear()
        self.data.show_q_range_sliders = False
        self.q_sliders = None
        self.parent.toggleSlider(self.data.name)
        self.parent.canvas.draw_idle()

    def closeEvent(self, ev: QtCore.QEvent):
        self.clearSliders()

    def accept(self):
        self.clearSliders()
        self.close()

    def reject(self):
        self.clearSliders()
        self.close()
