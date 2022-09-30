import sys
import unittest
import numpy
import platform

import pytest

import os
os.environ["MPLBACKEND"] = "qtagg"

from PyQt5 import QtGui, QtWidgets, QtPrintSupport
from PyQt5 import QtCore
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from unittest.mock import MagicMock
from mpl_toolkits.mplot3d import Axes3D

####### TEMP
import sas.qtgui.path_prepare
#######
from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Plotting.PlotterData import Data2D
from sas.qtgui.UnitTesting.TestUtils import WarningTestNotImplemented

# Tested module
import sas.qtgui.Plotting.Plotter2D as Plotter2D

if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)

class Plotter2DTest(unittest.TestCase):
    '''Test the Plotter 2D class'''
    def setUp(self):
        '''create'''
        class dummy_manager(object):
            def communicator(self):
                return Communicate()
            def perspective(self):
                return MyPerspective()
            def workspace(self):
                return None

        self.plotter = Plotter2D.Plotter2D(parent=dummy_manager(), quickplot=True)

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
        self.data.ndim = 1
        self.isWindows = platform.system=="Windows"

    def tearDown(self):
        '''destroy'''
        self.plotter.figure.clf()
        self.plotter = None

    @pytest.mark.skip(reason="2022-09 already broken - causes segfault")
    def testDataProperty(self):
        """ Adding data """
        self.plotter.data = self.data

        assert self.plotter.data0 == self.data
        assert self.plotter._title == self.data.title
        assert self.plotter.xLabel == "$\\rm{Q_{x}}(A^{-1})$"
        assert self.plotter.yLabel == "$\\rm{Q_{y}}(A^{-1})$"

    @pytest.mark.xfail(reason="2022-09 already broken")
    def testPlot(self):
        """ Look at the plotting """
        self.plotter.data = self.data
        self.plotter.show()
        FigureCanvas.draw_idle = MagicMock()

        self.plotter.plot()

        assert FigureCanvas.draw_idle.called
        self.plotter.figure.clf()

    @pytest.mark.skip(reason="2022-09 already broken - causes segfault")
    def testCalculateDepth(self):
        ''' Test the depth calculator '''
        self.plotter.data = self.data

        # Default, log scale
        depth = self.plotter.calculateDepth()
        assert depth == (0.1, 1.e20)

        # Change the scale to linear
        self.plotter.scale = 'linear'
        depth = self.plotter.calculateDepth()
        assert depth[0] == -32.
        assert round(abs(depth[1]-1.30103), 5) == 0

    @pytest.mark.skip(reason="2022-09 already broken - causes segfault")
    def testOnColorMap(self):
        ''' Respond to the color map event '''
        self.plotter.data = self.data
        self.plotter.plot()
        self.plotter.show()

        QtWidgets.QDialog.exec_ = MagicMock(return_value=QtWidgets.QDialog.Accepted)

        # Just this one plot
        self.plotter.onColorMap()

        # Check that exec_ got called
        assert QtWidgets.QDialog.exec_.called

        assert self.plotter.cmap == "jet"
        assert round(abs(self.plotter.vmin-0.1), 6) == 0
        assert round(abs(self.plotter.vmax-1e+20), 6) == 0
        self.plotter.figure.clf()

    @pytest.mark.skip(reason="2022-09 already broken - causes segfault")
    def testOnToggleScale(self):
        """ Respond to the event by replotting """
        self.plotter.data = self.data
        self.plotter.show()
        FigureCanvas.draw_idle = MagicMock()

        self.plotter.onToggleScale(None)

        assert FigureCanvas.draw_idle.called
        self.plotter.figure.clf()

    @pytest.mark.skip(reason="2022-09 already broken - causes segfault")
    def testOnBoxSum(self):
        """ Test the box sum display and functionality """

        # hacky way to make things work in manipulations._sum
        self.data.detector = [1]
        self.data.err_data = numpy.array([0.0, 0.0, 0.1, 0.0])
        self.plotter.data = self.data
        self.plotter.show()

        # Mock the main window
        self.plotter.manager.parent = MagicMock()

        # Call the main tested method
        self.plotter.onBoxSum()

        # Test various properties
        assert isinstance(self.plotter.slicer.model(), QtGui.QStandardItemModel)
        assert self.plotter.boxwidget.isVisible()
        assert isinstance(self.plotter.boxwidget.model, QtGui.QStandardItemModel)
        self.plotter.figure.clf()

    @pytest.mark.skip(reason="2022-09 already broken")
    def testContextMenuQuickPlot(self):
        """ Test the right click menu """
        self.plotter.data = self.data
        self.plotter.createContextMenuQuick()
        actions = self.plotter.contextMenu.actions()
        assert len(actions) == 7

        # Trigger Print Image and make sure the method is called
        assert actions[1].text() == "Print Image"
        QtPrintSupport.QPrintDialog.exec_ = MagicMock(return_value=QtWidgets.QDialog.Rejected)
        actions[1].trigger()
        assert QtPrintSupport.QPrintDialog.exec_.called

        # Trigger Copy to Clipboard and make sure the method is called
        assert actions[2].text() == "Copy to Clipboard"

        # Trigger Toggle Grid and make sure the method is called
        assert actions[4].text() == "Toggle Grid On/Off"
        self.plotter.ax.grid = MagicMock()
        actions[4].trigger()
        assert self.plotter.ax.grid.called

        # Trigger Change Scale and make sure the method is called
        assert actions[6].text() == "Toggle Linear/Log Scale"
        FigureCanvas.draw_idle = MagicMock()
        actions[6].trigger()
        assert FigureCanvas.draw_idle.called

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
        self.plotter.figure.clf()

    @pytest.mark.skip(reason="2022-09 already broken - causes segfault")
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

        assert not FigureCanvas.draw_idle.called
        assert not FigureCanvas.draw.called
        self.plotter.figure.clf()

    @pytest.mark.skip(reason="2022-09 already broken - causes segfault")
    def testShow3DPlot(self):
        """ Test the 3Dplot rendering and generation """
        # Test 3D printout
        FigureCanvas.draw = MagicMock()
        Axes3D.plot_surface = MagicMock()
        self.plotter.figure.colorbar = MagicMock()

        self.plotter.dimension = 3
        self.plotter.data = self.data
        self.plotter.showPlot(data=self.plotter.data0.data,
                              qx_data=self.data.qx_data,
                              qy_data=self.data.qy_data,
                              xmin=self.data.xmin,
                              xmax=self.data.xmax,
                              ymin=self.data.ymin, ymax=self.data.ymax,
                              cmap=None, zmin=None,
                              zmax=None)
        assert Axes3D.plot_surface.called
        assert FigureCanvas.draw.called
        self.plotter.figure.clf()

    @pytest.mark.skip(reason="2022-09 already broken - causes segfault")
    def testShow2DPlot(self):
        """ Test the 2Dplot rendering and generation """
        # Test 2D printout
        FigureCanvas.draw_idle = MagicMock()
        self.plotter.figure.colorbar = MagicMock()

        self.plotter.dimension = 2
        self.plotter.data = self.data
        self.plotter.showPlot(data=self.data.data,
                              qx_data=self.data.qx_data,
                              qy_data=self.data.qy_data,
                              xmin=self.data.xmin,
                              xmax=self.data.xmax,
                              ymin=self.data.ymin, ymax=self.data.ymax,
                              cmap=None, zmin=None,
                              zmax=None)
        assert FigureCanvas.draw_idle.called
        self.plotter.figure.clf()


if __name__ == "__main__":
    unittest.main()
