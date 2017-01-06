from PyQt4 import QtGui
from PyQt4 import QtCore
import functools
import copy

import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

from sas.sasgui.guiframe.dataFitting import Data1D
from sas.qtgui.PlotterBase import PlotterBase
import sas.qtgui.GuiUtils as GuiUtils
from sas.qtgui.AddText import AddText
from sas.qtgui.SetGraphRange import SetGraphRange
from sas.qtgui.LinearFit import LinearFit

class PlotterWidget(PlotterBase):
    """
    1D Plot widget for use with a QDialog
    """
    def __init__(self, parent=None, manager=None, quickplot=False):
        super(PlotterWidget, self).__init__(parent, manager=manager, quickplot=quickplot)

        self.parent = parent
        self.addText = AddText(self)

        # Dictionary of {plot_id:Data1d}
        self.plot_dict = {}

        # Simple window for data display
        self.txt_widget = QtGui.QTextEdit(None)

        self.xLogLabel = "log10(x)"
        self.yLogLabel = "log10(y)"

        # Data container for the linear fit
        self.fit_result = Data1D(x=[], y=[], dy=None)
        self.fit_result.symbol = 13
        self.fit_result.name = "Fit"

        # Add a slot for receiving update signal from LinearFit
        # NEW style signals - don't work!
        #self.updatePlot = QtCore.pyqtSignal(tuple)
        #self.updatePlot.connect(self.updateWithData)
        # OLD style signals - work perfectly
        QtCore.QObject.connect(self, QtCore.SIGNAL('updatePlot'), self.onFitDisplay)

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        """ data setter """
        self._data = value
        self.xLabel = "%s(%s)"%(value._xaxis, value._xunit)
        self.yLabel = "%s(%s)"%(value._yaxis, value._yunit)
        self.title(title=value.name)

    def plot(self, data=None, marker=None, linestyle=None, hide_error=False):
        """
        Add a new plot of self._data to the chart.
        """
        # Data1D
        if isinstance(data, Data1D):
            self.data = data
        assert(self._data)

        is_fit = (self._data.id=="fit")

        # Shortcut for an axis
        ax = self.ax

        if marker == None:
            marker = 'o'

        if linestyle == None:
            linestyle = ''

        if not self._title:
            self.title(title=self.data.name)

        # plot data with/without errorbars
        if hide_error:
            line = ax.plot(self._data.view.x, self._data.view.y,
                    marker=marker,
                    linestyle=linestyle,
                    label=self._title,
                    picker=True)
        else:
            line = ax.errorbar(self._data.view.x, self._data.view.y,
                        yerr=self._data.view.dy, xerr=None,
                        capsize=2, linestyle='',
                        barsabove=False,
                        marker=marker,
                        lolims=False, uplims=False,
                        xlolims=False, xuplims=False,
                        label=self._title,
                        picker=True)

        # Update the list of data sets (plots) in chart
        self.plot_dict[self._data.id] = self.data

        # Now add the legend with some customizations.
        self.legend = ax.legend(loc='upper right', shadow=True)
        self.legend.set_picker(True)

        # Current labels for axes
        if self.y_label and not is_fit:
            ax.set_ylabel(self.y_label)
        if self.x_label and not is_fit:
            ax.set_xlabel(self.x_label)

        # Title only for regular charts
        if not self.quickplot and not is_fit:
            ax.set_title(label=self._title)

        # Include scaling (log vs. linear)
        ax.set_xscale(self.xscale)
        ax.set_yscale(self.yscale)

        # define the ranges
        self.setRange = SetGraphRange(parent=self,
            x_range=self.ax.get_xlim(), y_range=self.ax.get_ylim())

        # refresh canvas
        self.canvas.draw()

    def createContextMenu(self):
        """
        Define common context menu and associated actions for the MPL widget
        """
        self.defaultContextMenu()

        # Separate plots
        self.addPlotsToContextMenu()

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
        #if self.parent:
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

    def addPlotsToContextMenu(self):
        """
        Adds operations on all plotted sets of data to the context menu
        """
        for id in self.plot_dict.keys():
            plot = self.plot_dict[id]
            name = plot.name
            plot_menu = self.contextMenu.addMenu('&%s' % name)

            self.actionDataInfo = plot_menu.addAction("&DataInfo")
            self.actionDataInfo.triggered.connect(
                                functools.partial(self.onDataInfo, plot))

            self.actionSavePointsAsFile = plot_menu.addAction("&Save Points as a File")
            self.actionSavePointsAsFile.triggered.connect(
                                functools.partial(self.onSavePoints, plot))
            plot_menu.addSeparator()

            if plot.id != 'fit':
                self.actionLinearFit = plot_menu.addAction('&Linear Fit')
                self.actionLinearFit.triggered.connect(
                                functools.partial(self.onLinearFit, id))
                plot_menu.addSeparator()

            self.actionRemovePlot = plot_menu.addAction("Remove")
            self.actionRemovePlot.triggered.connect(
                                functools.partial(self.onRemovePlot, id))

            if not plot.is_data:
                self.actionFreeze = plot_menu.addAction('&Freeze')
                self.actionFreeze.triggered.connect(
                                functools.partial(self.onFreeze, id))
            plot_menu.addSeparator()

            if plot.is_data:
                self.actionHideError = plot_menu.addAction("Hide Error Bar")
                if plot.dy is not None and plot.dy != []:
                    if plot.hide_error:
                        self.actionHideError.setText('Show Error Bar')
                else:
                    self.actionHideError.setEnabled(False)
                self.actionHideError.triggered.connect(
                                functools.partial(self.onToggleHideError, id))
                plot_menu.addSeparator()

            self.actionModifyPlot = plot_menu.addAction('&Modify Plot Property')
            self.actionModifyPlot.triggered.connect(self.onModifyPlot)

    def createContextMenuQuick(self):
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
            self.xLogLabel, self.yLogLabel = self.properties.getValues()
            self.xyTransform(self.xLogLabel, self.yLogLabel)

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

    def onDataInfo(self, plot_data):
        """
        Displays data info text window for the selected plot
        """
        text_to_show = GuiUtils.retrieveData1d(plot_data)
        # Hardcoded sizes to enable full width rendering with default font
        self.txt_widget.resize(420,600)

        self.txt_widget.setReadOnly(True)
        self.txt_widget.setWindowFlags(QtCore.Qt.Window)
        self.txt_widget.setWindowIcon(QtGui.QIcon(":/res/ball.ico"))
        self.txt_widget.setWindowTitle("Data Info: %s" % plot_data.filename)
        self.txt_widget.insertPlainText(text_to_show)

        self.txt_widget.show()
        # Move the slider all the way up, if present
        vertical_scroll_bar = self.txt_widget.verticalScrollBar()
        vertical_scroll_bar.triggerAction(QtGui.QScrollBar.SliderToMinimum)

    def onSavePoints(self, plot_data):
        """
        Saves plot data to a file
        """
        GuiUtils.saveData1D(plot_data)

    def onLinearFit(self, id):
        """
        Creates and displays a simple linear fit for the selected plot
        """
        selected_plot = self.plot_dict[id]

        maxrange = (min(selected_plot.x), max(selected_plot.x))
        fitrange = self.ax.get_xlim()

        fit_dialog = LinearFit(parent=self,
                    data=selected_plot,
                    max_range=maxrange,
                    fit_range=fitrange,
                    xlabel=self.xLogLabel,
                    ylabel=self.yLogLabel)
        if fit_dialog.exec_() == QtGui.QDialog.Accepted:
            return

    def onRemovePlot(self, id):
        """
        Responds to the plot delete action
        """
        self.removePlot(id)

        if len(self.plot_dict) == 0:
            # last plot: graph is empty must be the panel must be destroyed
                self.parent.close()

    def removePlot(self, id):
        """
        Deletes the selected plot from the chart
        """
        if id not in self.plot_dict:
            return

        selected_plot = self.plot_dict[id]

        plot_dict = copy.deepcopy(self.plot_dict)

        self.plot_dict = {}

        plt.cla()
        self.ax.cla()

        for ids in plot_dict:
            if ids != id:
                self.plot(data=plot_dict[ids], hide_error=plot_dict[ids].hide_error)                

    def onFreeze(self, id):
        """
        Freezes the selected plot to a separate chart
        """
        plot = self.plot_dict[id]
        self.manager.add_data(data_list=[plot])

    def onModifyPlot(self):
        """
        Allows for MPL modifications to the selected plot
        """
        pass

    def onToggleHideError(self, id):
        """
        Toggles hide error/show error menu item
        """
        selected_plot = self.plot_dict[id]
        current = selected_plot.hide_error

        # Flip the flag
        selected_plot.hide_error = not current

        plot_dict = copy.deepcopy(self.plot_dict)
        self.plot_dict = {}

        # Clean the canvas
        plt.cla()
        self.ax.cla()

        # Recreate the plots but reverse the error flag for the current
        for ids in plot_dict:
            if ids == id:
                self.plot(data=plot_dict[ids], hide_error=(not current))
            else:
                self.plot(data=plot_dict[ids], hide_error=plot_dict[ids].hide_error)                

    def xyTransform(self, xLabel="", yLabel=""):
        """
        Transforms x and y in View and set the scale
        """
        # Transform all the plots on the chart
        for id in self.plot_dict.keys():
            current_plot = self.plot_dict[id]
            if current_plot.id == "fit":
                self.removePlot(id)
                continue
            new_xlabel, new_ylabel, xscale, yscale =\
                GuiUtils.xyTransform(current_plot, xLabel, yLabel)
            self.xscale = xscale
            self.yscale = yscale
            self.xLabel = new_xlabel
            self.yLabel = new_ylabel
            # Plot the updated chart
            self.removePlot(id)
            self.plot(data=current_plot, marker='o', linestyle='')

        pass # debug hook

    def onFitDisplay(self, fit_data):
        """
        Add a linear fitting line to the chart
        """
        # Create new data structure with fitting result
        tempx = fit_data[0]
        tempy = fit_data[1]
        self.fit_result.x = []
        self.fit_result.y = []
        self.fit_result.x = tempx
        self.fit_result.y = tempy
        self.fit_result.dx = None
        self.fit_result.dy = None

        #Remove another Fit, if exists
        self.removePlot("fit")

        self.fit_result.reset_view()
        #self.offset_graph()

        # Set plot properties
        self.fit_result.id = 'fit'
        self.fit_result.title = 'Fit'
        self.fit_result.name = 'Fit'

        # Plot the line
        self.plot(data=self.fit_result, marker='', linestyle='solid', hide_error=True)


class Plotter(QtGui.QDialog, PlotterWidget):
    def __init__(self, parent=None, quickplot=False):

        QtGui.QDialog.__init__(self)
        PlotterWidget.__init__(self, parent=self, manager=parent, quickplot=quickplot)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/res/ball.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(icon)


