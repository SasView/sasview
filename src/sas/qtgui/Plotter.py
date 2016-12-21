from PyQt4 import QtGui

import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

from sas.sasgui.guiframe.dataFitting import Data1D
from sas.sasgui.plottools import transform
from sas.sasgui.plottools.convert_units import convert_unit
from sas.qtgui.PlotterBase import PlotterBase
from sas.qtgui.AddText import AddText
from sas.qtgui.SetGraphRange import SetGraphRange

class PlotterWidget(PlotterBase):
    """
    1D Plot widget for use with a QDialog
    """
    def __init__(self, parent=None, manager=None, quickplot=False):
        super(PlotterWidget, self).__init__(parent, manager=manager, quickplot=quickplot)
        self.parent = parent
        self.addText = AddText(self)

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

    def plot(self, data=None, marker=None, linestyle=None, hide_error=False):
        """
        Plot self._data
        """
        # Data1D
        if isinstance(data, Data1D):
            self.data = data
        assert(self._data)

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
                    label=self._title,
                    picker=True)
        else:
            ax.errorbar(self._data.view.x, self._data.view.y,
                        yerr=self._data.view.dx, xerr=None,
                        capsize=2, linestyle='',
                        barsabove=False,
                        marker=marker,
                        lolims=False, uplims=False,
                        xlolims=False, xuplims=False,
                        label=self._title,
                        picker=True)

        # Now add the legend with some customizations.
        self.legend = ax.legend(loc='upper right', shadow=True)
        #self.legend.get_frame().set_alpha(0.4)
        self.legend.set_picker(True)

        # Current labels for axes
        ax.set_ylabel(self.y_label)
        ax.set_xlabel(self.x_label)

        # Title only for regular charts
        if not self.quickplot:
            ax.set_title(label=self._title)

        # Include scaling (log vs. linear)
        ax.set_xscale(self.xscale)
        ax.set_yscale(self.yscale)

        # define the ranges
        self.setRange = SetGraphRange(parent=self,
            x_range=self.ax.get_xlim(), y_range=self.ax.get_ylim())

        # refresh canvas
        self.canvas.draw()

    def contextMenu(self):
        """
        Define common context menu and associated actions for the MPL widget
        """
        self.defaultContextMenu()

        # Additional menu items
        self.contextMenu.addSeparator()
        self.actionModifyGraphAppearance =\
            self.contextMenu.addAction("Modify Graph Appearance")
        self.contextMenu.addSeparator()
        self.actionAddText = self.contextMenu.addAction("Add Text")
        self.actionRemoveText = self.contextMenu.addAction("Remove Text")
        self.contextMenu.addSeparator()
        self.actionChangeScale = self.contextMenu.addAction("Change Scale")
        self.contextMenu.addSeparator()
        self.actionSetGraphRange = self.contextMenu.addAction("Set Graph Range")
        self.actionResetGraphRange =\
            self.contextMenu.addAction("Reset Graph Range")
        # Add the title change for dialogs
        if self.parent:
            self.contextMenu.addSeparator()
            self.actionWindowTitle = self.contextMenu.addAction("Window Title")

        # Define the callbacks
        self.actionModifyGraphAppearance.triggered.connect(self.onModifyGraph)
        self.actionAddText.triggered.connect(self.onAddText)
        self.actionRemoveText.triggered.connect(self.onRemoveText)
        self.actionChangeScale.triggered.connect(self.onScaleChange)
        self.actionSetGraphRange.triggered.connect(self.onSetGraphRange)
        self.actionResetGraphRange.triggered.connect(self.onResetGraphRange)
        self.actionWindowTitle.triggered.connect(self.onWindowsTitle)

    def contextMenuQuickPlot(self):
        """
        Define context menu and associated actions for the quickplot MPL widget
        """
        # Default actions
        self.defaultContextMenu()

        # Additional actions
        self.actionToggleGrid = self.contextMenu.addAction("Toggle Grid On/Off")
        self.contextMenu.addSeparator()
        self.actionChangeScale = self.contextMenu.addAction("Change Scale")

        # Define the callbacks
        self.actionToggleGrid.triggered.connect(self.onGridToggle)
        self.actionChangeScale.triggered.connect(self.onScaleChange)

    def onScaleChange(self):
        """
        Show a dialog allowing axes rescaling
        """
        if self.properties.exec_() == QtGui.QDialog.Accepted:
            xLabel, yLabel = self.properties.getValues()
            self.xyTransform(xLabel, yLabel)

    def onModifyGraph(self):
        """
        Show a dialog allowing chart manipulations
        """
        print ("onModifyGraph")
        pass

    def onAddText(self):
        """
        Show a dialog allowing adding custom text to the chart
        """
        if self.addText.exec_() == QtGui.QDialog.Accepted:
            # Retrieve the new text, its font and color
            extra_text = self.addText.text()
            extra_font = self.addText.font()
            extra_color = self.addText.color()

            # Place the text on the screen at (0,0)
            pos_x = self.x_click
            pos_y = self.y_click

            # Map QFont onto MPL font
            mpl_font = FontProperties()
            mpl_font.set_size(int(extra_font.pointSize()))
            mpl_font.set_family(str(extra_font.family()))
            mpl_font.set_weight(int(extra_font.weight()))
            # MPL style names
            styles = ['normal', 'italic', 'oblique']
            # QFont::Style maps directly onto the above
            try:
                mpl_font.set_style(styles[extra_font.style()])
            except:
                pass

            if len(extra_text) > 0:
                new_text = self.ax.text(str(pos_x),
                                        str(pos_y),
                                        extra_text,
                                        color=extra_color,
                                        fontproperties=mpl_font)
                # Update the list of annotations
                self.textList.append(new_text)
                self.canvas.draw_idle()

    def onRemoveText(self):
        """
        Remove the most recently added text
        """
        num_text = len(self.textList)
        if num_text < 1:
            return
        txt = self.textList[num_text - 1]
        text_remove = txt.get_text()
        txt.remove()
        self.textList.remove(txt)

        self.canvas.draw_idle()

    def onSetGraphRange(self):
        """
        Show a dialog allowing setting the chart ranges
        """
        # min and max of data
        if self.setRange.exec_() == QtGui.QDialog.Accepted:
            x_range = self.setRange.xrange()
            y_range = self.setRange.yrange()
            if x_range is not None and y_range is not None:
                self.ax.set_xlim(x_range)
                self.ax.set_ylim(y_range)
                self.canvas.draw_idle()

    def onResetGraphRange(self):
        """
        Resets the chart X and Y ranges to their original values
        """
        x_range = (self.data.x.min(), self.data.x.max())
        y_range = (self.data.y.min(), self.data.y.max())
        if x_range is not None and y_range is not None:
            self.ax.set_xlim(x_range)
            self.ax.set_ylim(y_range)
            self.canvas.draw_idle()

    def xyTransform(self, xLabel="", yLabel=""):
        """
        Transforms x and y in View and set the scale
        """
        # Clear the plot first
        plt.cla()
        self.ax.cla()

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


