import sys
import unittest
from PyQt4 import QtGui
from PyQt4.QtTest import QTest
from PyQt4.QtCore import Qt
from mock import MagicMock

# set up import paths
import path_prepare

from SlitSizeCalculator import SlitSizeCalculator
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


    def testCalculateSlitSize(self):
        """ Test slit size calculated value """

        filename = "beam_profile.DAT"
        loader = Loader()
        data = loader.load(filename)

        self.widget.calculateSlitSize(data)
        # The value "5.5858" was obtained by manual calculation.
        # It turns out our slit length is FWHM/2
        self.assertAlmostEqual(float(self.widget.slit_length_out.text()), 5.5858/2, 3)

    def testWrongInput(self):
        """ Test on wrong input data """

        filename = "Dec07031.ASC"
        loader = Loader()
        data = loader.load(filename)
        self.assertRaisesRegexp(RuntimeError,
                                "Slit Length cannot be computed for 2D Data",
                                self.widget.calculateSlitSize, data)

        filename = "empty_file.txt"
        loader = Loader()
        data = loader.load(filename)
        self.assertRaisesRegexp(RuntimeError,
                                "ERROR: Data hasn't been loaded correctly",
                                self.widget.calculateSlitSize, data)

        data = None
        self.assertRaisesRegexp(RuntimeError,
                                "ERROR: Data hasn't been loaded correctly",
                                self.widget.calculateSlitSize, data)


if __name__ == "__main__":
    unittest.main()
