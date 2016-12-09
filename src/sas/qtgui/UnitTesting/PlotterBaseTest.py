import sys
import unittest
from mock import MagicMock

from PyQt4 import QtGui
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar

####### TEMP
import path_prepare
#######

from sas.qtgui.ScaleProperties import ScaleProperties
#import sas.qtgui.GuiUtils as GuiUtils
from sas.qtgui.GuiUtils import *

# Tested module
import sas.qtgui.PlotterBase as PlotterBase

app = QtGui.QApplication(sys.argv)

class PlotterBaseTest(unittest.TestCase):
    '''Test the Plotter base class'''
    def setUp(self):
        '''create'''
        class dummy_manager(object):
            def communicator(self):
                return Communicate()
            def perspective(self):
                return MyPerspective()

        #PlotterBase.PlotterBase.updatePlotHelper = MagicMock()
        #self.plotter = PlotterBase.PlotterBase(None, manager=dummy_manager())

        PlotterBase.PlotterBase.contextMenuQuickPlot = MagicMock()
        self.plotter = PlotterBase.PlotterBase(None, manager=dummy_manager(), quickplot=True)

    def tearDown(self):
        '''destroy'''
        self.plotter = None
        self.plotter_qp = None

    def testDefaults(self):
        """ default method variables values """
        self.assertIsInstance(self.plotter, QtGui.QWidget)
        self.assertIsInstance(self.plotter.canvas, FigureCanvas)
        self.assertIsInstance(self.plotter.toolbar, NavigationToolbar)
        self.assertIsInstance(self.plotter.properties, ScaleProperties)

        self.assertEqual(self.plotter._data, [])
        self.assertEqual(self.plotter._xscale, 'log')
        self.assertEqual(self.plotter._yscale, 'log')
        self.assertEqual(self.plotter.scale, 'linear')
        self.assertFalse(self.plotter.grid_on)
        self.assertEqual(self.plotter.x_label, 'log10(x)')
        self.assertEqual(self.plotter.y_label, 'log10(y)')

    def testData(self):
        ''' Test the pure virtual method '''
        with self.assertRaises(NotImplementedError):
            self.plotter.data=[]

    def testContextMenu(self):
        ''' Test the default context menu '''
        pass

    def testContextMenuQuickPlot(self):
        ''' Test the default quick context menu '''
        pass

    def testClean(self):
        ''' test the graph cleanup '''
        pass

    def testPlot(self):
        ''' test the pure virtual method '''
        with self.assertRaises(NotImplementedError):
            self.plotter.plot()

    def testOnCloseEvent(self):
        ''' test the plotter close behaviour '''
        pass

    def testOnImageSave(self):
        ''' test the workspace save '''
        pass

    def testOnImagePrint(self):
        ''' test the workspace print '''
        pass

    def tesOonClipboardCopy(self):
        ''' test the workspace copy '''
        pass

    def testOnGridToggle(self):
        ''' test toggling the grid lines '''
        pass


if __name__ == "__main__":
    unittest.main()
