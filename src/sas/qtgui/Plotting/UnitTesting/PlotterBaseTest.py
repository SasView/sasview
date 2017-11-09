import sys
import unittest
import platform
from unittest.mock import MagicMock

from PyQt5 import QtGui, QtWidgets, QtPrintSupport
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

####### TEMP
import path_prepare
#######

from sas.qtgui.Plotting.ScaleProperties import ScaleProperties
from sas.qtgui.Plotting.WindowTitle import WindowTitle
from sas.qtgui.Utilities.GuiUtils import *
import sas.qtgui.Plotting.PlotHelper as PlotHelper

# Tested module
import sas.qtgui.Plotting.PlotterBase as PlotterBase

if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)

class PlotterBaseTest(unittest.TestCase):
    '''Test the Plotter base class'''
    def setUp(self):
        '''create'''
        class dummy_manager(object):
            def communicator(self):
                return Communicate()
            def perspective(self):
                return MyPerspective()

        #PlotterBase.PlotterBase.contextMenuQuickPlot = MagicMock()
        self.plotter = PlotterBase.PlotterBase(None, manager=dummy_manager(), quickplot=True)
        self.isWindows = platform.system=="Windows"

    def tearDown(self):
        '''destroy'''
        self.plotter = None
        self.plotter_qp = None

    def testDefaults(self):
        """ default method variables values """
        self.assertIsInstance(self.plotter, QtWidgets.QWidget)
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
        with self.assertRaises(NotImplementedError):
            self.plotter.createContextMenu()

    def testClean(self):
        ''' test the graph cleanup '''
        self.plotter.figure.delaxes = MagicMock()
        self.plotter.clean()
        self.assertTrue(self.plotter.figure.delaxes.called)

    def testPlot(self):
        ''' test the pure virtual method '''
        with self.assertRaises(NotImplementedError):
            self.plotter.plot()

    def notestOnCloseEvent(self):
        ''' test the plotter close behaviour '''
        PlotHelper.deletePlot = MagicMock()
        self.plotter.closeEvent(None)
        self.assertTrue(PlotHelper.deletePlot.called)

    def testOnImageSave(self):
        ''' test the workspace save '''
        self.plotter.toolbar.save_figure = MagicMock()
        self.plotter.onImageSave()
        self.assertTrue(self.plotter.toolbar.save_figure.called)

    def testOnImagePrint(self):
        ''' test the workspace print '''
        QtGui.QPainter.end = MagicMock()
        QtWidgets.QLabel.render = MagicMock()

        # First, let's cancel printing
        QtPrintSupport.QPrintDialog.exec_ = MagicMock(return_value=QtWidgets.QDialog.Rejected)
        self.plotter.onImagePrint()
        self.assertFalse(QtGui.QPainter.end.called)
        self.assertFalse(QtWidgets.QLabel.render.called)

        # Let's print now
        QtPrintSupport.QPrintDialog.exec_ = MagicMock(return_value=QtWidgets.QDialog.Accepted)
        self.plotter.onImagePrint()
        self.assertTrue(QtGui.QPainter.end.called)
        self.assertTrue(QtWidgets.QLabel.render.called)

    def testOnClipboardCopy(self):
        ''' test the workspace screen copy '''
        QtGui.QClipboard.setPixmap = MagicMock()
        self.plotter.onClipboardCopy()
        self.assertTrue(QtGui.QClipboard.setPixmap.called)

    def testOnGridToggle(self):
        ''' test toggling the grid lines '''
        # Check the toggle
        orig_toggle = self.plotter.grid_on
        
        FigureCanvas.draw_idle = MagicMock()
        self.plotter.onGridToggle()

        self.assertTrue(FigureCanvas.draw_idle.called)
        self.assertTrue(self.plotter.grid_on != orig_toggle)

    def testDefaultContextMenu(self):
        """ Test the right click default menu """

        self.plotter.defaultContextMenu()

        actions = self.plotter.contextMenu.actions()
        self.assertEqual(len(actions), 4)

        # Trigger Save Image and make sure the method is called
        self.assertEqual(actions[0].text(), "Save Image")
        self.plotter.toolbar.save_figure = MagicMock()
        actions[0].trigger()
        self.assertTrue(self.plotter.toolbar.save_figure.called)

        # Trigger Print Image and make sure the method is called
        self.assertEqual(actions[1].text(), "Print Image")
        QtPrintSupport.QPrintDialog.exec_ = MagicMock(return_value=QtWidgets.QDialog.Rejected)
        actions[1].trigger()
        self.assertTrue(QtPrintSupport.QPrintDialog.exec_.called)

        # Trigger Copy to Clipboard and make sure the method is called
        self.assertEqual(actions[2].text(), "Copy to Clipboard")

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

    def testOnWindowsTitle(self):
        """ Test changing the plot title"""
        # Mock the modal dialog's response
        QtWidgets.QDialog.exec_ = MagicMock(return_value=QtWidgets.QDialog.Accepted)
        self.plotter.show()
        # Assure the original title is none
        self.assertEqual(self.plotter.windowTitle(), "")
        self.plotter.manager.communicator = MagicMock()

        WindowTitle.title = MagicMock(return_value="I am a new title")
        # Change the title
        self.plotter.onWindowsTitle()

        self.assertEqual(self.plotter.windowTitle(), "I am a new title")

    def testOnMplMouseDown(self):
        """ Test what happens on mouse click down in chart """
        pass

    def testOnMplMouseUp(self):
        """ Test what happens on mouse release in chart """
        pass

    def testOnMplMouseMotion(self):
        """ Test what happens on mouse move in chart """
        pass

    def testOnMplPick(self):
        """ Test what happens on mouse pick in chart """
        pass

    def testOnMplWheel(self):
        """ Test what happens on mouse pick in chart """
        pass

if __name__ == "__main__":
    unittest.main()
