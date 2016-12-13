import sys
import unittest
from PyQt4 import QtGui
from PyQt4.QtTest import QTest
from PyQt4.QtCore import Qt
from mock import MagicMock

# set up import paths
import path_prepare

from SlitSizeCalculator import SlitSizeCalculator
from sas.sascalc.calculator.slit_length_calculator import SlitlengthCalculator as calculator
from sas.sascalc.dataloader.loader import Loader

app = QtGui.QApplication(sys.argv)


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
        self.assertIsInstance(self.widget, QtGui.QWidget)
        self.assertEqual(self.widget.windowTitle(), "Slit Size Calculator")
        self.assertEqual(self.widget.sizePolicy().Policy(), QtGui.QSizePolicy.Fixed)

    def testHelp(self):
        """ Assure help file is shown """

        # this should not rise
        self.widget.onHelp()

    def testComputeSlit(self):
        """ User entered compound calculations and subsequent reset"""

        filename = "beam_profile.DAT"
        loader = Loader()
        data = loader.load(filename)
        # Push Compute with the left mouse button
        cal = calculator()
        cal.set_data(x = data.x, y = data.y)
        slitlength = cal.calculate_slit_length()

        # The value "5.5858" was obtained by manual calculation.
        # It turns out our slit length is FWHM/2
        self.assertAlmostEqual(slitlength,5.5858/2, 3)

    def testBrowseButton(self):
        browseButton = self.widget.browseButton

        filename = "beam_profile.DAT"

        # Return no files.
        QtGui.QFileDialog.getOpenFileName = MagicMock(return_value=None)

        # Click on the Browse button
        QTest.mouseClick(browseButton, Qt.LeftButton)

        # Test the getOpenFileName() dialog called once
        self.assertTrue(QtGui.QFileDialog.getOpenFileName.called)
        QtGui.QFileDialog.getOpenFileName.assert_called_once()

        # Now, return a single file
        QtGui.QFileDialog.getOpenFileName = MagicMock(return_value=filename)

        # Click on the Load button
        QTest.mouseClick(browseButton, Qt.LeftButton)
        QtGui.qApp.processEvents()

        # Test the getOpenFileName() dialog called once
        self.assertTrue(QtGui.QFileDialog.getOpenFileName.called)
        QtGui.QFileDialog.getOpenFileName.assert_called_once()

    # def testDataEntryNumbers(self):
    #     """ User entered compound calculations and subsequent reset"""
    #
    #     self.widget.data_file.clear()
    #     self.widget.data_file.insert("beam profile.DAT")
    #     #
    #     # Push Compute with the left mouse button
    #     computeButton = self.widget.computeButton
    #     QTest.mouseClick(computeButton, Qt.LeftButton)
    #     self.assertEqual(self.widget.lengthscale_out.text(), '6.283')
    #
    #
    # def testComplexEntryLetters(self):
    #     """ User entered compound calculations and subsequent reset"""
    #
    #     self.widget.deltaq_in.insert("xyz")
    #
    #     # Push Compute with the left mouse button
    #     computeButton = self.widget.computeButton
    #     QTest.mouseClick(computeButton, Qt.LeftButton)
    #     self.assertEqual(self.widget.lengthscale_out.text(), '')

if __name__ == "__main__":
    unittest.main()
