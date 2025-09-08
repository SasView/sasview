import webbrowser

import matplotlib as mpl
import pytest

mpl.use("Qt5Agg")

from PySide6 import QtCore, QtGui, QtWidgets

from sas.qtgui.Plotting.Plotter2D import Plotter2D
from sas.qtgui.Plotting.PlotterData import Data2D

# Local
from sas.qtgui.Plotting.SlicerParameters import SlicerParameters
from sas.qtgui.UnitTesting.TestUtils import QtSignalSpy
from sas.qtgui.Utilities.GuiUtils import Communicate


class dummy_manager:
    # def communicator(self):
    #     return Communicate()
    communicator = Communicate()
    communicate = Communicate()
    active_plots = {}


class SlicerParametersTest:
    '''Test the SlicerParameters dialog'''

    @pytest.fixture(autouse=True)
    def data(self):
        d = Data2D(image=[0.1] * 4,
                    qx_data=[1.0, 2.0, 3.0, 4.0],
                    qy_data=[10.0, 11.0, 12.0, 13.0],
                    dqx_data=[0.1, 0.2, 0.3, 0.4],
                    dqy_data=[0.1, 0.2, 0.3, 0.4],
                    q_data=[1, 2, 3, 4],
                    xmin=-1.0, xmax=5.0,
                    ymin=-1.0, ymax=15.0,
                    zmin=-1.0, zmax=20.0)

        d.title = "Test data"
        d.id = 1
        d.ndim = 1
        yield d

    @pytest.fixture(autouse=True)
    def widget(self, qapp, data):
        '''Create/Destroy the SlicerParameters'''

        ## FIXME: any second creation of this fixture causes the Python
        ## interpreter to segfault at the end of the tests being run.
        ## Every single test passes on its own, but none of them together.

        model = QtGui.QStandardItemModel()
        plotter = Plotter2D(parent=dummy_manager(), quickplot=False)
        plotter.data = data
        active_plots = {"test_plot": plotter}
        w = SlicerParameters(model=model, parent=plotter,
                                       active_plots=active_plots,
                                       communicator=dummy_manager().communicate)
        yield w
        w.close()

    def testDefaults(self, widget):
        '''Test the GUI in its default state'''
        assert isinstance(widget.proxy, QtCore.QIdentityProxyModel)
        assert isinstance(widget.lstParams.itemDelegate(), QtWidgets.QStyledItemDelegate)
        assert widget.lstParams.model().columnReadOnly(0)
        assert not widget.lstParams.model().columnReadOnly(1)

        # Test the proxy model
        assert widget.lstParams.model() == widget.proxy
        assert widget.proxy.columnCount() == 0
        assert widget.proxy.rowCount() == 0

        # Slicer choice
        assert widget.cbSlicer.count(), 5
        assert widget.cbSlicer.itemText(0), 'None'

        # Batch slicing options tab
        assert not widget.cbSave1DPlots.isChecked()
        assert not widget.txtLocation.isEnabled()
        assert widget.cbSlicer.count(), 3
        assert widget.cbSlicer.itemText(0), 'No fitting'

    @pytest.mark.skip(reason="2022-09 already broken - causes segfault")
    def testLstParams(self, widget, data):
        ''' test lstParams with content '''
        item1 = QtGui.QStandardItem('t1')
        item2 = QtGui.QStandardItem('t2')
        model = QtGui.QStandardItemModel()
        model.appendRow([item1, item2])
        item1 = QtGui.QStandardItem('t3')
        item2 = QtGui.QStandardItem('t4')
        model.appendRow([item1, item2])

        plotter = Plotter2D(parent=dummy_manager(), quickplot=False)
        plotter.data = data
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

    @pytest.mark.skip(reason="2022-09 already broken - causes segfault")
    def testClose(self, widget, qtbot):
        ''' Assure that clicking on Close triggers right behaviour'''
        widget.show()
        qtbot.addWidget(widget)

        # Set up the spy
        spy_close = QtSignalSpy(widget, widget.closeWidgetSignal)
        # Click on the "Close" button
        qtbot.mouseClick(widget.cmdClose, QtCore.Qt.LeftButton)

        # Check the signal
        assert spy_close.count() == 1

    @pytest.mark.skip(reason="2022-09 already broken - causes segfault")
    def testOnHelp(self, widget, mocker):
        ''' Assure clicking on help returns QtWeb view on requested page'''
        widget.show()

        #Mock the webbrowser.open method
        mocker.patch.object(webbrowser, 'open')

        # Invoke the action
        widget.onHelp()

        # Check if show() got called
        assert webbrowser.open.called

        # Assure the filename is correct
        assert "graph_help.html" in webbrowser.open.call_args[0][0]

    @pytest.mark.skip(reason="2022-09 already broken - causes segfault")
    def testSetModel(self, widget):
        ''' Test if resetting the model works'''
        item1 = QtGui.QStandardItem("s1")
        item2 = QtGui.QStandardItem("5.0")
        new_model = QtGui.QStandardItemModel()
        new_model.appendRow([item1, item2])
        item1 = QtGui.QStandardItem("s2")
        item2 = QtGui.QStandardItem("20.0")
        new_model.appendRow([item1, item2])
        # Force the new model onto the widget
        widget.setModel(model=new_model)

        # Test if the widget got it
        assert widget.model.columnCount() == 2
        assert widget.model.rowCount() == 2
        assert widget.model.item(0, 0).text() == 's1'
        assert widget.model.item(1, 0).text() == 's2'

    @pytest.mark.skip(reason="2022-09 already broken - causes segfault")
    def testPlotSave(self, widget):
        ''' defaults for the Auto Save options '''
        assert not widget.cbSave1DPlots.isChecked()
        assert not widget.txtLocation.isEnabled()
        assert not widget.txtExtension.isEnabled()
        assert not widget.cbFitOptions.isEnabled()
        assert not widget.cbSaveExt.isEnabled()

        # Select auto save
        widget.cbSave1DPlots.setChecked(True)
        assert widget.txtLocation.isEnabled()
        assert widget.txtExtension.isEnabled()
        assert widget.cbFitOptions.isEnabled()
        assert widget.cbSaveExt.isEnabled()

    @pytest.mark.skip(reason="2022-09 already broken - causes segfault")
    def testPlotList(self, widget):
        ''' check if the plot list shows correct content '''
        assert widget.lstPlots.count() == 1
        assert widget.lstPlots.item(0).text() == "test_plot"
        assert not widget.lstPlots.item(0).checkState()

    @pytest.mark.skip(reason="2022-09 already broken - causes segfault")
    def testOnSlicerChange(self, widget, mocker):
        ''' change the slicer '''
        mocker.patch.object(widget, 'onApply')
        assert widget.lstParams.model().rowCount() == 0
        assert widget.lstParams.model().columnCount() == 0
        assert widget.lstParams.model().index(0, 0).data() is None

    @pytest.mark.skip(reason="2022-09 already broken - causes segfault")
    def testOnApply(self, widget, mocker):
        widget.lstPlots.item(0).setCheckState(True)
        mocker.patch.object(widget, 'applyPlotter')
        mocker.patch.object(widget, 'save1DPlotsForPlot')
        assert not widget.isSave
        # Apply without 1D data saved
        widget.onApply()
        widget.applyPlotter.assert_called_once()
        widget.save1DPlotsForPlot.assert_not_called()

        # Apply with 1D data saved
        widget.cbSave1DPlots.setCheckState(True)
        assert widget.isSave
        widget.onApply()
        assert widget.model is not None
        widget.applyPlotter.assert_called()
        widget.save1DPlotsForPlot.assert_called_once()
