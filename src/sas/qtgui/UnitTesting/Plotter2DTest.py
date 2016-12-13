import sys
import unittest

from PyQt4 import QtGui
from PyQt4 import QtCore
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from mock import MagicMock
from mpl_toolkits.mplot3d import Axes3D

####### TEMP
import path_prepare
#######
from sas.sasgui.guiframe.dataFitting import Data1D
from sas.sasgui.guiframe.dataFitting import Data2D

# Tested module
import sas.qtgui.Plotter2D as Plotter2D

app = QtGui.QApplication(sys.argv)

class Plotter2DTest(unittest.TestCase):
    '''Test the Plotter 2D class'''
    def setUp(self):
        '''create'''
        self.plotter = Plotter2D.Plotter2D(None, quickplot=True)

        self.data = Data2D(image=[0.1]*4,
                           qx_data=[1.0, 2.0, 3.0, 4.0],
                           qy_data=[10.0, 11.0, 12.0, 13.0],
                           dqx_data=[0.1, 0.2, 0.3, 0.4],
                           dqy_data=[0.1, 0.2, 0.3, 0.4],
                           q_data=[1,2,3,4],
                           xmin=-1.0, xmax=5.0,
                           ymin=-1.0, ymax=15.0,
                           zmin=-1.0, zmax=20.0)

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
        self.assertEqual(self.plotter.xLabel, "$\\rm{Q_{x}}(A^{-1})$")
        self.assertEqual(self.plotter.yLabel, "$\\rm{Q_{y}}(A^{-1})$")

    def testPlot(self):
        """ Look at the plotting """
        self.plotter.data = self.data
        self.plotter.show()
        FigureCanvas.draw_idle = MagicMock()

        self.plotter.plot()

        self.assertTrue(FigureCanvas.draw_idle.called)

    def testOnToggleScale(self):
        """ Respond to the event by replotting """
        self.plotter.data = self.data
        self.plotter.show()
        FigureCanvas.draw_idle = MagicMock()

        self.plotter.onToggleScale(None)

        self.assertTrue(FigureCanvas.draw_idle.called)

    def testContextMenuQuickPlot(self):
        """ Test the right click menu """
        self.plotter.data = self.data
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
        self.assertEqual(actions[6].text(), "Toggle Linear/Log Scale")
        FigureCanvas.draw_idle = MagicMock()
        actions[6].trigger()
        self.assertTrue(FigureCanvas.draw_idle.called)

    def testShowNoPlot(self):
        """ Test the plot rendering and generation """

        FigureCanvas.draw_idle = MagicMock()
        FigureCanvas.draw = MagicMock()

        # Test early return on no data
        self.plotter.showPlot(data=None,
                              qx_data=self.data.qx_data,
                              qy_data=self.data.qy_data,
                              xmin=self.data.xmin,
                              xmax=self.data.xmax,
                              ymin=self.data.ymin, ymax=self.data.ymax,
                              cmap=None, zmin=None,
                              zmax=None)

        self.assertFalse(FigureCanvas.draw_idle.called)
        self.assertFalse(FigureCanvas.draw.called)

    def testShow3DPlot(self):
        """ Test the 3Dplot rendering and generation """
        # Test 3D printout
        FigureCanvas.draw = MagicMock()
        Axes3D.plot_surface = MagicMock()
        self.plotter.figure.colorbar = MagicMock()

        self.plotter.dimension = 3
        self.plotter.data = self.data
        self.plotter.showPlot(data=self.plotter.data.data,
                              qx_data=self.data.qx_data,
                              qy_data=self.data.qy_data,
                              xmin=self.data.xmin,
                              xmax=self.data.xmax,
                              ymin=self.data.ymin, ymax=self.data.ymax,
                              cmap=None, zmin=None,
                              zmax=None)
        self.assertTrue(Axes3D.plot_surface.called)
        self.assertTrue(FigureCanvas.draw.called)

    def testShow2DPlot(self):
        """ Test the 2Dplot rendering and generation """
        # Test 2D printout
        FigureCanvas.draw_idle = MagicMock()
        self.plotter.figure.colorbar = MagicMock()

        self.plotter.dimension = 2
        self.plotter.data = self.data
        self.plotter.showPlot(data=self.plotter.data.data,
                              qx_data=self.data.qx_data,
                              qy_data=self.data.qy_data,
                              xmin=self.data.xmin,
                              xmax=self.data.xmax,
                              ymin=self.data.ymin, ymax=self.data.ymax,
                              cmap=None, zmin=None,
                              zmax=None)
        self.assertTrue(FigureCanvas.draw_idle.called)


if __name__ == "__main__":
    unittest.main()
