import sys
import time
import numpy
import logging
import unittest
from PyQt5 import QtGui, QtWidgets
from PyQt5 import QtCore
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt
from unittest.mock import MagicMock

from twisted.internet import threads

# from UnitTesting.TestUtils import QtSignalSpy
# from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from sas.qtgui.Calculators.ResolutionCalculatorPanel \
    import ResolutionCalculatorPanel

# from sas.qtgui.MainWindow.DataManager import DataManager
# from sas.qtgui.MainWindow.GuiManager import GuiManager
# from sas.qtgui.Utilities.GuiUtils import *


BG_COLOR_ERR = 'background-color: rgb(244, 170, 164);'

BG_COLOR_WARNING = 'background-color: rgb(244, 217, 164);'


if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)


class ResolutionCalculatorPanelTest(unittest.TestCase):
    """Test the ResolutionCalculator"""
    def setUp(self):
        """Create the ResolutionCalculator"""
        self.widget = ResolutionCalculatorPanel(None)

        # self.widget.onCompute = MagicMock()

    def tearDown(self):
        """Destroy the ResolutionCalculator"""
        self.widget.close()
        self.widget = None

    def testDefaults(self):
        """Test the GUI in its default state"""

        self.assertIsInstance(self.widget, QtWidgets.QDialog)
        self.assertEqual(self.widget.windowTitle(), "Q Resolution Estimator")
        # size
        self.assertEqual(self.widget.size().height(), 540)
        self.assertEqual(self.widget.size().width(), 876)

        # visibility
        self.assertFalse(self.widget.lblSpectrum.isVisible())
        self.assertFalse(self.widget.cbCustomSpectrum.isVisible())

        # content of line edits
        self.assertEqual(self.widget.txtDetectorPixSize.text(), '0.5, 0.5')
        self.assertEqual(self.widget.txtDetectorSize.text(), '128, 128')
        self.assertEqual(self.widget.txtSample2DetectorDistance.text(), '1000')
        self.assertEqual(self.widget.txtSampleApertureSize.text(), '1.27')
        self.assertEqual(self.widget.txtSampleOffset.text(), '0')
        self.assertEqual(self.widget.txtSource2SampleDistance.text(), '1627')
        self.assertEqual(self.widget.txtSourceApertureSize.text(), '3.81')
        self.assertEqual(self.widget.txtWavelength.text(), '6.0')
        self.assertEqual(self.widget.txtWavelengthSpread.text(), '0.125')

        self.assertEqual(self.widget.txtQx.text(), '0.0')
        self.assertEqual(self.widget.txtQy.text(), '0.0')

        self.assertEqual(self.widget.txt1DSigma.text(), '0.0008289')
        self.assertEqual(self.widget.txtSigma_lamd.text(), '3.168e-05')
        self.assertEqual(self.widget.txtSigma_x.text(), '0.0008288')
        self.assertEqual(self.widget.txtSigma_x.text(), '0.0008288')

        # items of comboboxes
        self.assertFalse(self.widget.cbCustomSpectrum.isEditable())
        self.assertEqual(self.widget.cbCustomSpectrum.currentText(), 'Flat')
        self.assertEqual(self.widget.cbCustomSpectrum.currentIndex(), 0)
        self.assertListEqual([self.widget.cbCustomSpectrum.itemText(i) for i in
                              range(self.widget.cbCustomSpectrum.count())],
                             ['Flat', 'Add New'])

        self.assertFalse(self.widget.cbSource.isEditable())
        self.assertEqual(self.widget.cbSource.count(), 6)
        self.assertEqual(self.widget.cbSource.currentText(), 'Neutron')
        self.assertListEqual([self.widget.cbSource.itemText(i) for i in
                              range(self.widget.cbSource.count())],
                             ['Alpha', 'Deutron', 'Neutron', 'Photon',
                              'Proton', 'Triton'])

        self.assertFalse(self.widget.cbWaveColor.isEditable())
        self.assertEqual(self.widget.cbWaveColor.count(), 2)
        self.assertEqual(self.widget.cbWaveColor.currentText(), 'Monochromatic')
        self.assertListEqual([self.widget.cbWaveColor.itemText(i) for i in
                              range(self.widget.cbWaveColor.count())],
                             ['Monochromatic', 'TOF'])

        # read only text edits
        self.assertTrue(self.widget.txtSigma_x.isReadOnly())
        self.assertTrue(self.widget.txtSigma_y.isReadOnly())
        self.assertTrue(self.widget.txtSigma_lamd.isReadOnly())
        self.assertTrue(self.widget.txt1DSigma.isReadOnly())

        # tooltips
        self.assertEqual(self.widget.cbSource.toolTip(),
                         "Source Selection: "
                         "Affect on the gravitational contribution.")
        self.widget.cbCustomSpectrum.toolTip(), \
        "Wavelength Spectrum: Intensity vs. wavelength."
        # print self.widget.txtDetectorPixSize.toolTip()
        self.assertEqual(self.widget.txtDetectorPixSize.toolTip(),
                         "Detector Pixel Size.")
        self.assertEqual(self.widget.txtDetectorSize.toolTip(),
                         "Number of Pixels on Detector.")
        self.assertEqual(self.widget.txtSample2DetectorDistance.toolTip(),
                         "Sample Aperture to Detector Distance.")
        self.assertEqual(self.widget.txtSampleApertureSize.toolTip(),
                         "Sample Aperture Size.")
        self.assertEqual(self.widget.txtSampleOffset.toolTip(),
                         "Sample Offset.")
        self.assertEqual(self.widget.txtSource2SampleDistance.toolTip(),
                         "Source to Sample Aperture Distance.")
        self.assertEqual(self.widget.txtSourceApertureSize.toolTip(),
                         "Source Aperture Size.")
        self.assertEqual(self.widget.txtWavelength.toolTip(),
                         "Wavelength of the Neutrons.")
        self.assertEqual(self.widget.txtWavelengthSpread.toolTip(),
                         "Wavelength Spread of Neutrons.")
        self.assertEqual(self.widget.txtQx.toolTip(), "Type the Qx value.")
        self.assertEqual(self.widget.txtQy.toolTip(), "Type the Qy value.")
        self.assertEqual(self.widget.txt1DSigma.toolTip(),
                         "Resolution in 1-dimension (for 1D data).")
        self.assertEqual(self.widget.txtSigma_lamd.toolTip(),
                         "The wavelength contribution in the radial direction."
                         " Note: The phi component is always zero.")
        self.assertEqual(self.widget.txtSigma_x.toolTip(),
                         "The x component of the geometric resolution, "
                         "excluding sigma_lamda.")
        self.assertEqual(self.widget.txtSigma_y.toolTip(),
                         "The y component of the geometric resolution, "
                         "excluding sigma_lamda.")

    def testFormatNumber(self):
        self.assertEqual(self.widget.formatNumber('  7.123456  '), '7.123')

    def testCheckWavelength(self):
        """ Test validator for Wavelength text edit"""
        self.widget.txtWavelength.clear()
        # Enter invalid input for Monochromatic spectrum
        # check that background becomes red and Compute button is disabled
        QTest.keyClicks(self.widget.txtWavelength, 'vcv ')
        QTest.keyClick(self.widget.txtWavelength, QtCore.Qt.Key_Return)
        self.assertIn(BG_COLOR_ERR, self.widget.txtWavelength.styleSheet())
        self.assertFalse(self.widget.cmdCompute.isEnabled())

        # Enter invalid input for TOF spectrum
        # check that background becomes red and Compute button is disabled
        self.widget.cbWaveColor.setCurrentIndex(1)

        self.widget.txtWavelength.clear()
        QTest.keyClicks(self.widget.txtWavelength, '4')
        QTest.keyClick(self.widget.txtWavelength, QtCore.Qt.Key_Return)
        self.assertIn(BG_COLOR_ERR, self.widget.txtWavelength.styleSheet())
        self.assertFalse(self.widget.cmdCompute.isEnabled())

    def testCheckWavelengthSpread(self):
        """ Test validator for WavelengthSpread """
        self.widget.txtWavelengthSpread.clear()
        QTest.keyClicks(self.widget.txtWavelengthSpread, '0.12; 1.3')
        QTest.keyClick(self.widget.txtWavelengthSpread, QtCore.Qt.Key_Return)
        self.assertIn(BG_COLOR_ERR,
                      self.widget.txtWavelengthSpread.styleSheet())

    def testCheckPixels(self):
        """ Test validator for pixel size and number """
        self.widget.txtDetectorPixSize.clear()
        QTest.keyClicks(self.widget.txtDetectorPixSize, '0.12; 1.3')
        QTest.keyClick(self.widget.txtDetectorPixSize, QtCore.Qt.Key_Return)
        self.assertIn(BG_COLOR_ERR,
                      self.widget.txtDetectorPixSize.styleSheet())

        self.widget.txtDetectorSize.clear()
        QTest.keyClicks(self.widget.txtDetectorSize, '0.12')
        QTest.keyClick(self.widget.txtDetectorSize, QtCore.Qt.Key_Return)
        self.assertIn(BG_COLOR_ERR,
                      self.widget.txtDetectorSize.styleSheet())

    def testCheckQx_y(self):
        """ Test validator for qx and qy inputs """
        self.widget.txtQx.clear()
        QTest.keyClicks(self.widget.txtQx, '0.12; 1.3')
        QTest.keyClick(self.widget.txtQx, QtCore.Qt.Key_Return)
        self.assertIn(BG_COLOR_ERR,
                      self.widget.txtQx.styleSheet())
        # put back default value
        self.widget.txtQx.setText('0.0')

        self.widget.txtQy.clear()
        QTest.keyClicks(self.widget.txtQy, '0.12, a')
        QTest.keyClick(self.widget.txtQy, QtCore.Qt.Key_Return)
        self.assertIn(BG_COLOR_ERR, self.widget.txtQy.styleSheet())
        # put back default value
        self.widget.txtQy.setText('0.0')

    def testOnSelectWaveColor(self):
        """ Test change of layout if type of source is TOF """
        # choose TOF
        AllItems = [self.widget.cbWaveColor.itemText(i)
                    for i in range(self.widget.cbWaveColor.count())]
        self.widget.cbWaveColor.setCurrentIndex(AllItems.index('TOF'))

        # call function
        self.widget.onSelectWaveColor()
        self.widget.show()

        # check that TOF is selected
        self.assertTrue(self.widget.cbWaveColor.currentText(), 'TOF')

        # check modifications of Wavelength text edit: min - max
        self.assertEqual(self.widget.txtWavelength.text(), '6.0 - 12.0')
        self.assertEqual(self.widget.txtWavelengthSpread.text(), '0.125 - 0.125')

        # check that Spectrum label and cbCustomSpectrum are visible
        self.assertTrue(self.widget.lblSpectrum.isVisible())
        self.assertTrue(self.widget.cbCustomSpectrum.isVisible())

    def testOnSelectCustomSpectrum(self):
        """ Test Custom Spectrum: load file if 'Add New' """
        QtWidgets.QFileDialog.getOpenFileName = MagicMock(return_value=("",""))
        self.widget.cbCustomSpectrum.setCurrentIndex(1)

        # Test the getOpenFileName() dialog called once
        self.assertTrue(QtWidgets.QFileDialog.getOpenFileName.called)
        QtWidgets.QFileDialog.getOpenFileName.assert_called_once()

    def testHelp(self):
        """ Assure help file is shown """
        # this should not rise
        self.widget.manager = QtWidgets.QWidget()
        self.widget.manager.showHelp = MagicMock()
        self.widget.onHelp()
        self.assertTrue(self.widget.manager.showHelp.called_once())
        args = self.widget.manager.showHelp.call_args
        self.assertIn('resolution_calculator_help.html', args[0][0])

    def testOnReset(self):
        """ Test onReset function"""
        # modify gui
        self.widget.txtQx.setText('33.0')
        self.widget.cbSource.setCurrentIndex(0)

        # check that GUI has been modified
        self.assertNotEqual(self.widget.cbSource.currentText(), 'Neutron')
        # apply reset
        QTest.mouseClick(self.widget.cmdReset, Qt.LeftButton)
        # check that we get back to the initial state
        self.assertEqual(self.widget.txtQx.text(), '0.0')
        self.assertEqual(self.widget.cbSource.currentText(), 'Neutron')

    def testOnClose(self):
        """ test Closing window """
        closeButton = self.widget.cmdClose
        QTest.mouseClick(closeButton, Qt.LeftButton)

    def testOnCompute(self):
        """ """
        threads.deferToThread = MagicMock()
        self.widget.onCompute()

        # thread called
        self.assertTrue(threads.deferToThread.called)
        self.assertEqual(threads.deferToThread.call_args_list[0][0][0].__name__, 'map_wrapper')

        # the Compute button changed caption and got disabled
        self.assertEqual(self.widget.cmdCompute.text(), 'Wait...')
        self.assertFalse(self.widget.cmdCompute.isEnabled())


if __name__ == "__main__":
    unittest.main()
