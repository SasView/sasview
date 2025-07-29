import platform
from unittest.mock import patch

import matplotlib as mpl
import pytest

mpl.use("Qt5Agg")

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PySide6 import QtCore, QtGui, QtPrintSupport, QtWidgets

# Tested module
import sas.qtgui.Plotting.Plotter as Plotter
from sas.qtgui.Plotting.PlotterData import Data1D


class PlotterTest:
    '''Test the Plotter 1D class'''
    @pytest.fixture(autouse=True)
    def plotter(self, qapp):
        '''Create/Destroy the Plotter1D'''

        p = Plotter.Plotter(None, quickplot=True)
        self.data = Data1D(x=[1.0, 2.0, 3.0],
                           y=[10.0, 11.0, 12.0],
                           dx=[0.1, 0.2, 0.3],
                           dy=[0.1, 0.2, 0.3])
        self.data.title="Test data"
        self.data.name="Test name"
        self.data.id = 1
        self.isWindows = platform.system=="Windows"

        yield p

    def testDataProperty(self, plotter):
        """ Adding data """
        plotter.data = self.data

        assert plotter.data[0] == self.data
        assert plotter._title == self.data.name
        assert plotter.xLabel == ""
        assert plotter.yLabel == ""

    def testPlotWithErrors(self, plotter, mocker):
        """ Look at the plotting with error bars"""
        plotter.data = self.data
        plotter.show()
        mocker.patch.object(FigureCanvas, 'draw_idle')

        plotter.plot(hide_error=False)

        assert plotter.ax.get_xscale() == 'linear'
        assert FigureCanvas.draw_idle.called

        plotter.figure.clf()

    def testPlotWithoutErrors(self, plotter, mocker):
        """ Look at the plotting without error bars"""
        plotter.data = self.data
        plotter.show()
        mocker.patch.object(FigureCanvas, 'draw_idle')

        plotter.plot(hide_error=True)

        assert plotter.ax.get_yscale() == 'linear'
        assert FigureCanvas.draw_idle.called
        plotter.figure.clf()

    def testPlotWithSesans(self, plotter, mocker):
        """ Ensure that Sesans data is plotted in linear cooredinates"""
        data = Data1D(x=[1.0, 2.0, 3.0],
                      y=[-10.0, -11.0, -12.0],
                      dx=[0.1, 0.2, 0.3],
                      dy=[0.1, 0.2, 0.3])
        data.title = "Sesans data"
        data.name = "Test Sesans"
        data.isSesans = True
        data.id = 2

        plotter.data = data
        plotter.show()
        mocker.patch.object(FigureCanvas, 'draw_idle')

        plotter.plot(hide_error=True)

        assert plotter.ax.get_xscale() == 'linear'
        assert plotter.ax.get_yscale() == 'linear'
        #assert plotter.data[0].ytransform == "y"
        assert FigureCanvas.draw_idle.called

    def testCreateContextMenuQuick(self, plotter, mocker):
        """ Test the right click menu """
        plotter.createContextMenuQuick()
        actions = plotter.contextMenu.actions()
        assert len(actions) == 8

        # Trigger Print Image and make sure the method is called
        assert actions[1].text() == "Print Image"
        mocker.patch.object(QtPrintSupport.QPrintDialog, 'exec_', return_value=QtWidgets.QDialog.Rejected)
        actions[1].trigger()
        assert QtPrintSupport.QPrintDialog.exec_.called

        # Trigger Copy to Clipboard and make sure the method is called
        assert actions[2].text() == "Copy to Clipboard"

        # Trigger Toggle Grid and make sure the method is called
        assert actions[4].text() == "Toggle Grid On/Off"
        mocker.patch.object(plotter.ax, 'grid')
        actions[4].trigger()
        assert plotter.ax.grid.called

        # Trigger Change Scale and make sure the method is called
        assert actions[6].text() == "Change Scale"
        mocker.patch.object(plotter.properties, 'exec_', return_value=QtWidgets.QDialog.Rejected)
        actions[6].trigger()
        assert plotter.properties.exec_.called

        # Spy on cliboard's dataChanged() signal
        if not self.isWindows:
            return
        self.clipboard_called = False
        def done():
            self.clipboard_called = True
        QtCore.QObject.connect(QtWidgets.qApp.clipboard(), QtCore.SIGNAL("dataChanged()"), done)
        actions[2].trigger()
        QtWidgets.qApp.processEvents()
        # Make sure clipboard got updated.
        assert self.clipboard_called

    def testXyTransform(self, plotter):
        """ Tests the XY transformation and new chart update """
        plotter.plot(self.data)

        # Transform the points
        plotter.xyTransform(xLabel="x", yLabel="log10(y)")

        # Assure new plot has correct labels
        assert plotter.ax.get_xlabel() == "$()$"
        assert plotter.ax.get_ylabel() == "$()$"
        # ... and scale
        assert plotter.xscale == "linear"
        assert plotter.yscale == "log"
        # See that just one plot is present
        assert len(plotter.plot_dict) == 1
        assert len(plotter.ax.collections) == 1
        plotter.figure.clf()

    def testAddText(self, plotter, mocker):
        """ Checks the functionality of adding text to graph """

        plotter.plot(self.data)
        plotter.x_click = 100.0
        plotter.y_click = 100.0
        # modify the text edit control
        test_text = "Smoke in cabin"
        test_font = QtGui.QFont("Arial", 16, QtGui.QFont.Bold)
        test_color = "#00FF00"
        plotter.addText.codeEditor.setText(test_text)

        # Return the requested font parameters
        mocker.patch.object(plotter.addText, 'font', return_value=test_font)
        mocker.patch.object(plotter.addText, 'color', return_value=test_color)
        # Return OK from the dialog
        mocker.patch.object(plotter.addText, 'exec_', return_value=QtWidgets.QDialog.Accepted)
        # Add text to graph
        plotter.onAddText()
        plotter.show()
        # Check if the text was added properly
        assert len(plotter.textList) == 1
        assert plotter.textList[0].get_text() == test_text
        assert plotter.textList[0].get_color() == test_color
        assert plotter.textList[0].get_fontproperties().get_family()[0] == 'Arial'
        assert plotter.textList[0].get_fontproperties().get_size() == 16
        plotter.figure.clf()

    def testOnRemoveText(self, plotter, mocker):
        """ Cheks if annotations can be removed from the graph """

        # Add some text
        plotter.plot(self.data)
        test_text = "Safety instructions"
        plotter.addText.codeEditor.setText(test_text)
        # Return OK from the dialog
        mocker.patch.object(plotter.addText, 'exec_', return_value=QtWidgets.QDialog.Accepted)
        # Add text to graph
        plotter.x_click = 1.0
        plotter.y_click = 5.0
        plotter.onAddText()
        plotter.show()
        # Check if the text was added properly
        assert len(plotter.textList) == 1

        # Now, remove the text
        plotter.onRemoveText()

        # And assure no text is displayed
        assert plotter.textList == []

        # Attempt removal on empty and check
        plotter.onRemoveText()
        assert plotter.textList == []
        plotter.figure.clf()

    def testOnSetGraphRange(self, plotter, mocker):
        """ Cheks if the graph can be resized for range """
        new_x = (1,2)
        new_y = (10,11)
        plotter.plot(self.data)
        plotter.show()
        mocker.patch.object(plotter.setRange, 'exec_', return_value=QtWidgets.QDialog.Accepted)
        mocker.patch.object(plotter.setRange, 'xrange', return_value=new_x)
        mocker.patch.object(plotter.setRange, 'yrange', return_value=new_y)

        # Call the tested method
        plotter.onSetGraphRange()
        # See that ranges changed accordingly
        assert plotter.ax.get_xlim() == new_x
        assert plotter.ax.get_ylim() == new_y
        plotter.figure.clf()

    def testOnResetGraphRange(self, plotter, mocker):
        """ Cheks if the graph can be reset after resizing for range """
        # New values
        new_x = (1,2)
        new_y = (10,11)
        # define the plot
        plotter.plot(self.data)
        plotter.show()

        # mock setRange methods
        mocker.patch.object(plotter.setRange, 'exec_', returnvalue=QtWidgets.QDialog.Accepted)
        mocker.patch.object(plotter.setRange, 'xrange', returnvalue=new_x)
        mocker.patch.object(plotter.setRange, 'yrange', returnvalue=new_y)

        # Change the axes range
        plotter.onSetGraphRange()

        # Now, reset the range back
        plotter.onResetGraphRange()

        # See that ranges are changed
        assert plotter.ax.get_xlim() != new_x
        assert plotter.ax.get_ylim() != new_y
        plotter.figure.clf()

    def testOnLinearFit(self, plotter, mocker):
        """ Checks the response to LinearFit call """
        plotter.plot(self.data)
        plotter.show()
        mocker.patch.object(QtWidgets.QDialog, 'exec_', return_value=QtWidgets.QDialog.Accepted)

        # Just this one plot
        assert len(list(plotter.plot_dict.keys())) == 1
        plotter.onLinearFit('Test name')

        # Check that exec_ got called
        assert QtWidgets.QDialog.exec_.called
        plotter.figure.clf()

    def testOnRemovePlot(self, plotter, mocker):
        """ Assure plots get removed when requested """
        # Add two plots
        plotter.show()
        plotter.plot(self.data)
        data2 = Data1D(x=[1.0, 2.0, 3.0],
                       y=[11.0, 12.0, 13.0],
                       dx=[0.1, 0.2, 0.3],
                       dy=[0.1, 0.2, 0.3])
        data2.title="Test data 2"
        data2.name="Test name 2"
        data2.id = 2
        plotter.plot(data2)

        # Assure the plotter window is visible
        #assert plotter.isVisible()

        # Assure we have two sets
        assert len(list(plotter.plot_dict.keys())) == 2

        # Delete one set
        plotter.onRemovePlot('Test name 2')
        # Assure we have two sets
        assert len(list(plotter.plot_dict.keys())) == 1

        mocker.patch.object(plotter, 'manager')

        # Delete the remaining set
        plotter.onRemovePlot('Test name')
        # Assure we have no plots
        assert len(list(plotter.plot_dict.keys())) == 0
        # Assure the plotter window is closed
        assert not plotter.isVisible()
        plotter.figure.clf()

    def testRemovePlot(self, plotter):
        """ Test plot removal """
        # Add two plots
        plotter.show()
        plotter.plot(self.data)
        data2 = Data1D(x=[1.0, 2.0, 3.0],
                       y=[11.0, 12.0, 13.0],
                       dx=[0.1, 0.2, 0.3],
                       dy=[0.1, 0.2, 0.3])
        data2.title="Test data 2"
        data2.name="Test name 2"
        data2.id = 2
        data2._xaxis = "XAXIS"
        data2._xunit = "furlong*fortnight^{-1}"
        data2._yaxis = "YAXIS"
        data2._yunit = "cake"
        data2.hide_error = True
        plotter.plot(data2)

        # delete plot 1
        plotter.removePlot(1)

        # See that the labels didn't change
        xl = plotter.ax.xaxis.label.get_text()
        yl = plotter.ax.yaxis.label.get_text()
        assert xl == "$XAXIS(furlong*fortnight^{-1})$"
        assert yl == "$YAXIS(cake)$"
        # The hide_error flag should also remain
        assert plotter.plot_dict['Test name 2'].hide_error
        plotter.figure.clf()

    def testOnToggleHideError(self, plotter):
        """ Test the error bar toggle on plots """
        # Add two plots
        plotter.show()
        plotter.plot(self.data)
        data2 = Data1D(x=[1.0, 2.0, 3.0],
                       y=[11.0, 12.0, 13.0],
                       dx=[0.1, 0.2, 0.3],
                       dy=[0.1, 0.2, 0.3])
        data2.title="Test data 2"
        data2.name="Test name 2"
        data2.id = 2
        data2._xaxis = "XAXIS"
        data2._xunit = "furlong*fortnight^{-1}"
        data2._yaxis = "YAXIS"
        data2._yunit = "cake"
        error_status = True
        data2.hide_error = error_status
        plotter.plot(data2)

        # Reverse the toggle
        plotter.onToggleHideError('Test name 2')
        # See that the labels didn't change
        xl = plotter.ax.xaxis.label.get_text()
        yl = plotter.ax.yaxis.label.get_text()
        assert xl == "$XAXIS(furlong*fortnight^{-1})$"
        assert yl == "$YAXIS(cake)$"
        # The hide_error flag should toggle
        assert plotter.plot_dict['Test name 2'].hide_error == (not error_status)
        plotter.figure.clf()

    def testOnFitDisplay(self, plotter, mocker):
        """ Test the fit line display on the chart """
        assert isinstance(plotter.fit_result, Data1D)
        assert plotter.fit_result.symbol == 17
        assert plotter.fit_result.name == "Fit"

        # fudge some init data
        fit_data = [[0.0,0.0], [5.0,5.0]]
        # Call the method
        mocker.patch.object(plotter, 'plot')
        plotter.onFitDisplay(fit_data)
        assert plotter.plot.called
        # Look at arguments passed to .plot()
        plotter.plot.assert_called_with(data=plotter.fit_result,
                                             hide_error=True, marker='-')
        plotter.figure.clf()

    def testReplacePlot(self, plotter):
        """ Test the plot refresh functionality """
        # Add original data
        plotter.show()
        plotter.plot(self.data)
        # See the default labels
        xl = plotter.ax.xaxis.label.get_text()
        yl = plotter.ax.yaxis.label.get_text()
        assert xl == "$()$"
        assert yl == "$()$"

        # Prepare new data
        data2 = Data1D(x=[1.0, 2.0, 3.0],
                       y=[11.0, 12.0, 13.0],
                       dx=[0.1, 0.2, 0.3],
                       dy=[0.1, 0.2, 0.3])
        data2.title="Test data 2"
        data2.name="Test name 2"
        data2.id = 2
        data2._xaxis = "XAXIS"
        data2._xunit = "furlong*fortnight^{-1}"
        data2._yaxis = "YAXIS"
        data2._yunit = "cake"
        error_status = True
        data2.hide_error = error_status
        data2.custom_color = None
        data2.symbol = 1
        data2.markersize = 11

        # Replace data in plot
        plotter.replacePlot("Test name", data2)

        # See that the labels changed
        xl = plotter.ax.xaxis.label.get_text()
        yl = plotter.ax.yaxis.label.get_text()
        assert xl == "$XAXIS(furlong*fortnight^{-1})$"
        assert yl == "$YAXIS(cake)$"
        # The hide_error flag should be as set
        assert plotter.plot_dict['Test name 2'].hide_error == error_status
        plotter.figure.clf()

    def notestOnModifyPlot(self, plotter, mocker):
        """ Test the functionality for changing plot properties """
        # Prepare new data
        data2 = Data1D(x=[1.0, 2.0, 3.0],
                       y=[11.0, 12.0, 13.0],
                       dx=[0.1, 0.2, 0.3],
                       dy=[0.1, 0.2, 0.3])
        data2.title="Test data 2"
        data2.name="Test name 2"
        data2.id = 2
        data2.custom_color = None
        data2.symbol = 1
        data2.markersize = 11

        plotter.plot(data2)

        with patch('sas.qtgui.Plotting.PlotProperties.PlotProperties') as mock:
            instance = mock.return_value
            mocker.patch.object(QtWidgets.QDialog, 'exec_', return_value=QtWidgets.QDialog.Accepted)
            instance.symbol.returnvalue=7

            plotter.onModifyPlot(2)
        plotter.figure.clf()

    def testOnToggleLegend(self, plotter, mocker):
        """
        Make sure Legend can be switched on/off
        """
        # Prepare new data
        data2 = Data1D(x=[1.0, 2.0, 3.0],
                       y=[11.0, 12.0, 13.0],
                       dx=[0.1, 0.2, 0.3],
                       dy=[0.1, 0.2, 0.3])
        data2.title="Test data 2"
        data2.name="Test name 2"
        data2.id = 2
        data2.custom_color = None
        data2.symbol = 1
        data2.markersize = 11

        plotter.plot(data2)

        assert plotter.showLegend
        # assure we see the legend
        assert plotter.legend.get_visible()

        # toggle legend
        plotter.onToggleLegend()

        # now we don't see the legend
        assert not plotter.legend.get_visible()

        # toggle again
        plotter.onToggleLegend()

        # see the legend again
        assert plotter.legend.get_visible()

        # switch the visibility of the legend
        plotter.showLegend = False

        # see that the legend setting is not done
        mocker.patch.object(plotter.legend, 'set_visible')

        plotter.onToggleLegend()
        plotter.legend.set_visible.assert_not_called()
