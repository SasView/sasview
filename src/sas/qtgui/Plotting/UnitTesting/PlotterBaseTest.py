import platform

import matplotlib as mpl
import pytest

mpl.use("Qt5Agg")

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PySide6 import QtCore, QtGui, QtPrintSupport, QtWidgets

import sas.qtgui.Plotting.PlotHelper as PlotHelper

# Tested module
import sas.qtgui.Plotting.PlotterBase as PlotterBase
from sas.qtgui.MainWindow.UnitTesting.DataExplorerTest import MyPerspective
from sas.qtgui.Plotting.ScaleProperties import ScaleProperties
from sas.qtgui.Plotting.WindowTitle import WindowTitle
from sas.qtgui.Utilities.GuiUtils import Communicate


class PlotterBaseTest:
    '''Test the Plotter base class'''

    @pytest.fixture(autouse=True)
    def plotter(self, qapp):
        '''Create/Destroy the AboutBox'''
        class dummy_manager:
            def communicator(self):
                return Communicate()
            def perspective(self):
                return MyPerspective()

        #PlotterBase.PlotterBase.contextMenuQuickPlot = MagicMock()
        p = PlotterBase.PlotterBase(None, manager=dummy_manager(), quickplot=True)
        self.isWindows = platform.system=="Windows"

        yield p

    def testDefaults(self, plotter):
        """ default method variables values """
        assert isinstance(plotter, QtWidgets.QWidget)
        assert isinstance(plotter.canvas, FigureCanvas)
        assert isinstance(plotter.properties, ScaleProperties)

        assert len(plotter._data) == 0
        assert plotter._xscale == 'log'
        assert plotter._yscale == 'log'
        assert plotter.scale == 'linear'
        assert not plotter.grid_on
        assert plotter.x_label == 'log10(x)'
        assert plotter.y_label == 'log10(y)'

    def testData(self, plotter):
        ''' Test the pure virtual method '''
        with pytest.raises(NotImplementedError):
            plotter.data=[]

    def testContextMenu(self, plotter):
        ''' Test the default context menu '''
        with pytest.raises(NotImplementedError):
            plotter.createContextMenu()

    def testClean(self, plotter, mocker):
        ''' test the graph cleanup '''
        mocker.patch.object(plotter.figure, 'delaxes')
        plotter.clean()
        assert plotter.figure.delaxes.called

    def testPlot(self, plotter):
        ''' test the pure virtual method '''
        with pytest.raises(NotImplementedError):
            plotter.plot()

    def notestOnCloseEvent(self, plotter, mocker):
        ''' test the plotter close behaviour '''
        mocker.patch.object(PlotHelper, 'deletePlot')
        plotter.closeEvent(None)
        assert PlotHelper.deletePlot.called

    def notestOnImagePrint(self, plotter, mocker):
        ''' test the workspace print '''
        mocker.patch.object(QtGui.QPainter, 'end')
        mocker.patch.object(QtWidgets.QLabel, 'render')

        # First, let's cancel printing
        mocker.patch.object(QtPrintSupport.QPrintDialog, 'exec_', return_value=QtWidgets.QDialog.Rejected)
        plotter.onImagePrint()
        assert not QtGui.QPainter.end.called
        assert not QtWidgets.QLabel.render.called

        # Let's print now
        mocker.patch.object(QtPrintSupport.QPrintDialog, 'exec_', return_value=QtWidgets.QDialog.Accepted)
        plotter.onImagePrint()
        assert QtGui.QPainter.end.called
        assert QtWidgets.QLabel.render.called

    def testOnClipboardCopy(self, plotter, mocker):
        ''' test the workspace screen copy '''
        mocker.patch.object(QtGui.QClipboard, 'setPixmap')
        plotter.onClipboardCopy()
        assert QtGui.QClipboard.setPixmap.called

    def testOnGridToggle(self, plotter, mocker):
        ''' test toggling the grid lines '''
        # Check the toggle
        orig_toggle = plotter.grid_on

        mocker.patch.object(FigureCanvas, 'draw_idle')
        plotter.onGridToggle()

        assert FigureCanvas.draw_idle.called
        assert plotter.grid_on != orig_toggle

    def testDefaultContextMenu(self, plotter, mocker):
        """ Test the right click default menu """

        plotter.defaultContextMenu()

        actions = plotter.contextMenu.actions()
        assert len(actions) == 4

        # Trigger Print Image and make sure the method is called
        assert actions[1].text() == "Print Image"
        mocker.patch.object(QtPrintSupport.QPrintDialog, 'exec_', return_value=QtWidgets.QDialog.Rejected)
        actions[1].trigger()
        assert QtPrintSupport.QPrintDialog.exec_.called

        # Trigger Copy to Clipboard and make sure the method is called
        assert actions[2].text() == "Copy to Clipboard"

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

        # Trigger toggle navigation bar and make sure the method is called
        #assert actions[4].text() == "Toggle Navigation Menu"
        #isShown = plotter.toolbar.isVisible()
        #assert isShown
        #actions[4].trigger()
        #isShown = plotter.toolbar.isVisible()
        #assert not isShown
        #actions[4].trigger()
        #isShown = plotter.toolbar.isVisible()
        #assert isShown


    def testOnWindowsTitle(self, plotter, mocker):
        """ Test changing the plot title"""
        # Mock the modal dialog's response
        mocker.patch.object(QtWidgets.QDialog, 'exec_', return_value=QtWidgets.QDialog.Accepted)
        plotter.show()
        # Assure the original title is none
        assert plotter.windowTitle() == ""
        mocker.patch.object(plotter.manager, 'communicator')

        mocker.patch.object(WindowTitle, 'title', return_value="I am a new title")
        # Change the title
        plotter.onWindowsTitle()

        assert plotter.windowTitle() == "I am a new title"

    def testOnMplMouseDown(self, plotter):
        """ Test what happens on mouse click down in chart """
        pass

    def testOnMplMouseUp(self, plotter):
        """ Test what happens on mouse release in chart """
        pass

    def testOnMplMouseMotion(self, plotter):
        """ Test what happens on mouse move in chart """
        pass

    def testOnMplPick(self, plotter):
        """ Test what happens on mouse pick in chart """
        pass

    def testOnMplWheel(self, plotter):
        """ Test what happens on mouse pick in chart """
        pass
