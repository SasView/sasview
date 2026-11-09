import pytest
from PySide6 import QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from sasdata import dataset_types

import sas.qtgui.Calculators.SlitSizeCalculator as slit_size_module
import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Calculators.SlitSizeCalculator import SlitSizeCalculator
from sas.qtgui.UnitTesting import base_path


class SlitSizeCalculatorTest:
    """Test the SlitSizeCalculator"""
    @pytest.fixture(autouse=True)
    def widget(self, qapp):
        """Create/Destroy the SlitSizeCalculator"""
        w = SlitSizeCalculator(None)

        yield w

        w.close()
        w = None

    def testDefaults(self, widget):
        """Test the GUI in its default state"""
        assert isinstance(widget, QtWidgets.QWidget)
        assert widget.windowTitle() == "Slit Size Calculator"
        sp = widget.sizePolicy()
        assert sp.horizontalPolicy() == QtWidgets.QSizePolicy.Policy.Preferred
        assert sp.verticalPolicy() == QtWidgets.QSizePolicy.Policy.Preferred

    def testHelp(self, widget, mocker):
        """ Assure help file is shown """
        show_help = mocker.patch.object(GuiUtils, 'showHelp')
        widget.onHelp()
        show_help.assert_called_once()
        assert 'slit_calculator_help.html' in show_help.call_args[0][0]

    def testBrowseButton(self, widget, mocker):
        browseButton = widget.browseButton

        filename = str(base_path / "beam_profile.DAT")

        # Return no files.
        mocker.patch.object(QtWidgets.QFileDialog, 'getOpenFileName', return_value=('',''))

        # Click on the Browse button
        QTest.mouseClick(browseButton, Qt.LeftButton)

        # Test the getOpenFileName() dialog called once
        assert QtWidgets.QFileDialog.getOpenFileName.called
        QtWidgets.QFileDialog.getOpenFileName.assert_called_once()

        # Now, return a single file
        mocker.patch.object(QtWidgets.QFileDialog, 'getOpenFileName', return_value=(filename,''))

        # Click on the Load button
        QTest.mouseClick(browseButton, Qt.LeftButton)
        QtWidgets.QApplication.processEvents()

        # Test the getOpenFileName() dialog called once
        assert QtWidgets.QFileDialog.getOpenFileName.called
        QtWidgets.QFileDialog.getOpenFileName.assert_called_once()

    def testCalculateSlitSize(self, widget):
        """ Test slit size calculated value """
        # Load through the widget's own loader, so a change in how files are
        # read is caught here too.
        data = widget.loadFile(str(base_path / "beam_profile.DAT"))
        assert data.dataset_type == dataset_types.one_dim

        widget.calculateSlitSize(data)
        # The value "5.5858" was obtained by manual calculation.
        # It turns out our slit length is FWHM/2
        assert float(widget.slit_length_out.text()) == pytest.approx(5.5858/2, abs=1e-3)
        assert widget.unit_out.text() == "[Unknown]"

    def testBrowseComputesSlitSize(self, widget, mocker):
        """ Choosing a file loads it and shows the result """
        filename = str(base_path / "beam_profile.DAT")
        mocker.patch.object(QtWidgets.QFileDialog, 'getOpenFileName', return_value=(filename, ''))

        QTest.mouseClick(widget.browseButton, Qt.LeftButton)

        assert widget.data_file.text() == "beam_profile.DAT"
        assert float(widget.slit_length_out.text()) == pytest.approx(5.5858/2, abs=1e-3)

    def testWrongInput(self, widget, mocker):
        """ Test on wrong input data """
        error = mocker.patch.object(slit_size_module.logger, 'error')

        data_2d = widget.loadFile(str(base_path / "P123_D2O_10_percent.dat"))
        assert data_2d.dataset_type == dataset_types.two_dim
        widget.calculateSlitSize(data_2d)
        error.assert_called_once()
        assert "2D" in error.call_args[0][0]
        assert widget.slit_length_out.text() == "ERROR!"

        widget.calculateSlitSize(None)
        assert error.call_count == 2

    def testEmptyFileClearsThePreviousResult(self, widget, mocker):
        """ An empty file must not leave the previous file's result on display """
        widget.calculateSlitSize(widget.loadFile(str(base_path / "beam_profile.DAT")))
        assert widget.slit_length_out.text() != "ERROR!"

        error = mocker.patch.object(slit_size_module.logger, 'error')
        widget.calculateSlitSize(widget.loadFile(str(base_path / "empty_file.txt")))

        error.assert_called_once()
        assert widget.slit_length_out.text() == "ERROR!"
