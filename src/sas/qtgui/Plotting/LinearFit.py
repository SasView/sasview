"""
Adds a linear fit plot to the chart
"""
import re
import numpy
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from sas.qtgui.Utilities.GuiUtils import formatNumber, DoubleValidator

from sas.qtgui.Plotting import Fittings
from sas.qtgui.Plotting import DataTransform
from sas.qtgui.Plotting.LineModel import LineModel
import sas.qtgui.Utilities.GuiUtils as GuiUtils

# Local UI
from sas.qtgui.UI import main_resources_rc
from sas.qtgui.Plotting.UI.LinearFitUI import Ui_LinearFitUI

class LinearFit(QtWidgets.QDialog, Ui_LinearFitUI):
    updatePlot = QtCore.pyqtSignal(tuple)
    def __init__(self, parent=None,
                 data=None,
                 max_range=(0.0, 0.0),
                 fit_range=(0.0, 0.0),
                 xlabel="",
                 ylabel=""):
        super(LinearFit, self).__init__()

        self.setupUi(self)
        assert(isinstance(max_range, tuple))
        assert(isinstance(fit_range, tuple))

        self.data = data
        self.parent = parent

        self.max_range = max_range
        self.fit_range = fit_range
        self.xLabel = xlabel
        self.yLabel = ylabel

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
        self.txtRangeMin.setText(str(max_range[0]))
        self.txtRangeMax.setText(str(max_range[1]))
        # Assure nice display of ranges
        fr_min = GuiUtils.formatNumber(fit_range[0])
        fr_max = GuiUtils.formatNumber(fit_range[1])
        self.txtFitRangeMin.setText(str(fr_min))
        self.txtFitRangeMax.setText(str(fr_max))

        # cast xLabel into html
        label = re.sub(r'\^\((.)\)(.*)', r'<span style=" vertical-align:super;">\1</span>\2',
                      str(self.xLabel).rstrip())
        self.lblRange.setText('Fit range of ' + label)

        self.model = LineModel()
        # Display the fittings values
        self.default_A = self.model.getParam('A')
        self.default_B = self.model.getParam('B')
        self.cstA = Fittings.Parameter(self.model, 'A', self.default_A)
        self.cstB = Fittings.Parameter(self.model, 'B', self.default_B)
        self.transform = DataTransform

        self.setFixedSize(self.minimumSizeHint())

        # connect Fit button
        self.cmdFit.clicked.connect(self.fit)

    def setRangeLabel(self, label=""):
        """
        Overwrite default fit range label to correspond to actual unit
        """
        assert(isinstance(label, str))
        self.lblRange.setText(label)

    def range(self):
        return (float(self.txtFitRangeMin.text()), float(self.txtFitRangeMax.text()))

    def fit(self, event):
        """
        Performs the fit. Receive an event when clicking on
        the button Fit.Computes chisqr ,
        A and B parameters of the best linear fit y=Ax +B
        Push a plottable to the caller
        """
        tempx = []
        tempy = []
        tempdy = []

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
        tempdy = numpy.asarray(tempdy)
        tempdy[tempdy == 0] = 1

        if self.x_is_log:
            xmin = numpy.log10(xmin)
            xmax = numpy.log10(xmax)

        chisqr, out, cov = Fittings.sasfit(self.model,
                                           [self.cstA, self.cstB],
                                           tempx, tempy, tempdy,
                                           xmin, xmax)
        # Use chi2/dof
        if len(tempx) > 0:
            chisqr = chisqr / len(tempx)

        # Check that cov and out are iterable before displaying them
        errA = numpy.sqrt(cov[0][0]) if cov is not None else 0
        errB = numpy.sqrt(cov[1][1]) if cov is not None else 0
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
        tempy.append(numpy.power(10.0, y_model) if self.y_is_log else y_model)

        # load tempy with the maximum transformation
        y_model = self.model.run(xmax)
        tempx.append(xmaxView)
        tempy.append(numpy.power(10.0, y_model) if self.y_is_log else y_model)

        # Set the fit parameter display when  FitDialog is opened again
        self.Avalue = cstA
        self.Bvalue = cstB
        self.ErrAvalue = errA
        self.ErrBvalue = errB
        self.Chivalue = chisqr

        # Update the widget
        self.txtA.setText(formatNumber(self.Avalue))
        self.txtAerr.setText(formatNumber(self.ErrAvalue))
        self.txtB.setText(formatNumber(self.Bvalue))
        self.txtBerr.setText(formatNumber(self.ErrBvalue))
        self.txtChi2.setText(formatNumber(self.Chivalue))

        self.updatePlot.emit((tempx, tempy))

    def origData(self):
        # Store the transformed values of view x, y and dy before the fit
        xmin_check = numpy.log10(self.xminFit)
        # Local shortcuts
        x = self.data.view.x
        y = self.data.view.y
        dy = self.data.view.dy

        if self.y_is_log:
            if self.x_is_log:
                tempy  = [numpy.log10(y[i])
                         for i in range(len(x)) if x[i] >= xmin_check]
                tempdy = [DataTransform.errToLogX(y[i], 0, dy[i], 0)
                         for i in range(len(x)) if x[i] >= xmin_check]
            else:
                tempy = list(map(numpy.log10, y))
                tempdy = list(map(lambda t1,t2:DataTransform.errToLogX(t1,0,t2,0),y,dy))
        else:
            tempy = y
            tempdy = dy

        if self.x_is_log:
            tempx = [numpy.log10(x) for x in self.data.view.x if x > xmin_check]
        else:
            tempx = x

        return tempx, tempy, tempdy

    def checkFitValues(self, item):
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

    def floatInvTransform(self, x):
        """
        transform a float.It is used to determine the x.View min and x.View
        max for values not in x.  Also used to properly calculate RgQmin,
        RgQmax and to update qmin and qmax in the linear range boxes on the
        panel.

        """
        # TODO: refactor this. This is just a hack to make the
        # functionality work without rewritting the whole code
        # with good design (which really should be done...).
        if self.xLabel == "x":
            return x
        elif self.xLabel == "x^(2)":
            return numpy.sqrt(x)
        elif self.xLabel == "x^(4)":
            return numpy.sqrt(numpy.sqrt(x))
        elif self.xLabel == "log10(x)":
            return numpy.power(10.0, x)
        elif self.xLabel == "ln(x)":
            return numpy.exp(x)
        elif self.xLabel == "log10(x^(4))":
            return numpy.sqrt(numpy.sqrt(numpy.power(10.0, x)))
        return x


