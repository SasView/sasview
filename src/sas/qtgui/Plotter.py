from PyQt4 import QtGui

import matplotlib.pyplot as plt

from sas.sasgui.plottools import transform
from sas.sasgui.plottools.convert_units import convert_unit
from sas.qtgui.PlotterBase import PlotterBase

class PlotterWidget(PlotterBase):
    """
    1D Plot widget for use with a QDialog
    """
    def __init__(self, parent=None, manager=None, quickplot=False):
        super(PlotterWidget, self).__init__(parent, manager=manager, quickplot=quickplot)

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        """ data setter """
        self._data = value
        self.xLabel = "%s(%s)"%(value._xaxis, value._xunit)
        self.yLabel = "%s(%s)"%(value._yaxis, value._yunit)
        self.title(title=value.title)

    def plot(self, marker=None, linestyle=None, hide_error=False):
        """
        Plot self._data
        """
        # Shortcut for an axis
        ax = self.ax

        if marker == None:
            marker = 'o'

        if linestyle == None:
            linestyle = ''

        # plot data with/without errorbars
        if hide_error:
            ax.plot(self._data.view.x, self._data.view.y,
                    marker=marker,
                    linestyle=linestyle,
                    label=self._title)
        else:
            ax.errorbar(self._data.view.x, self._data.view.y,
                        yerr=self._data.view.dx, xerr=None,
                        capsize=2, linestyle='',
                        barsabove=False,
                        marker=marker,
                        lolims=False, uplims=False,
                        xlolims=False, xuplims=False,
                        label=self._title)

        # Now add the legend with some customizations.
        legend = ax.legend(loc='upper right', shadow=True)

        # Current labels for axes
        ax.set_ylabel(self.y_label)
        ax.set_xlabel(self.x_label)

        # Title only for regular charts
        if not self.quickplot:
            ax.set_title(label=self._title)

        # Include scaling (log vs. linear)
        ax.set_yscale(self.xscale)
        ax.set_xscale(self.xscale)

        # refresh canvas
        self.canvas.draw()

    def contextMenuQuickPlot(self):
        """
        Define context menu and associated actions for the quickplot MPL widget
        """
        # Actions
        self.contextMenu = QtGui.QMenu(self)
        self.actionSaveImage = self.contextMenu.addAction("Save Image")
        self.actionPrintImage = self.contextMenu.addAction("Print Image")
        self.actionCopyToClipboard = self.contextMenu.addAction("Copy to Clipboard")
        self.contextMenu.addSeparator()
        self.actionToggleGrid = self.contextMenu.addAction("Toggle Grid On/Off")
        self.contextMenu.addSeparator()
        self.actionChangeScale = self.contextMenu.addAction("Change Scale")

        # Define the callbacks
        self.actionSaveImage.triggered.connect(self.onImageSave)
        self.actionPrintImage.triggered.connect(self.onImagePrint)
        self.actionCopyToClipboard.triggered.connect(self.onClipboardCopy)
        self.actionToggleGrid.triggered.connect(self.onGridToggle)
        self.actionChangeScale.triggered.connect(self.onScaleChange)

    def onScaleChange(self):
        """
        Show a dialog allowing axes rescaling
        """
        if self.properties.exec_() == QtGui.QDialog.Accepted:
            xLabel, yLabel = self.properties.getValues()
            self.xyTransform(xLabel, yLabel)

    def xyTransform(self, xLabel="", yLabel=""):
        """
        Transforms x and y in View and set the scale
        """
        # Clear the plot first
        plt.cla()

        # Changing the scale might be incompatible with
        # currently displayed data (for instance, going
        # from ln to log when all plotted values have
        # negative natural logs).
        # Go linear and only change the scale at the end.
        self._xscale = "linear"
        self._yscale = "linear"
        _xscale = 'linear'
        _yscale = 'linear'
        # Local data is either 1D or 2D
        if self.data.id == 'fit':
            return

        # control axis labels from the panel itself
        yname, yunits = self.data.get_yaxis()
        xname, xunits = self.data.get_xaxis()

        # Goes through all possible scales
        # self.x_label is already wrapped with Latex "$", so using the argument

        # X
        if xLabel == "x":
            self.data.transformX(transform.toX, transform.errToX)
            self.xLabel = "%s(%s)" % (xname, xunits)
        if xLabel == "x^(2)":
            self.data.transformX(transform.toX2, transform.errToX2)
            xunits = convert_unit(2, xunits)
            self.xLabel = "%s^{2}(%s)" % (xname, xunits)
        if xLabel == "x^(4)":
            self.data.transformX(transform.toX4, transform.errToX4)
            xunits = convert_unit(4, xunits)
            self.xLabel = "%s^{4}(%s)" % (xname, xunits)
        if xLabel == "ln(x)":
            self.data.transformX(transform.toLogX, transform.errToLogX)
            self.xLabel = "\ln{(%s)}(%s)" % (xname, xunits)
        if xLabel == "log10(x)":
            self.data.transformX(transform.toX_pos, transform.errToX_pos)
            _xscale = 'log'
            self.xLabel = "%s(%s)" % (xname, xunits)
        if xLabel == "log10(x^(4))":
            self.data.transformX(transform.toX4, transform.errToX4)
            xunits = convert_unit(4, xunits)
            self.xLabel = "%s^{4}(%s)" % (xname, xunits)
            _xscale = 'log'

        # Y
        if yLabel == "ln(y)":
            self.data.transformY(transform.toLogX, transform.errToLogX)
            self.yLabel = "\ln{(%s)}(%s)" % (yname, yunits)
        if yLabel == "y":
            self.data.transformY(transform.toX, transform.errToX)
            self.yLabel = "%s(%s)" % (yname, yunits)
        if yLabel == "log10(y)":
            self.data.transformY(transform.toX_pos, transform.errToX_pos)
            _yscale = 'log'
            self.yLabel = "%s(%s)" % (yname, yunits)
        if yLabel == "y^(2)":
            self.data.transformY(transform.toX2, transform.errToX2)
            yunits = convert_unit(2, yunits)
            self.yLabel = "%s^{2}(%s)" % (yname, yunits)
        if yLabel == "1/y":
            self.data.transformY(transform.toOneOverX, transform.errOneOverX)
            yunits = convert_unit(-1, yunits)
            self.yLabel = "1/%s(%s)" % (yname, yunits)
        if yLabel == "y*x^(2)":
            self.data.transformY(transform.toYX2, transform.errToYX2)
            xunits = convert_unit(2, xunits)
            self.yLabel = "%s \ \ %s^{2}(%s%s)" % (yname, xname, yunits, xunits)
        if yLabel == "y*x^(4)":
            self.data.transformY(transform.toYX4, transform.errToYX4)
            xunits = convert_unit(4, xunits)
            self.yLabel = "%s \ \ %s^{4}(%s%s)" % (yname, xname, yunits, xunits)
        if yLabel == "1/sqrt(y)":
            self.data.transformY(transform.toOneOverSqrtX,
                                 transform.errOneOverSqrtX)
            yunits = convert_unit(-0.5, yunits)
            self.yLabel = "1/\sqrt{%s}(%s)" % (yname, yunits)
        if yLabel == "ln(y*x)":
            self.data.transformY(transform.toLogXY, transform.errToLogXY)
            self.yLabel = "\ln{(%s \ \ %s)}(%s%s)" % (yname, xname, yunits, xunits)
        if yLabel == "ln(y*x^(2))":
            self.data.transformY(transform.toLogYX2, transform.errToLogYX2)
            xunits = convert_unit(2, xunits)
            self.yLabel = "\ln (%s \ \ %s^{2})(%s%s)" % (yname, xname, yunits, xunits)
        if yLabel == "ln(y*x^(4))":
            self.data.transformY(transform.toLogYX4, transform.errToLogYX4)
            xunits = convert_unit(4, xunits)
            self.yLabel = "\ln (%s \ \ %s^{4})(%s%s)" % (yname, xname, yunits, xunits)
        if yLabel == "log10(y*x^(4))":
            self.data.transformY(transform.toYX4, transform.errToYX4)
            xunits = convert_unit(4, xunits)
            _yscale = 'log'
            self.yLabel = "%s \ \ %s^{4}(%s%s)" % (yname, xname, yunits, xunits)

        # Perform the transformation of data in data1d->View
        self.data.transformView()

        self.xscale = _xscale
        self.yscale = _yscale

        # Plot the updated chart
        self.plot(marker='o', linestyle='')


class Plotter(QtGui.QDialog, PlotterWidget):
    def __init__(self, parent=None, quickplot=False):

        QtGui.QDialog.__init__(self)
        PlotterWidget.__init__(self, manager=parent, quickplot=quickplot)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/res/ball.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(icon)


