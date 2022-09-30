import sys
import unittest
import webbrowser
from unittest.mock import MagicMock

import os
os.environ["MPLBACKEND"] = "qtagg"

from PyQt5 import QtGui, QtWidgets
from PyQt5 import QtCore
from PyQt5 import QtTest

# set up import paths
import sas.qtgui.path_prepare

from sas.qtgui.UnitTesting.TestUtils import QtSignalSpy
from sas.qtgui.Utilities.GuiUtils import Communicate
from sas.qtgui.Plotting.Plotter2D import Plotter2D
from sas.qtgui.Plotting.PlotterData import Data2D

# Local
from sas.qtgui.Plotting.SlicerParameters import SlicerParameters

if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)


class dummy_manager(object):
    # def communicator(self):
    #     return Communicate()
    communicator = Communicate()
    communicate = Communicate()
    active_plots = {}


def testData():
    data = Data2D(image=[0.1] * 4,
                  qx_data=[1.0, 2.0, 3.0, 4.0],
                  qy_data=[10.0, 11.0, 12.0, 13.0],
                  dqx_data=[0.1, 0.2, 0.3, 0.4],
                  dqy_data=[0.1, 0.2, 0.3, 0.4],
                  q_data=[1, 2, 3, 4],
                  xmin=-1.0, xmax=5.0,
                  ymin=-1.0, ymax=15.0,
                  zmin=-1.0, zmax=20.0)

    data.title = "Test data"
    data.id = 1
    data.ndim = 1
    return data

class SlicerParametersTest(unittest.TestCase):
    '''Test the SlicerParameters dialog'''
    def setUp(self):
        '''Create the SlicerParameters dialog'''
        self.model = QtGui.QStandardItemModel()
        plotter = Plotter2D(parent=dummy_manager(), quickplot=False)
        plotter.data = testData()
        active_plots = {"test_plot": plotter}
        self.widget = SlicerParameters(model=self.model, parent=plotter,
                                       active_plots=active_plots,
                                       communicator=dummy_manager().communicate)

    def tearDown(self):
        '''Destroy the model'''
        self.widget = None

    def testDefaults(self):
        '''Test the GUI in its default state'''
        assert isinstance(self.widget.proxy, QtCore.QIdentityProxyModel)
        assert isinstance(self.widget.lstParams.itemDelegate(), QtWidgets.QStyledItemDelegate)
        assert self.widget.lstParams.model().columnReadOnly(0)
        assert not self.widget.lstParams.model().columnReadOnly(1)

        # Test the proxy model
        assert self.widget.lstParams.model() == self.widget.proxy
        assert self.widget.proxy.columnCount() == 0
        assert self.widget.proxy.rowCount() == 0

        # Slicer choice
        assert self.widget.cbSlicer.count(), 5
        assert self.widget.cbSlicer.itemText(0), 'None'

        # Batch slicing options tab
        assert not self.widget.cbSave1DPlots.isChecked()
        assert not self.widget.txtLocation.isEnabled()
        assert self.widget.cbSlicer.count(), 3
        assert self.widget.cbSlicer.itemText(0), 'No fitting'

    def testLstParams(self):
        ''' test lstParams with content '''
        item1 = QtGui.QStandardItem('t1')
        item2 = QtGui.QStandardItem('t2')
        model = QtGui.QStandardItemModel()
        model.appendRow([item1, item2])
        item1 = QtGui.QStandardItem('t3')
        item2 = QtGui.QStandardItem('t4')
        model.appendRow([item1, item2])

        plotter = Plotter2D(parent=dummy_manager(), quickplot=False)
        plotter.data = testData()
        active_plots = {"test_plot": plotter}
        widget = SlicerParameters(model=model, parent=plotter,
                                  active_plots=active_plots,
                                  communicator=dummy_manager().communicate)
        assert widget.proxy.columnCount() == 2
        assert widget.proxy.rowCount() == 2
        assert widget.model.item(0, 0).text() == 't1'
        assert widget.model.item(0, 1).text() == 't2'
        # Check the flags in the proxy model
        flags = widget.proxy.flags(widget.proxy.index(0, 0))
        assert not flags & QtCore.Qt.ItemIsEditable
        assert flags & QtCore.Qt.ItemIsSelectable
        assert flags & QtCore.Qt.ItemIsEnabled

    def testClose(self):
        ''' Assure that clicking on Close triggers right behaviour'''
        self.widget.show()

        # Set up the spy
        spy_close = QtSignalSpy(self.widget, self.widget.closeWidgetSignal)
        # Click on the "Close" button
        QtTest.QTest.mouseClick(self.widget.cmdClose, QtCore.Qt.LeftButton)

        # Check the signal
        assert spy_close.count() == 1
        self.widget.close()

    def testOnHelp(self):
        ''' Assure clicking on help returns QtWeb view on requested page'''
        self.widget.show()

        #Mock the webbrowser.open method
        webbrowser.open = MagicMock()

        # Invoke the action
        self.widget.onHelp()

        # Check if show() got called
        assert webbrowser.open.called

        # Assure the filename is correct
        assert "graph_help.html" in webbrowser.open.call_args[0][0]

        self.widget.close()

    def testSetModel(self):
        ''' Test if resetting the model works'''
        item1 = QtGui.QStandardItem("s1")
        item2 = QtGui.QStandardItem("5.0")
        new_model = QtGui.QStandardItemModel()
        new_model.appendRow([item1, item2])
        item1 = QtGui.QStandardItem("s2")
        item2 = QtGui.QStandardItem("20.0")
        new_model.appendRow([item1, item2])
        # Force the new model onto the widget
        self.widget.setModel(model=new_model)

        # Test if the widget got it
        assert self.widget.model.columnCount() == 2
        assert self.widget.model.rowCount() == 2
        assert self.widget.model.item(0, 0).text() == 's1'
        assert self.widget.model.item(1, 0).text() == 's2'

    def testPlotSave(self):
        ''' defaults for the Auto Save options '''
        assert not self.widget.cbSave1DPlots.isChecked()
        assert not self.widget.txtLocation.isEnabled()
        assert not self.widget.txtExtension.isEnabled()
        assert not self.widget.cbFitOptions.isEnabled()
        assert not self.widget.cbSaveExt.isEnabled()

        # Select auto save
        self.widget.cbSave1DPlots.setChecked(True)
        assert self.widget.txtLocation.isEnabled()
        assert self.widget.txtExtension.isEnabled()
        assert self.widget.cbFitOptions.isEnabled()
        assert self.widget.cbSaveExt.isEnabled()

    def testPlotList(self):
        ''' check if the plot list shows correct content '''
        assert self.widget.lstPlots.count() == 1
        assert self.widget.lstPlots.item(0).text() == "test_plot"
        assert not self.widget.lstPlots.item(0).checkState()

    def testOnSlicerChange(self):
        ''' change the slicer '''
        self.widget.onApply = MagicMock()
        assert self.widget.lstParams.model().rowCount() == 0
        assert self.widget.lstParams.model().columnCount() == 0
        assert self.widget.lstParams.model().index(0, 0).data() == None

    def testOnApply(self):
        self.widget.lstPlots.item(0).setCheckState(True)
        self.widget.applyPlotter = MagicMock()
        self.widget.save1DPlotsForPlot = MagicMock()
        assert not self.widget.isSave
        # Apply without 1D data saved
        self.widget.onApply()
        self.widget.applyPlotter.assert_called_once()
        self.widget.save1DPlotsForPlot.assert_not_called()

        # Apply with 1D data saved
        self.widget.cbSave1DPlots.setCheckState(True)
        assert self.widget.isSave
        self.widget.onApply()
        assert self.widget.model is not None
        self.widget.applyPlotter.assert_called()
        self.widget.save1DPlotsForPlot.assert_called_once()


if __name__ == "__main__":
    unittest.main()
