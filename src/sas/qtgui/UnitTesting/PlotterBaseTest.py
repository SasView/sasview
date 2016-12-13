import sys
import unittest
from mock import patch, MagicMock

from PyQt4 import QtGui
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar

####### TEMP
import path_prepare
#######

from sas.qtgui.ScaleProperties import ScaleProperties
from sas.qtgui.WindowTitle import WindowTitle
#import sas.qtgui.GuiUtils as GuiUtils
from sas.qtgui.GuiUtils import *
import sas.qtgui.PlotHelper as PlotHelper

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
        with self.assertRaises(NotImplementedError):
            self.plotter.contextMenu()

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
        QtGui.QLabel.render = MagicMock()

        # First, let's cancel printing
        QtGui.QPrintDialog.exec_ = MagicMock(return_value=QtGui.QDialog.Rejected)
        self.plotter.onImagePrint()
        self.assertFalse(QtGui.QPainter.end.called)
        self.assertFalse(QtGui.QLabel.render.called)

        # Let's print now
        QtGui.QPrintDialog.exec_ = MagicMock(return_value=QtGui.QDialog.Accepted)
        self.plotter.onImagePrint()
        self.assertTrue(QtGui.QPainter.end.called)
        self.assertTrue(QtGui.QLabel.render.called)

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
        self.assertTrue(self.clipboard_called)

    def testOnWindowsTitle(self):
        ''' test changing the plot title'''
        # Mock the modal dialog's response
        QtGui.QDialog.exec_ = MagicMock(return_value=QtGui.QDialog.Accepted)
        self.plotter.show()
        # Assure the original title is none
        self.assertEqual(self.plotter.windowTitle(), "")
        self.plotter.manager.communicator = MagicMock()

        WindowTitle.title = MagicMock(return_value="I am a new title")
        # Change the title
        self.plotter.onWindowsTitle()

        self.assertEqual(self.plotter.windowTitle(), "I am a new title")

if __name__ == "__main__":
    unittest.main()
