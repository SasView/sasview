import logging
from pathlib import Path

import pytest
from PySide6 import QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from sasdata.dataloader.loader import Loader

from sas.qtgui.Calculators.SlitSizeCalculator import SlitSizeCalculator

logger = logging.getLogger(__name__)


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
        widget._parent = QtWidgets.QWidget()
        mocker.patch.object(widget._parent, 'showHelp', create=True)
        widget.onHelp()
        widget._parent.showHelp.assert_called_once()
        args = widget._parent.showHelp.call_args
        assert 'slit_calculator_help.html' in args[0][0]

    def testBrowseButton(self, widget, mocker):
        browseButton = widget.browseButton

        filename = str(Path("./src/sas/qtgui/UnitTesting/beam_profile.DAT").absolute())

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
        QtWidgets.qApp.processEvents()

        # Test the getOpenFileName() dialog called once
        assert QtWidgets.QFileDialog.getOpenFileName.called
        QtWidgets.QFileDialog.getOpenFileName.assert_called_once()

    @pytest.mark.skip(reason="2022-09 already broken - already skipped")
    def testCalculateSlitSize(self, widget):
        """ Test slit size calculated value """

        filename = str(Path("./src/sas/qtgui/UnitTesting/beam_profile.DAT").absolute())
        loader = Loader()
        data = loader.load(filename)[0]

        widget.calculateSlitSize(data)
        # The value "5.5858" was obtained by manual calculation.
        # It turns out our slit length is FWHM/2
        assert float(widget.slit_length_out.text()) == pytest.approx(5.5858/2, abs=1e-3)

    @pytest.mark.xfail(reason="2022-09 already broken - input file issue")
    def testWrongInput(self, widget, mocker):
        """ Test on wrong input data """

        filename = str(Path("./src/sas/qtgui/UnitTesting/Dec07031.ASC").absolute())
        loader = Loader()
        data = loader.load(filename)[0]

        mocker.patch.object(logger, 'error')

        widget.calculateSlitSize(data)

        logger.error.assert_not_called()

        data = None
        widget.calculateSlitSize(data)
        logger.error.assert_not_called()
