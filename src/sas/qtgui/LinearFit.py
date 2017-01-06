"""
Adds a linear fit plot to the chart
"""
import numpy
from PyQt4 import QtGui
from PyQt4 import QtCore

#from sas.sasgui.transform import 
from sas.qtgui.GuiUtils import formatNumber
from sas.sasgui.plottools import fittings
from sas.sasgui.plottools import transform

from sas.sasgui.plottools.LineModel import LineModel

# Local UI
from sas.qtgui.UI.LinearFitUI import Ui_LinearFitUI

class LinearFit(QtGui.QDialog, Ui_LinearFitUI):
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

        self.txtFitRangeMin.setValidator(QtGui.QDoubleValidator())
        self.txtFitRangeMax.setValidator(QtGui.QDoubleValidator())

        # Default values in the line edits
        self.txtA.setText("1")
        self.txtB.setText("1")
        self.txtAerr.setText("0")
        self.txtBerr.setText("0")
        self.txtChi2.setText("0")
        # Initial ranges
        self.txtRangeMin.setText(str(max_range[0]))
        self.txtRangeMax.setText(str(max_range[1]))
        self.txtFitRangeMin.setText(str(fit_range[0]))
        self.txtFitRangeMax.setText(str(fit_range[1]))

        self.lblRange.setText('Fit range of ' + self.xLabel)

        self.model = LineModel()
        # Display the fittings values
        self.default_A = self.model.getParam('A')
        self.default_B = self.model.getParam('B')
        self.cstA = fittings.Parameter(self.model, 'A', self.default_A)
        self.cstB = fittings.Parameter(self.model, 'B', self.default_B)
        self.transform = transform

        self.cmdFit.clicked.connect(self.fit)

    def setRangeLabel(self, label=""):
        """
        Overwrite default fit range label to correspond to actual unit
        """
        assert(isinstance(label, basestring))
        self.lblRange.setText(label)

    def a(self):
        return (float(self.txtA.text()), float(self.txtAerr.text()))

    def b(self):
        return (float(self.txtB.text()), float(self.txtBerr.text()))

    def chi(self):
        return float(self.txtChi2.text())

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

        xminView = self.xminFit
        xmaxView = self.xmaxFit
        xmin = xminView
        xmax = xmaxView
        # Set the qmin and qmax in the panel that matches the
        # transformed min and max
        self.txtRangeMin.setText(formatNumber(self.floatInvTransform(xmin)))
        self.txtRangeMax.setText(formatNumber(self.floatInvTransform(xmax)))

        # Store the transformed values of view x, y and dy before the fit
        xmin_check = numpy.log10(xmin)
        x = self.data.view.x
        y = self.data.view.y
        dy = self.data.view.dy

        if self.yLabel == "log10(y)":
            if self.xLabel == "log10(x)":
                tempy  = [numpy.log10(y[i])
                         for i in range(len(x)) if x[i] >= xmin_check]
                tempdy = [transform.errToLogX(y[i], 0, dy[i], 0)
                         for i in range(len(x)) if x[i] >= xmin_check]
            else:
                tempy = map(numpy.log10, y)
                tempdy = map(lambda t1,t2:transform.errToLogX(t1,0,t2,0),y,dy)
        else:
            tempy = y
            tempdy = dy

        if self.xLabel == "log10(x)":
            tempx = [numpy.log10(x) for x in self.data.view.x if x > xmin_check]
        else:
            tempx = self.data.view.x

        # Find the fitting parameters
        # Always use the same defaults, so that fit history
        # doesn't play a role!
        self.cstA = fittings.Parameter(self.model, 'A', self.default_A)
        self.cstB = fittings.Parameter(self.model, 'B', self.default_B)
        tempdy = numpy.asarray(tempdy)
        tempdy[tempdy == 0] = 1

        if self.xLabel == "log10(x)":
            chisqr, out, cov = fittings.sasfit(self.model,
                                               [self.cstA, self.cstB],
                                               tempx, tempy,
                                               tempdy,
                                               numpy.log10(xmin),
                                               numpy.log10(xmax))
        else:
            chisqr, out, cov = fittings.sasfit(self.model,
                                               [self.cstA, self.cstB],
                                               tempx, tempy, tempdy,
                                               xminView, xmaxView)
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
        if self.xLabel == "log10(x)":
            y_model = self.model.run(numpy.log10(xmin))
            tempx.append(xmin)
        else:
            y_model = self.model.run(xminView)
            tempx.append(xminView)

        if self.yLabel == "log10(y)":
            tempy.append(numpy.power(10, y_model))
        else:
            tempy.append(y_model)

        # load tempy with the maximum transformation
        if self.xLabel == "log10(x)":
            y_model = self.model.run(numpy.log10(xmax))
            tempx.append(xmax)
        else:
            y_model = self.model.run(xmaxView)
            tempx.append(xmaxView)

        if self.yLabel == "log10(y)":
            tempy.append(numpy.power(10, y_model))
        else:
            tempy.append(y_model)
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

        #self.parent.updatePlot.emit((tempx, tempy))
        self.parent.emit(QtCore.SIGNAL('updatePlot'), (tempx, tempy))

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
        # Check for possible values entered
        if self.xLabel == "log10(x)":
            if float(value) > 0:
                item.setPalette(p_white)
            else:
                flag = False
                item.setPalette(p_pink)
        return flag

    #def checkFitRanges(self, usermin, usermax):
    #    """
    #    Ensure that fields parameter contains a min and a max value
    #    within x min and x max range
    #    """
    #    self.mini = float(self.xminFit.GetValue())
    #    self.maxi = float(self.xmaxFit.GetValue())
    #    flag = True
    #    try:
    #        mini = float(usermin.GetValue())
    #        maxi = float(usermax.GetValue())
    #        if mini < maxi:
    #            usermin.SetBackgroundColour(wx.WHITE)
    #            usermin.Refresh()
    #        else:
    #            flag = False
    #            usermin.SetBackgroundColour("pink")
    #            usermin.Refresh()
    #    except:
    #        # Check for possible values entered
    #        flag = False
    #        usermin.SetBackgroundColour("pink")
    #        usermin.Refresh()

    #    return flag
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
            return numpy.sqrt(math.sqrt(x))
        elif self.xLabel == "log10(x)":
            return numpy.power(10, x)
        elif self.xLabel == "ln(x)":
            return numpy.exp(x)
        elif self.xLabel == "log10(x^(4))":
            return numpy.sqrt(numpy.sqrt(numpy.power(10, x)))
        return x
