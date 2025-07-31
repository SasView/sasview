# CRUFT: this shouldn't be needed in the test but makes the difference
# between passing tests and failing tests. Remove this and figure out how
# to fix the resolution calculator widget itself?
import matplotlib as mpl
import pytest
from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

mpl.use("Qt5Agg")

from twisted.internet import threads

from sas.qtgui.Calculators.ResolutionCalculatorPanel import ResolutionCalculatorPanel
from sas.qtgui.Utilities.GuiUtils import Communicate

BG_COLOR_ERR = 'background-color: rgb(244, 170, 164);'

BG_COLOR_WARNING = 'background-color: rgb(244, 217, 164);'

class ResolutionCalculatorPanelTest:
    """Test the ResolutionCalculatorPanel"""

    @pytest.fixture(autouse=True)
    def widget(self, qapp):
        """Create/Destroy the ResolutionCalculatorPanel"""
        class dummy_manager:
            def communicator(widget):
                return Communicate()

        w = ResolutionCalculatorPanel(dummy_manager())

        yield w

        w.close()
        w = None

    def testDefaults(self, widget):
        """Test the GUI in its default state"""

        assert isinstance(widget, QtWidgets.QDialog)
        assert widget.windowTitle() == "Q Resolution Estimator"
        # size
        assert widget.size().height() == 540
        assert widget.size().width() == 876

        # visibility
        assert not widget.lblSpectrum.isVisible()
        assert not widget.cbCustomSpectrum.isVisible()

        # content of line edits
        assert widget.txtDetectorPixSize.text() == '0.5, 0.5'
        assert widget.txtDetectorSize.text() == '128, 128'
        assert widget.txtSample2DetectorDistance.text() == '1000'
        assert widget.txtSampleApertureSize.text() == '1.27'
        assert widget.txtSampleOffset.text() == '0'
        assert widget.txtSource2SampleDistance.text() == '1627'
        assert widget.txtSourceApertureSize.text() == '3.81'
        assert widget.txtWavelength.text() == '6.0'
        assert widget.txtWavelengthSpread.text() == '0.125'

        assert widget.txtQx.text() == '0.0'
        assert widget.txtQy.text() == '0.0'

        assert widget.txt1DSigma.text() == '0.0008289'
        assert widget.txtSigma_lamd.text() == '3.168e-05'
        assert widget.txtSigma_x.text() == '0.0008288'
        assert widget.txtSigma_x.text() == '0.0008288'

        # items of comboboxes
        assert not widget.cbCustomSpectrum.isEditable()
        assert widget.cbCustomSpectrum.currentText() == 'Flat'
        assert widget.cbCustomSpectrum.currentIndex() == 0
        assert [widget.cbCustomSpectrum.itemText(i) for i in
                                range(widget.cbCustomSpectrum.count())] == \
                                ['Flat', 'Add New']

        assert not widget.cbSource.isEditable()
        assert widget.cbSource.count() == 6
        assert widget.cbSource.currentText() == 'Neutron'
        assert [widget.cbSource.itemText(i) for i in
                                range(widget.cbSource.count())] == \
                                ['Alpha', 'Deutron', 'Neutron', 'Photon',
                                'Proton', 'Triton']

        assert not widget.cbWaveColor.isEditable()
        assert widget.cbWaveColor.count() == 2
        assert widget.cbWaveColor.currentText() == 'Monochromatic'
        assert [widget.cbWaveColor.itemText(i) for i in
                                range(widget.cbWaveColor.count())] == \
                                ['Monochromatic', 'TOF']

        # read only text edits
        assert widget.txtSigma_x.isReadOnly()
        assert widget.txtSigma_y.isReadOnly()
        assert widget.txtSigma_lamd.isReadOnly()
        assert widget.txt1DSigma.isReadOnly()

        # tooltips
        assert widget.cbSource.toolTip() == \
                            "Source Selection: " \
                            "Affect on the gravitational contribution."
        widget.cbCustomSpectrum.toolTip(), \
        "Wavelength Spectrum: Intensity vs. wavelength."
        # print widget.txtDetectorPixSize.toolTip()
        assert widget.txtDetectorPixSize.toolTip() == \
                            "Detector Pixel Size."
        assert widget.txtDetectorSize.toolTip() == \
                            "Number of Pixels on Detector."
        assert widget.txtSample2DetectorDistance.toolTip() == \
                            "Sample Aperture to Detector Distance."
        assert widget.txtSampleApertureSize.toolTip() == \
                            "Sample Aperture Size."
        assert widget.txtSampleOffset.toolTip() == \
                            "Sample Offset."
        assert widget.txtSource2SampleDistance.toolTip() == \
                            "Source to Sample Aperture Distance."
        assert widget.txtSourceApertureSize.toolTip() == \
                            "Source Aperture Size."
        assert widget.txtWavelength.toolTip() == \
                            "Wavelength of the Neutrons."
        assert widget.txtWavelengthSpread.toolTip() == \
                            "Wavelength Spread of Neutrons."
        assert widget.txtQx.toolTip() == "Type the Qx value."
        assert widget.txtQy.toolTip() == "Type the Qy value."
        assert widget.txt1DSigma.toolTip() == \
                            "Resolution in 1-dimension (for 1D data)."
        assert widget.txtSigma_lamd.toolTip() == \
                            "The wavelength contribution in the radial direction." \
                            " Note: The phi component is always zero."
        assert widget.txtSigma_x.toolTip() == \
                            "The x component of the geometric resolution, " \
                            "excluding sigma_lamda."
        assert widget.txtSigma_y.toolTip() == \
                            "The y component of the geometric resolution, " \
                            "excluding sigma_lamda."

    def testFormatNumber(self, widget):
        assert widget.formatNumber('  7.123456  ') == '7.123'

    def testCheckWavelength(self, widget):
        """ Test validator for Wavelength text edit"""
        widget.txtWavelength.clear()
        # Enter invalid input for Monochromatic spectrum
        # check that background becomes red and Compute button is disabled
        QTest.keyClicks(widget.txtWavelength, 'vcv ')
        QTest.keyClick(widget.txtWavelength, QtCore.Qt.Key_Return)
        assert BG_COLOR_ERR in widget.txtWavelength.styleSheet()
        assert not widget.cmdCompute.isEnabled()

        # Enter invalid input for TOF spectrum
        # check that background becomes red and Compute button is disabled
        widget.cbWaveColor.setCurrentIndex(1)

        widget.txtWavelength.clear()
        QTest.keyClicks(widget.txtWavelength, '4')
        QTest.keyClick(widget.txtWavelength, QtCore.Qt.Key_Return)
        assert BG_COLOR_ERR in widget.txtWavelength.styleSheet()
        assert not widget.cmdCompute.isEnabled()

    def testCheckWavelengthSpread(self, widget):
        """ Test validator for WavelengthSpread """
        widget.txtWavelengthSpread.clear()
        QTest.keyClicks(widget.txtWavelengthSpread, '0.12; 1.3')
        QTest.keyClick(widget.txtWavelengthSpread, QtCore.Qt.Key_Return)
        assert BG_COLOR_ERR in \
                        widget.txtWavelengthSpread.styleSheet()

    def testCheckPixels(self, widget):
        """ Test validator for pixel size and number """
        widget.txtDetectorPixSize.clear()
        QTest.keyClicks(widget.txtDetectorPixSize, '0.12; 1.3')
        QTest.keyClick(widget.txtDetectorPixSize, QtCore.Qt.Key_Return)
        assert BG_COLOR_ERR in \
                        widget.txtDetectorPixSize.styleSheet()

        widget.txtDetectorSize.clear()
        QTest.keyClicks(widget.txtDetectorSize, '0.12')
        QTest.keyClick(widget.txtDetectorSize, QtCore.Qt.Key_Return)
        assert BG_COLOR_ERR in \
                        widget.txtDetectorSize.styleSheet()

    def testCheckQx_y(self, widget):
        """ Test validator for qx and qy inputs """
        widget.txtQx.clear()
        QTest.keyClicks(widget.txtQx, '0.12; 1.3')
        QTest.keyClick(widget.txtQx, QtCore.Qt.Key_Return)
        assert BG_COLOR_ERR in \
                        widget.txtQx.styleSheet()
        # put back default value
        widget.txtQx.setText('0.0')

        widget.txtQy.clear()
        QTest.keyClicks(widget.txtQy, '0.12, a')
        QTest.keyClick(widget.txtQy, QtCore.Qt.Key_Return)
        assert BG_COLOR_ERR in widget.txtQy.styleSheet()
        # put back default value
        widget.txtQy.setText('0.0')

    def testOnSelectWaveColor(self, widget):
        """ Test change of layout if type of source is TOF """
        # choose TOF
        AllItems = [widget.cbWaveColor.itemText(i)
                    for i in range(widget.cbWaveColor.count())]
        widget.cbWaveColor.setCurrentIndex(AllItems.index('TOF'))

        # call function
        widget.onSelectWaveColor()
        widget.show()

        # check that TOF is selected
        assert widget.cbWaveColor.currentText(), 'TOF'

        # check modifications of Wavelength text edit: min - max
        assert widget.txtWavelength.text() == '6.0 - 12.0'
        assert widget.txtWavelengthSpread.text() == '0.125 - 0.125'

        # check that Spectrum label and cbCustomSpectrum are visible
        assert widget.lblSpectrum.isVisible()
        assert widget.cbCustomSpectrum.isVisible()

    def testOnSelectCustomSpectrum(self, widget, mocker):
        """ Test Custom Spectrum: load file if 'Add New' """
        mocker.patch.object(QtWidgets.QFileDialog, 'getOpenFileName', return_value=("",""))
        widget.cbCustomSpectrum.setCurrentIndex(1)

        # Test the getOpenFileName() dialog called once
        assert QtWidgets.QFileDialog.getOpenFileName.called
        QtWidgets.QFileDialog.getOpenFileName.assert_called_once()

    def testHelp(self, widget, mocker):
        """ Assure help file is shown """
        # this should not rise
        widget.manager = QtWidgets.QWidget()
        mocker.patch.object(widget.manager, 'showHelp', create=True)
        widget.onHelp()
        assert widget.manager.showHelp.called_once()
        args = widget.manager.showHelp.call_args
        assert 'resolution_calculator_help.html' in args[0][0]

    def testOnReset(self, widget):
        """ Test onReset function"""
        # modify gui
        widget.txtQx.setText('33.0')
        widget.cbSource.setCurrentIndex(0)

        # check that GUI has been modified
        assert widget.cbSource.currentText() != 'Neutron'
        # apply reset
        QTest.mouseClick(widget.cmdReset, Qt.LeftButton)
        # check that we get back to the initial state
        assert widget.txtQx.text() == '0.0'
        assert widget.cbSource.currentText() == 'Neutron'

    def testOnClose(self, widget):
        """ test Closing window """
        closeButton = widget.cmdClose
        QTest.mouseClick(closeButton, Qt.LeftButton)

    def testOnCompute(self, widget, mocker):
        """ """
        mocker.patch.object(threads, 'deferToThread')
        widget.onCompute()

        # thread called
        assert threads.deferToThread.called
        assert threads.deferToThread.call_args_list[0][0][0].__name__ == 'map_wrapper'

        # the Compute button changed caption and got disabled
        assert widget.cmdCompute.text() == 'Wait...'
        assert not widget.cmdCompute.isEnabled()
