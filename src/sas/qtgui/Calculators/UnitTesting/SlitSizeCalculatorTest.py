import sys
import unittest
import logging

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt
from unittest.mock import MagicMock

# set up import paths
import sas.qtgui.path_prepare

from sas.qtgui.Calculators.SlitSizeCalculator import SlitSizeCalculator
from sas.sascalc.dataloader.loader import Loader

if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)


class SlitSizeCalculatorTest(unittest.TestCase):
    """Test the SlitSizeCalculator"""
    def setUp(self):
        """Create the SlitSizeCalculator"""
        self.widget = SlitSizeCalculator(None)

    def tearDown(self):
        """Destroy the SlitSizeCalculator"""
        self.widget.close()
        self.widget = None

    def testDefaults(self):
        """Test the GUI in its default state"""
        self.assertIsInstance(self.widget, QtWidgets.QWidget)
        self.assertEqual(self.widget.windowTitle(), "Slit Size Calculator")
        self.assertEqual(self.widget.sizePolicy().Policy(), QtWidgets.QSizePolicy.Fixed)

    def testHelp(self):
        """ Assure help file is shown """
        self.widget._parent = QtWidgets.QWidget()
        self.widget._parent.showHelp = MagicMock()
        self.widget.onHelp()
        self.assertTrue(self.widget._parent.showHelp.called_once())
        args = self.widget._parent.showHelp.call_args
        self.assertIn('slit_calculator_help.html', args[0][0])

    def testBrowseButton(self):
        browseButton = self.widget.browseButton

        filename = "beam_profile.DAT"

        # Return no files.
        QtWidgets.QFileDialog.getOpenFileName = MagicMock(return_value=('',''))

        # Click on the Browse button
        QTest.mouseClick(browseButton, Qt.LeftButton)

        # Test the getOpenFileName() dialog called once
        self.assertTrue(QtWidgets.QFileDialog.getOpenFileName.called)
        QtWidgets.QFileDialog.getOpenFileName.assert_called_once()

        # Now, return a single file
        QtWidgets.QFileDialog.getOpenFileName = MagicMock(return_value=(filename,''))

        # Click on the Load button
        QTest.mouseClick(browseButton, Qt.LeftButton)
        QtWidgets.qApp.processEvents()

        # Test the getOpenFileName() dialog called once
        self.assertTrue(QtWidgets.QFileDialog.getOpenFileName.called)
        QtWidgets.QFileDialog.getOpenFileName.assert_called_once()


    def notestCalculateSlitSize(self):
        """ Test slit size calculated value """

        filename = "beam_profile.DAT"
        loader = Loader()
        data = loader.load(filename)[0]

        self.widget.calculateSlitSize(data)
        # The value "5.5858" was obtained by manual calculation.
        # It turns out our slit length is FWHM/2
        self.assertAlmostEqual(float(self.widget.slit_length_out.text()), 5.5858/2, 3)

    def testWrongInput(self):
        """ Test on wrong input data """

        filename = "Dec07031.ASC"
        loader = Loader()
        data = loader.load(filename)[0]

        logging.error = MagicMock()

        self.widget.calculateSlitSize(data)

        self.assertTrue(logging.error.called_once())

        data = None
        self.widget.calculateSlitSize(data)
        self.assertTrue(logging.error.call_count == 2)


if __name__ == "__main__":
    unittest.main()
