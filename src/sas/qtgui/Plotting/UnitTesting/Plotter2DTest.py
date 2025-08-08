import platform

import matplotlib as mpl
import numpy
import pytest

mpl.use("Qt5Agg")

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from mpl_toolkits.mplot3d import Axes3D
from PySide6 import QtCore, QtGui, QtPrintSupport, QtWidgets

# Tested module
import sas.qtgui.Plotting.Plotter2D as Plotter2D
from sas.qtgui.MainWindow.UnitTesting.DataExplorerTest import MyPerspective
from sas.qtgui.Plotting.PlotterData import Data2D
from sas.qtgui.Utilities.GuiUtils import Communicate


class Plotter2DTest:
    '''Test the Plotter 2D class'''
    @pytest.fixture(autouse=True)
    def plotter(self, qapp):
        '''Create/Destroy the Plotter2D'''

        class dummy_manager:
            def communicator(self):
                return Communicate()
            def perspective(self):
                return MyPerspective()
            def workspace(self):
                return None

        p = Plotter2D.Plotter2D(parent=dummy_manager(), quickplot=True)

        data = Data2D(image=[[0.1]*4]*4,
                      qx_data=[[1.0, 2.0, 3.0, 4.0]]*4,
                      qy_data=[[10.0, 11.0, 12.0, 13.0]]*4,
                      dqx_data=[[0.1, 0.2, 0.3, 0.4]]*4,
                      dqy_data=[[0.1, 0.2, 0.3, 0.4]]*4,
                      q_data=[[1, 2, 3, 4]]*4,
                      xmin=1.0, xmax=5.0,
                      ymin=1.0, ymax=15.0,
                      zmin=1.0, zmax=20.0,
                      )

        data.title = "Test data"
        data.id = 1
        data.ndim = 2

        p.data = data

        yield p

        '''destroy'''
        p.figure.clf()

    def testDataProperty(self, plotter):
        """ Adding data """
        assert plotter._title == "Test data"
        assert plotter.xLabel == "$\\rm{Q_{x}}(A^{-1})$"
        assert plotter.yLabel == "$\\rm{Q_{y}}(A^{-1})$"

    def testPlot(self, plotter, mocker):
        """ Look at the plotting """
        mocker.patch.object(plotter, 'plot')
        plotter.plot()
        assert plotter.plot.called_once()

    @pytest.mark.skip(reason="2022-09 already broken")
    def testCalculateDepth(self, plotter):
        ''' Test the depth calculator '''
        plotter.data = self.data

        # Default, log scale
        depth = plotter.calculateDepth()
        assert depth == (0.1, 1.e20)

        # Change the scale to linear
        plotter.scale = 'linear'
        depth = plotter.calculateDepth()
        assert depth[0] == -32.
        assert depth[1] == pytest.approx(1.30103, abs=1e-5)

    @pytest.mark.skip(reason="2022-09 already broken - causes segfault")
    def testOnColorMap(self, plotter, mocker):
        ''' Respond to the color map event '''
        plotter.data = self.data
        plotter.plot()
        plotter.show()

        mocker.patch.object(QtWidgets.QDialog, 'exec_', return_value=QtWidgets.QDialog.Accepted)

        # Just this one plot
        plotter.onColorMap()

        # Check that exec_ got called
        assert QtWidgets.QDialog.exec_.called

        assert plotter.cmap == "jet"
        assert plotter.vmin == pytest.approx(0.1, abs=1e-6)
        assert plotter.vmax == pytest.approx(1e+20, abs=1e-6)

    @pytest.mark.skip(reason="2022-09 already broken - causes segfault")
    def testOnToggleScale(self, plotter, mocker):
        """ Respond to the event by replotting """
        plotter.data = self.data
        plotter.show()
        mocker.patch.object(FigureCanvas, 'draw_idle')

        plotter.onToggleScale(None)

        assert FigureCanvas.draw_idle.called

    def testOnToggleMaskedPoints(self, plotter, mocker):
        """ Respond to the masked data event by replotting """
        assert not plotter._show_masked_data
        plotter.data = Data2D(image=[[0.1]*4]*4,
                              qx_data=[[1.0, 2.0, 3.0, 4.0]]*4,
                              qy_data=[[10.0, 11.0, 12.0, 13.0]]*4,
                              dqx_data=[[0.1, 0.2, 0.3, 0.4]]*4,
                              dqy_data=[[0.1, 0.2, 0.3, 0.4]]*4,
                              q_data=[[1, 2, 3, 4]]*4,
                              mask=[[1, 1, 1, 0]]*4,
                              xmin=-1.0, xmax=5.0,
                              ymin=-1.0, ymax=15.0,
                              zmin=-1.0, zmax=20.0,
                              )
        assert len(plotter._masked_data[0].data) == 4*3

        mocker.patch.object(plotter, 'plot')
        plotter.onToggleMaskedData(None)
        assert plotter._show_masked_data
        assert plotter.plot.called_once()

    @pytest.mark.skip(reason="2022-09 already broken - causes segfault")
    def testOnBoxSum(self, plotter, mocker):
        """ Test the box sum display and functionality """

        # hacky way to make things work in manipulations._sum
        self.data.detector = [1]
        self.data.err_data = numpy.array([0.0, 0.0, 0.1, 0.0])
        plotter.data = self.data
        plotter.show()

        # Mock the main window
        mocker.patch.object(plotter.manager, 'parent', create=True)

        # Call the main tested method
        plotter.onBoxSum()

        # Test various properties
        assert isinstance(plotter.slicer.model(), QtGui.QStandardItemModel)
        assert plotter.boxwidget.isVisible()
        assert isinstance(plotter.boxwidget.model, QtGui.QStandardItemModel)

    @pytest.mark.skip(reason="2022-09 already broken")
    def testContextMenuQuickPlot(self, plotter, mocker):
        """ Test the right click menu """
        plotter.data = self.data
        plotter.createContextMenuQuick()
        actions = plotter.contextMenu.actions()
        assert len(actions) == 7

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
        assert actions[6].text() == "Toggle Linear/Log Scale"
        mocker.patch.object(FigureCanvas, 'draw_idle')
        actions[6].trigger()
        assert FigureCanvas.draw_idle.called

        # Spy on cliboard's dataChanged() signal
        if not platform.system == "Windows":
            return
        self.clipboard_called = False
        def done():
            self.clipboard_called = True
        QtCore.QObject.connect(QtWidgets.qApp.clipboard(), QtCore.SIGNAL("dataChanged()"), done)
        actions[2].trigger()
        QtWidgets.qApp.processEvents()
        # Make sure clipboard got updated.
        assert self.clipboard_called

    @pytest.mark.skip(reason="2022-09 already broken - causes segfault")
    def testShowNoPlot(self, plotter, mocker):
        """ Test the plot rendering and generation """

        mocker.patch.object(FigureCanvas, 'draw_idle')
        mocker.patch.object(FigureCanvas, 'draw')

        # Test early return on no data
        plotter.showPlot(data=None,
                              qx_data=self.data.qx_data,
                              qy_data=self.data.qy_data,
                              xmin=self.data.xmin,
                              xmax=self.data.xmax,
                              ymin=self.data.ymin, ymax=self.data.ymax,
                              cmap=None, zmin=None,
                              zmax=None)

        assert not FigureCanvas.draw_idle.called
        assert not FigureCanvas.draw.called

    @pytest.mark.skip(reason="2022-09 already broken - causes segfault")
    def testShow3DPlot(self, plotter, mocker):
        """ Test the 3Dplot rendering and generation """
        # Test 3D printout
        mocker.patch.object(FigureCanvas, 'draw')
        mocker.patch.object(Axes3D, 'plot_surface')
        mocker.patch.object(plotter.figure, 'colorbar')

        plotter.dimension = 3
        plotter.data = self.data
        plotter.showPlot(data=plotter.data0.data,
                              qx_data=self.data.qx_data,
                              qy_data=self.data.qy_data,
                              xmin=self.data.xmin,
                              xmax=self.data.xmax,
                              ymin=self.data.ymin, ymax=self.data.ymax,
                              cmap=None, zmin=None,
                              zmax=None)
        assert Axes3D.plot_surface.called
        assert FigureCanvas.draw.called

    @pytest.mark.skip(reason="2022-09 already broken - causes segfault")
    def testShow2DPlot(self, plotter, mocker):
        """ Test the 2Dplot rendering and generation """
        # Test 2D printout
        mocker.patch.object(FigureCanvas, 'draw_idle')
        mocker.patch.object(plotter.figure, 'colorbar')

        plotter.dimension = 2
        plotter.data = self.data
        plotter.showPlot(data=self.data.data,
                              qx_data=self.data.qx_data,
                              qy_data=self.data.qy_data,
                              xmin=self.data.xmin,
                              xmax=self.data.xmax,
                              ymin=self.data.ymin, ymax=self.data.ymax,
                              cmap=None, zmin=None,
                              zmax=None)
        assert FigureCanvas.draw_idle.called
