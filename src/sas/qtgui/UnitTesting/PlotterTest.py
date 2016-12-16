import sys
import unittest

from PyQt4 import QtGui
from PyQt4 import QtCore
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from mock import MagicMock

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
        self.data.id = 1

    def tearDown(self):
        '''destroy'''
        self.plotter = None

    def testDataProperty(self):
        """ Adding data """
        self.plotter.data = self.data

        self.assertEqual(self.plotter.data, self.data)
        self.assertEqual(self.plotter._title, self.data.title)
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
        self.plotter.data = self.data

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
        pass

    def testOnRemoveText(self):
        """ Cheks if annotations can be removed from the graph """
        pass


if __name__ == "__main__":
    unittest.main()
