import sys
import unittest
import platform

from PyQt5 import QtGui, QtWidgets, QtPrintSupport
from PyQt5 import QtCore
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from unittest.mock import MagicMock
from unittest.mock import patch

####### TEMP
import path_prepare
#######
from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Plotting.PlotterData import Data2D
from sas.qtgui.UnitTesting.TestUtils import WarningTestNotImplemented
from sas.qtgui.Plotting.LinearFit import LinearFit
from sas.qtgui.Plotting.PlotProperties import PlotProperties

# Tested module
import sas.qtgui.Plotting.Plotter as Plotter

if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)


class PlotterTest(unittest.TestCase):
    '''Test the Plotter 1D class'''
    def setUp(self):
        '''create'''

        self.plotter = Plotter.Plotter(None, quickplot=True)
        self.data = Data1D(x=[1.0, 2.0, 3.0],
                           y=[10.0, 11.0, 12.0],
                           dx=[0.1, 0.2, 0.3],
                           dy=[0.1, 0.2, 0.3])
        self.data.title="Test data"
        self.data.name="Test name"
        self.data.id = 1
        self.isWindows = platform.system=="Windows"

    def tearDown(self):
        '''destroy'''
        self.plotter = None

    def testDataProperty(self):
        """ Adding data """
        self.plotter.data = self.data

        self.assertEqual(self.plotter.data[0], self.data)
        self.assertEqual(self.plotter._title, self.data.name)
        self.assertEqual(self.plotter.xLabel, "")
        self.assertEqual(self.plotter.yLabel, "")

    def testPlotWithErrors(self):
        """ Look at the plotting with error bars"""
        self.plotter.data = self.data
        self.plotter.show()
        FigureCanvas.draw_idle = MagicMock()

        self.plotter.plot(hide_error=False)

        self.assertEqual(self.plotter.ax.get_xscale(), 'linear')
        self.assertTrue(FigureCanvas.draw_idle.called)

        self.plotter.figure.clf()

    def testPlotWithoutErrors(self):
        """ Look at the plotting without error bars"""
        self.plotter.data = self.data
        self.plotter.show()
        FigureCanvas.draw_idle = MagicMock()

        self.plotter.plot(hide_error=True)

        self.assertEqual(self.plotter.ax.get_yscale(), 'linear')
        self.assertTrue(FigureCanvas.draw_idle.called)
        self.plotter.figure.clf()

    def testPlotWithSesans(self):
        """ Ensure that Sesans data is plotted in linear cooredinates"""
        data = Data1D(x=[1.0, 2.0, 3.0],
                      y=[-10.0, -11.0, -12.0],
                      dx=[0.1, 0.2, 0.3],
                      dy=[0.1, 0.2, 0.3])
        data.title = "Sesans data"
        data.name = "Test Sesans"
        data.isSesans = True
        data.id = 2

        self.plotter.data = data
        self.plotter.show()
        FigureCanvas.draw_idle = MagicMock()

        self.plotter.plot(hide_error=True)

        self.assertEqual(self.plotter.ax.get_xscale(), 'linear')
        self.assertEqual(self.plotter.ax.get_yscale(), 'linear')
        #self.assertEqual(self.plotter.data[0].ytransform, "y")
        self.assertTrue(FigureCanvas.draw_idle.called)

    def testCreateContextMenuQuick(self):
        """ Test the right click menu """
        self.plotter.createContextMenuQuick()
        actions = self.plotter.contextMenu.actions()
        self.assertEqual(len(actions), 8)

        # Trigger Print Image and make sure the method is called
        self.assertEqual(actions[1].text(), "Print Image")
        QtPrintSupport.QPrintDialog.exec_ = MagicMock(return_value=QtWidgets.QDialog.Rejected)
        actions[1].trigger()
        self.assertTrue(QtPrintSupport.QPrintDialog.exec_.called)

        # Trigger Copy to Clipboard and make sure the method is called
        self.assertEqual(actions[2].text(), "Copy to Clipboard")

        # Trigger Toggle Grid and make sure the method is called
        self.assertEqual(actions[4].text(), "Toggle Grid On/Off")
        self.plotter.ax.grid = MagicMock()
        actions[4].trigger()
        self.assertTrue(self.plotter.ax.grid.called)

        # Trigger Change Scale and make sure the method is called
        self.assertEqual(actions[6].text(), "Change Scale")
        self.plotter.properties.exec_ = MagicMock(return_value=QtWidgets.QDialog.Rejected)
        actions[6].trigger()
        self.assertTrue(self.plotter.properties.exec_.called)

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
        self.assertTrue(self.clipboard_called)

    def testXyTransform(self):
        """ Tests the XY transformation and new chart update """
        self.plotter.plot(self.data)

        # Transform the points
        self.plotter.xyTransform(xLabel="x", yLabel="log10(y)")

        # Assure new plot has correct labels
        self.assertEqual(self.plotter.ax.get_xlabel(), "$()$")
        self.assertEqual(self.plotter.ax.get_ylabel(), "$()$")
        # ... and scale
        self.assertEqual(self.plotter.xscale, "linear")
        self.assertEqual(self.plotter.yscale, "log")
        # See that just one plot is present
        self.assertEqual(len(self.plotter.plot_dict), 1)
        self.assertEqual(len(self.plotter.ax.collections), 1)
        self.plotter.figure.clf()

    def testUnitChange(self):
        """ Test the various unit change methods """
        x_unit_default = 'A^{-1}'
        y_unit_default = 'cm^{-1}'
        x_unit_new = 'nm^{-1}'
        y_unit_new = 'm^{-1}'
        self.data.x_unit = x_unit_default
        self.data.y_unit = y_unit_default
        x0 = self.data.x[0]
        y0 = self.data.y[0]
        assert self.data.x_converter is not None
        assert self.data.y_converter is not None
        # Ensure units are compatible
        self.assertTrue(x_unit_new in self.data.x_converter.get_compatible_units())
        self.assertTrue(y_unit_new in self.data.y_converter.get_compatible_units())
        # Plot base data set with default units
        self.plotter.plot(self.data)
        # Change units of plot and check values changed
        self.plotter.setUnits(x_unit_new, y_unit_new)
        self.assertTrue(x_unit_new in str(self.plotter.ax.xaxis.label))
        self.assertTrue(y_unit_new in str(self.plotter.ax.yaxis.label))
        for id, plot in self.plotter.plot_dict.items():
            self.assertNotEqual(x0, plot.x[0])
            self.assertNotEqual(y0, plot.y[0])
        # Change units of plot back to original values and ensure x and y values restored
        self.plotter.setUnits(x_unit_default, y_unit_default)
        self.assertTrue(x_unit_default in str(self.plotter.ax.xaxis.label))
        self.assertTrue(y_unit_default in str(self.plotter.ax.yaxis.label))
        for id, plot in self.plotter.plot_dict.items():
            self.assertEqual(x0, plot.x[0])
            self.assertEqual(y0, plot.y[0])

    def testAddText(self):
        """ Checks the functionality of adding text to graph """

        self.plotter.plot(self.data)
        self.plotter.x_click = 100.0
        self.plotter.y_click = 100.0
        # modify the text edit control
        test_text = "Smoke in cabin"
        test_font = QtGui.QFont("Arial", 16, QtGui.QFont.Bold)
        test_color = "#00FF00"
        self.plotter.addText.textEdit.setText(test_text)

        # Return the requested font parameters
        self.plotter.addText.font = MagicMock(return_value = test_font)
        self.plotter.addText.color = MagicMock(return_value = test_color)
        # Return OK from the dialog
        self.plotter.addText.exec_ = MagicMock(return_value = QtWidgets.QDialog.Accepted)
        # Add text to graph
        self.plotter.onAddText()
        self.plotter.show()
        # Check if the text was added properly
        self.assertEqual(len(self.plotter.textList), 1)
        self.assertEqual(self.plotter.textList[0].get_text(), test_text)
        self.assertEqual(self.plotter.textList[0].get_color(), test_color)
        self.assertEqual(self.plotter.textList[0].get_fontproperties().get_family()[0], 'Arial')
        self.assertEqual(self.plotter.textList[0].get_fontproperties().get_size(), 16)
        self.plotter.figure.clf()

    def testOnRemoveText(self):
        """ Cheks if annotations can be removed from the graph """

        # Add some text
        self.plotter.plot(self.data)
        test_text = "Safety instructions"
        self.plotter.addText.textEdit.setText(test_text)
        # Return OK from the dialog
        self.plotter.addText.exec_ = MagicMock(return_value = QtWidgets.QDialog.Accepted)
        # Add text to graph
        self.plotter.x_click = 1.0
        self.plotter.y_click = 5.0
        self.plotter.onAddText()
        self.plotter.show()
        # Check if the text was added properly
        self.assertEqual(len(self.plotter.textList), 1)

        # Now, remove the text
        self.plotter.onRemoveText()

        # And assure no text is displayed
        self.assertEqual(self.plotter.textList, [])

        # Attempt removal on empty and check
        self.plotter.onRemoveText()
        self.assertEqual(self.plotter.textList, [])
        self.plotter.figure.clf()

    def testOnSetGraphRange(self):
        """ Cheks if the graph can be resized for range """
        new_x = (1,2)
        new_y = (10,11)
        self.plotter.plot(self.data)
        self.plotter.show()
        self.plotter.setRange.exec_ = MagicMock(return_value = QtWidgets.QDialog.Accepted)
        self.plotter.setRange.xrange = MagicMock(return_value = new_x)
        self.plotter.setRange.yrange = MagicMock(return_value = new_y)

        # Call the tested method
        self.plotter.onSetGraphRange()
        # See that ranges changed accordingly
        self.assertEqual(self.plotter.ax.get_xlim(), new_x)
        self.assertEqual(self.plotter.ax.get_ylim(), new_y)
        self.plotter.figure.clf()

    def testOnResetGraphRange(self):
        """ Cheks if the graph can be reset after resizing for range """
        # New values
        new_x = (1,2)
        new_y = (10,11)
        # define the plot
        self.plotter.plot(self.data)
        self.plotter.show()

        # mock setRange methods
        self.plotter.setRange.exec_ = MagicMock(return_value = QtWidgets.QDialog.Accepted)
        self.plotter.setRange.xrange = MagicMock(return_value = new_x)
        self.plotter.setRange.yrange = MagicMock(return_value = new_y)

        # Change the axes range
        self.plotter.onSetGraphRange()

        # Now, reset the range back
        self.plotter.onResetGraphRange()

        # See that ranges are changed
        self.assertNotEqual(self.plotter.ax.get_xlim(), new_x)
        self.assertNotEqual(self.plotter.ax.get_ylim(), new_y)
        self.plotter.figure.clf()

    def testOnLinearFit(self):
        """ Checks the response to LinearFit call """
        self.plotter.plot(self.data)
        self.plotter.show()
        QtWidgets.QDialog.exec_ = MagicMock(return_value=QtWidgets.QDialog.Accepted)

        # Just this one plot
        self.assertEqual(len(list(self.plotter.plot_dict.keys())), 1)
        self.plotter.onLinearFit('Test name')

        # Check that exec_ got called
        self.assertTrue(QtWidgets.QDialog.exec_.called)
        self.plotter.figure.clf()

    def testOnRemovePlot(self):
        """ Assure plots get removed when requested """
        # Add two plots
        self.plotter.show()
        self.plotter.plot(self.data)
        data2 = Data1D(x=[1.0, 2.0, 3.0],
                       y=[11.0, 12.0, 13.0],
                       dx=[0.1, 0.2, 0.3],
                       dy=[0.1, 0.2, 0.3])
        data2.title="Test data 2"
        data2.name="Test name 2"
        data2.id = 2
        self.plotter.plot(data2)

        # Assure the plotter window is visible
        #self.assertTrue(self.plotter.isVisible())

        # Assure we have two sets
        self.assertEqual(len(list(self.plotter.plot_dict.keys())), 2)

        # Delete one set
        self.plotter.onRemovePlot('Test name 2')
        # Assure we have two sets
        self.assertEqual(len(list(self.plotter.plot_dict.keys())), 1)

        self.plotter.manager = MagicMock()

        # Delete the remaining set
        self.plotter.onRemovePlot('Test name')
        # Assure we have no plots
        self.assertEqual(len(list(self.plotter.plot_dict.keys())), 0)
        # Assure the plotter window is closed
        self.assertFalse(self.plotter.isVisible())
        self.plotter.figure.clf()

    def testRemovePlot(self):
        """ Test plot removal """
        # Add two plots
        self.plotter.show()
        self.plotter.plot(self.data)
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
        self.plotter.plot(data2)

        # delete plot 1
        self.plotter.removePlot(1)

        # See that the labels didn't change
        xl = self.plotter.ax.xaxis.label.get_text()
        yl = self.plotter.ax.yaxis.label.get_text()
        self.assertEqual(xl, "$XAXIS(furlong*fortnight^{-1})$")
        self.assertEqual(yl, "$YAXIS(cake)$")
        # The hide_error flag should also remain
        self.assertTrue(self.plotter.plot_dict['Test name 2'].hide_error)
        self.plotter.figure.clf()

    def testOnToggleHideError(self):
        """ Test the error bar toggle on plots """
        # Add two plots
        self.plotter.show()
        self.plotter.plot(self.data)
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
        self.plotter.plot(data2)

        # Reverse the toggle
        self.plotter.onToggleHideError('Test name 2')
        # See that the labels didn't change
        xl = self.plotter.ax.xaxis.label.get_text()
        yl = self.plotter.ax.yaxis.label.get_text()
        self.assertEqual(xl, "$XAXIS(furlong*fortnight^{-1})$")
        self.assertEqual(yl, "$YAXIS(cake)$")
        # The hide_error flag should toggle
        self.assertEqual(self.plotter.plot_dict['Test name 2'].hide_error, not error_status)
        self.plotter.figure.clf()

    def testOnFitDisplay(self):
        """ Test the fit line display on the chart """
        self.assertIsInstance(self.plotter.fit_result, Data1D)
        self.assertEqual(self.plotter.fit_result.symbol, 13)
        self.assertEqual(self.plotter.fit_result.name, "Fit")

        # fudge some init data
        fit_data = [[0.0,0.0], [5.0,5.0]]
        # Call the method
        self.plotter.plot = MagicMock()
        self.plotter.onFitDisplay(fit_data)
        self.assertTrue(self.plotter.plot.called)
        # Look at arguments passed to .plot()
        self.plotter.plot.assert_called_with(data=self.plotter.fit_result,
                                             hide_error=True, marker='-')
        self.plotter.figure.clf()

    def testReplacePlot(self):
        """ Test the plot refresh functionality """
        # Add original data
        self.plotter.show()
        self.plotter.plot(self.data)
        # See the default labels
        xl = self.plotter.ax.xaxis.label.get_text()
        yl = self.plotter.ax.yaxis.label.get_text()
        self.assertEqual(xl, "$()$")
        self.assertEqual(yl, "$()$")

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
        self.plotter.replacePlot("Test name", data2)

        # See that the labels changed
        xl = self.plotter.ax.xaxis.label.get_text()
        yl = self.plotter.ax.yaxis.label.get_text()
        self.assertEqual(xl, "$XAXIS(furlong*fortnight^{-1})$")
        self.assertEqual(yl, "$YAXIS(cake)$")
        # The hide_error flag should be as set
        self.assertEqual(self.plotter.plot_dict['Test name 2'].hide_error, error_status)
        self.plotter.figure.clf()

    def notestOnModifyPlot(self):
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

        self.plotter.plot(data2)

        with patch('sas.qtgui.Plotting.PlotProperties.PlotProperties') as mock:
            instance = mock.return_value
            QtWidgets.QDialog.exec_ = MagicMock(return_value=QtWidgets.QDialog.Accepted)
            instance.symbol.return_value = 7

            self.plotter.onModifyPlot(2)
        self.plotter.figure.clf()

    def testOnToggleLegend(self):
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

        self.plotter.plot(data2)

        self.assertTrue(self.plotter.showLegend)
        # assure we see the legend
        self.assertTrue(self.plotter.legend.get_visible())

        # toggle legend
        self.plotter.onToggleLegend()

        # now we don't see the legend
        self.assertFalse(self.plotter.legend.get_visible())

        # toggle again
        self.plotter.onToggleLegend()

        # see the legend again
        self.assertTrue(self.plotter.legend.get_visible())

        # switch the visibility of the legend
        self.plotter.showLegend = False

        # see that the legend setting is not done
        self.plotter.legend.set_visible = MagicMock()

        self.plotter.onToggleLegend()
        self.plotter.legend.set_visible.assert_not_called()

if __name__ == "__main__":
    unittest.main()
