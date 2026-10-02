import matplotlib as mpl
import pytest

mpl.use("Qt5Agg")

from PySide6 import QtWidgets

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.MainWindow.WorkspaceManager import WorkspaceManager
from sas.qtgui.Perspectives.SizeDistribution.SizeDistributionPerspective import (
    SizeDistributionWindow,
)
from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Utilities.GuiUtils import communicator


def host_in_workspace(widget):
    """Host a perspective in a workspace window, as the application does"""
    window = QtWidgets.QMainWindow()
    mdi = QtWidgets.QMdiArea()
    window.setCentralWidget(mdi)
    window.show()
    manager = WorkspaceManager(mdi, window)
    manager.add(widget)
    return window, manager


class SizeDistributionTest:
    """Test the SizeDistribution Perspective GUI"""

    @pytest.fixture(autouse=True)
    def widget(self, qtbot):
        """Create/Destroy the SizeDistributionWindow"""

        class dummy_manager:
            HELP_DIRECTORY_LOCATION = "html"
            communicator = communicator

        w = SizeDistributionWindow(parent=dummy_manager())
        w._parent = QtWidgets.QMainWindow()
        qtbot.addWidget(w)

        self.fakeData1 = GuiUtils.HashableStandardItem("A")
        self.fakeData2 = GuiUtils.HashableStandardItem("B")
        reference_data1 = Data1D(x=[0.1, 0.2], y=[0.0, 0.0], dy=[0.0, 0.0])
        reference_data1.filename = "Test A"
        reference_data2 = Data1D(x=[0.1, 0.2], y=[0.0, 0.0], dy=[0.0, 0.0])
        reference_data2.filename = "Test B"
        GuiUtils.updateModelItem(self.fakeData1, reference_data1)
        GuiUtils.updateModelItem(self.fakeData2, reference_data2)

        yield w

        """ Destroy the SizeDistributionWindow """
        w.setClosable(False)
        w.close()

    def baseGUIState(self, widget):
        """Testing base state of SizeDistribution"""
        # base class information
        assert isinstance(widget, QtWidgets.QWidget)
        assert widget.windowTitle() == "Size Distribution Perspective"
        assert not widget.isClosable()
        # mapper
        assert isinstance(widget.mapper, QtWidgets.QDataWidgetMapper)
        # buttons
        assert not widget.quickFitButton.isEnabled()
        assert widget.helpButton.isEnabled()

    def testDefaults(self, widget):
        """Test the GUI in its default state"""
        self.baseGUIState(widget)

    def testRemoveData(self, widget):
        """Test data removal from widget"""
        widget.setData([self.fakeData1])
        assert widget.logic.data is not None
        widget.removeData([self.fakeData1])
        assert widget._data is None

    def testClose(self, widget):
        """Test methods related to closing the window"""
        window, manager = host_in_workspace(widget)
        container = manager.container_of(widget)
        # A perspective that is not closable refuses; its window is minimised instead
        assert not widget.isClosable()
        assert not manager.close(widget)
        assert container.isMinimized()
        manager.activate(widget)
        widget.setClosable(False)
        assert not widget.isClosable()
        assert not manager.close(widget)
        assert container.isMinimized()
        assert manager.is_hosted(widget)
        manager.remove(widget)
        window.close()
        widget.setClosable(True)
        assert widget.isClosable()
        widget.setClosable()
        assert widget.isClosable()
