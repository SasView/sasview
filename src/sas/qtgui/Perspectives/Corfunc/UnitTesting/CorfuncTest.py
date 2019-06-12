import os
import sys

import unittest
from unittest.mock import MagicMock

from PyQt5 import QtGui, QtWidgets
from PyQt5 import QtCore
from PyQt5.QtTest import QTest

from sas.qtgui.Perspectives.Corfunc.CorfuncPerspective import CorfuncWindow
from sas.sascalc.dataloader.loader import Loader
from sas.qtgui.MainWindow.DataManager import DataManager
import sas.qtgui.Utilities.GuiUtils as GuiUtils


if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)


class CorfuncTest(unittest.TestCase):
    '''Test the Corfunc Interface'''
    def setUp(self):

        '''Create the CorfuncWindow'''
        class MainWindow(object):
            def __init__(self):
                self.model = QtGui.QStandardItemModel()

        class dummy_manager(object):
            def __init__(self):
                self.filesWidget = MainWindow()

            def communicator(self):
                return GuiUtils.Communicate()

            def communicate(self):
                return GuiUtils.Communicate()

        self.widget = CorfuncWindow(dummy_manager())

    def tearDown(self):
        '''Destroy the CorfuncWindow'''
        self.widget.close()
        self.widget = None

    def testDefaults(self):
        '''Test the GUI in its default state'''
        self.assertIsInstance(self.widget, QtWidgets.QWidget)
        self.assertEqual(self.widget.windowTitle(), "Corfunc Perspective")
        self.assertEqual(self.widget.model.columnCount(), 1)
        self.assertEqual(self.widget.model.rowCount(), 16)

    def testOnCalculate(self):
        """ Test onCompute function """
        self.widget.calculate_background = MagicMock()
        self.widget.cmdCalculateBg.setEnabled(True)
        QTest.mouseClick(self.widget.cmdCalculateBg, QtCore.Qt.LeftButton)
        self.assertTrue(self.widget.calculate_background.called_once())

    def testProcess(self):
        """Test the full analysis path"""

        filename = os.path.join("UnitTesting", "ISIS_98929.txt")
        try:
            os.stat(filename)
        except OSError:
            self.assertTrue(False, "ISIS_98929.txt does not exist")
        f = Loader().load(filename)
        QtWidgets.QFileDialog.getOpenFileName = MagicMock(return_value=(filename, ''))

        #self.assertEqual(self.widget.txtFilename.text(), filename)

        self.assertEqual(float(self.widget.txtBackground.text()), 0.0)

        self.widget.txtLowerQMin.setText("0.01")
        self.widget.txtLowerQMax.setText("0.20")
        self.widget.txtUpperQMax.setText("0.22")

        QTest.mouseClick(self.widget.cmdCalculateBg, QtCore.Qt.LeftButton)


        #TODO: All the asserts when Calculate is clicked and file properly loaded
        #self.assertTrue(float(self.widget.txtBackground.text()) > 0.2)

        #self.widget.extrapolateBtn.click()
        #self.assertTrue(float(self.widget.txtGuinierA.text()) > 1)
        #self.assertTrue(float(self.widget.txtGuinierB.text()) < -10000)
        #self.assertTrue(float(self.widget.txtPorodK.text()) > 10)
        #self.assertTrue(float(self.widget.txtPorodSigma.text()) > 10)

        #################################################
        # The testing framework does not seem to handle
        # multi-threaded Qt.  Signals emitted from threads
        # are not detected when run in the unittest, even
        # though they ARE handled in the actual application.
        #################################################
        # sleep(1)
        # self.widget.transformBtn.click()
        # while float(self.widget.longPeriod.text()) == 0.0:
        #     print("Waiting")
        #     sleep(1)
        # self.assertTrue(float(self.widget.longPeriod.text()) > 10)
        # self.assertTrue(float(self.widget.polydisp.text()) > 0)
        # self.assertTrue(float(self.widget.localCrystal.text()) > 0)
        # self.assertTrue(float(self.widget.longPeriod.text()) >
        #                 float(self.widget.avgHardBlock.text()) > 0)
        # self.assertTrue(float(self.widget.longPeriod.text()) >
        #                 float(self.widget.avgIntThick.text()) > 0)
        # self.assertTrue(float(self.widget.longPeriod.text()) >
        #                 float(self.widget.avgCoreThick.text()) > 0)


if __name__ == "__main__":
    unittest.main()
