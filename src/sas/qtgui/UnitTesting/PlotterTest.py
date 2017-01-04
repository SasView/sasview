import sys
import unittest

from PyQt4 import QtGui
from PyQt4 import QtCore
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from mock import MagicMock
from mock import patch

####### TEMP
import path_prepare
#######
from sas.sasgui.guiframe.dataFitting import Data1D
from sas.sasgui.guiframe.dataFitting import Data2D
from UnitTesting.TestUtils import QtSignalSpy

# Tested module
import sas.qtgui.Plotter as Plotter

app = QtGui.QApplication(sys.argv)

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

    def tearDown(self):
        '''destroy'''
        self.plotter = None

    def testDataProperty(self):
        """ Adding data """
        self.plotter.data = self.data

        self.assertEqual(self.plotter.data, self.data)
        self.assertEqual(self.plotter._title, self.data.name)
        self.assertEqual(self.plotter.xLabel, "$()$")
        self.assertEqual(self.plotter.yLabel, "$()$")

    def testPlotWithErrors(self):
        """ Look at the plotting with error bars"""
        self.plotter.data = self.data
        self.plotter.show()
        FigureCanvas.draw = MagicMock()

        self.plotter.plot(hide_error=False)

        self.assertEqual(self.plotter.ax.get_xscale(), 'log')
        self.assertTrue(FigureCanvas.draw.called)

    def testPlotWithoutErrors(self):
        """ Look at the plotting without error bars"""
        self.plotter.data = self.data
        self.plotter.show()
        FigureCanvas.draw = MagicMock()

        self.plotter.plot(hide_error=True)

        self.assertEqual(self.plotter.ax.get_yscale(), 'log')
        self.assertTrue(FigureCanvas.draw.called)

    def testContextMenuQuickPlot(self):
        """ Test the right click menu """
        self.plotter.createContextMenuQuick()
        actions = self.plotter.contextMenu.actions()
        self.assertEqual(len(actions), 7)

        # Trigger Save Image and make sure the method is called
        self.assertEqual(actions[0].text(), "Save Image")
        self.plotter.toolbar.save_figure = MagicMock()
        actions[0].trigger()
        self.assertTrue(self.plotter.toolbar.save_figure.called)

        # Trigger Print Image and make sure the method is called
        self.assertEqual(actions[1].text(), "Print Image")
        QtGui.QPrintDialog.exec_ = MagicMock(return_value=QtGui.QDialog.Rejected)
        actions[1].trigger()
        self.assertTrue(QtGui.QPrintDialog.exec_.called)

        # Trigger Copy to Clipboard and make sure the method is called
        self.assertEqual(actions[2].text(), "Copy to Clipboard")

        # Spy on cliboard's dataChanged() signal
        self.clipboard_called = False
        def done():
            self.clipboard_called = True
        QtCore.QObject.connect(app.clipboard(), QtCore.SIGNAL("dataChanged()"), done)
        actions[2].trigger()
        QtGui.qApp.processEvents()
        # Make sure clipboard got updated.
        #self.assertTrue(self.clipboard_called)

        # Trigger Toggle Grid and make sure the method is called
        self.assertEqual(actions[4].text(), "Toggle Grid On/Off")
        self.plotter.ax.grid = MagicMock()
        actions[4].trigger()
        self.assertTrue(self.plotter.ax.grid.called)

        # Trigger Change Scale and make sure the method is called
        self.assertEqual(actions[6].text(), "Change Scale")
        self.plotter.properties.exec_ = MagicMock(return_value=QtGui.QDialog.Rejected)
        actions[6].trigger()
        self.assertTrue(self.plotter.properties.exec_.called)

    def testXYTransform(self):
        """ Assure the unit/legend transformation is correct"""
        self.plotter.plot(self.data)

        self.plotter.xyTransform(xLabel="x", yLabel="y")
        self.assertEqual(self.plotter.ax.get_xlabel(), "$()$")
        self.assertEqual(self.plotter.ax.get_ylabel(), "$()$")

        self.plotter.xyTransform(xLabel="x^(2)", yLabel="1/y")
        self.assertEqual(self.plotter.ax.get_xlabel(), "$^{2}(()^{2})$")
        self.assertEqual(self.plotter.ax.get_ylabel(), "$1/(()^{-1})$")

        self.plotter.xyTransform(xLabel="x^(4)", yLabel="ln(y)")
        self.assertEqual(self.plotter.ax.get_xlabel(), "$^{4}(()^{4})$")
        self.assertEqual(self.plotter.ax.get_ylabel(), "$\\ln{()}()$")

        self.plotter.xyTransform(xLabel="ln(x)", yLabel="y^(2)")
        self.assertEqual(self.plotter.ax.get_xlabel(), "$\\ln{()}()$")
        self.assertEqual(self.plotter.ax.get_ylabel(), "$^{2}(()^{2})$")

        self.plotter.xyTransform(xLabel="log10(x)", yLabel="y*x^(2)")
        self.assertEqual(self.plotter.ax.get_xlabel(), "$()$")
        self.assertEqual(self.plotter.ax.get_ylabel(), "$ \\ \\ ^{2}(()^{2})$")

        self.plotter.xyTransform(xLabel="log10(x^(4))", yLabel="y*x^(4)")
        self.assertEqual(self.plotter.ax.get_xlabel(), "$^{4}(()^{4})$")
        self.assertEqual(self.plotter.ax.get_ylabel(), "$ \\ \\ ^{4}(()^{16})$")

        self.plotter.xyTransform(xLabel="x", yLabel="1/sqrt(y)")
        self.assertEqual(self.plotter.ax.get_ylabel(), "$1/\\sqrt{}(()^{-0.5})$")

        self.plotter.xyTransform(xLabel="x", yLabel="log10(y)")
        self.assertEqual(self.plotter.ax.get_ylabel(), "$()$")

        self.plotter.xyTransform(xLabel="x", yLabel="ln(y*x)")
        self.assertEqual(self.plotter.ax.get_ylabel(), "$\\ln{( \\ \\ )}()$")

        self.plotter.xyTransform(xLabel="x", yLabel="ln(y*x^(2))")
        self.assertEqual(self.plotter.ax.get_ylabel(), "$\\ln ( \\ \\ ^{2})(()^{2})$")

        self.plotter.xyTransform(xLabel="x", yLabel="ln(y*x^(4))")
        self.assertEqual(self.plotter.ax.get_ylabel(), "$\\ln ( \\ \\ ^{4})(()^{4})$")

        self.plotter.xyTransform(xLabel="x", yLabel="log10(y*x^(4))")
        self.assertEqual(self.plotter.ax.get_ylabel(), "$ \\ \\ ^{4}(()^{4})$")

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
        self.plotter.addText.exec_ = MagicMock(return_value = QtGui.QDialog.Accepted)
        # Add text to graph
        self.plotter.onAddText()
        self.plotter.show()
        # Check if the text was added properly
        self.assertEqual(len(self.plotter.textList), 1)
        self.assertEqual(self.plotter.textList[0].get_text(), test_text)
        self.assertEqual(self.plotter.textList[0].get_color(), test_color)
        self.assertEqual(self.plotter.textList[0].get_fontproperties().get_family()[0], 'Arial')
        self.assertEqual(self.plotter.textList[0].get_fontproperties().get_size(), 16)

    def testOnRemoveText(self):
        """ Cheks if annotations can be removed from the graph """

        # Add some text
        self.plotter.plot(self.data)
        test_text = "Safety instructions"
        self.plotter.addText.textEdit.setText(test_text)
        # Return OK from the dialog
        self.plotter.addText.exec_ = MagicMock(return_value = QtGui.QDialog.Accepted)
        # Add text to graph
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

    def testOnSetGraphRange(self):
        """ Cheks if the graph can be resized for range """
        new_x = (1,2)
        new_y = (10,11)
        self.plotter.plot(self.data)
        self.plotter.show()
        self.plotter.setRange.exec_ = MagicMock(return_value = QtGui.QDialog.Accepted)
        self.plotter.setRange.xrange = MagicMock(return_value = new_x)
        self.plotter.setRange.yrange = MagicMock(return_value = new_y)

        # Call the tested method
        self.plotter.onSetGraphRange()
        # See that ranges changed accordingly
        self.assertEqual(self.plotter.ax.get_xlim(), new_x)
        self.assertEqual(self.plotter.ax.get_ylim(), new_y)

    def testOnResetGraphRange(self):
        """ Cheks if the graph can be reset after resizing for range """
        # New values
        new_x = (1,2)
        new_y = (10,11)
        # define the plot
        self.plotter.plot(self.data)
        self.plotter.show()

        # mock setRange methods
        self.plotter.setRange.exec_ = MagicMock(return_value = QtGui.QDialog.Accepted)
        self.plotter.setRange.xrange = MagicMock(return_value = new_x)
        self.plotter.setRange.yrange = MagicMock(return_value = new_y)

        # Change the axes range
        self.plotter.onSetGraphRange()

        # Now, reset the range back
        self.plotter.onResetGraphRange()

        # See that ranges are changed
        self.assertNotEqual(self.plotter.ax.get_xlim(), new_x)
        self.assertNotEqual(self.plotter.ax.get_ylim(), new_y)

if __name__ == "__main__":
    unittest.main()
