import sys
import unittest
import webbrowser
from time import sleep

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtTest import QTest
from PyQt5 import QtCore

import sas.qtgui.path_prepare
from sas.qtgui.Perspectives.Corfunc.CorfuncPerspective import CorfuncWindow
from sas.sascalc.dataloader.loader import Loader

from sas.qtgui.MainWindow.DataManager import DataManager
import sas.qtgui.Utilities.LocalConfig
import sas.qtgui.Utilities.GuiUtils as GuiUtils

if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)


class CorfuncTest(unittest.TestCase):
    '''Test the Corfunc Interface'''
    def setUp(self):
        '''Create the CorfuncWindow'''
        self.widget = CorfuncWindow(None)

    def tearDown(self):
        '''Destroy the CorfuncWindow'''
        self.widget.close()
        self.widget = None

    def testDefaults(self):
        '''Test the GUI in its default state'''
        self.assertIsInstance(self.widget, QtWidgets.QWidget)
        self.assertEqual(self.widget.windowTitle(), "Corfunc Perspective")
        self.assertEqual(self.widget.model.columnCount(), 1)
        self.assertEqual(self.widget.model.rowCount(), 15)

class CorfuncDataTest(unittest.TestCase):
    '''Test the actual Corfunc Usase'''
    def setUp(self):
        '''Create a CorfuncWindow and populate it with data'''
        self.widget = CorfuncWindow(None)
        path = "../test/corfunc/test/98929.txt"
        f = Loader().load(path)
        manager = DataManager()
        new_data = manager.create_gui_data(f[0], path)
        output = {new_data.id: new_data}
        item = QtGui.QStandardItem(True)
        object_item = QtGui.QStandardItem()
        object_item.setData(QtCore.QVariant(new_data))
        item.setChild(0, object_item)
        self.widget.setData([item])

    def tearDown(self):
        '''Destroy the CorfuncWindow'''
        self.widget.close()
        self.widget = None

    def testProcess(self):
        """Test the full analysis path"""
        self.assertEqual(float(self.widget.bg.text()), 0.0)

        self.widget.qMin.setValue(0.01)
        self.widget.qMax1.setValue(0.20)
        self.widget.qMax2.setValue(0.22)
        self.widget.transformCombo.setCurrentIndex(0)

        self.widget.calculateBgBtn.click()
        self.assertTrue(float(self.widget.bg.text()) > 0.2)

        self.widget.extrapolateBtn.click()
        self.assertTrue(float(self.widget.guinierA.text()) > 1)
        self.assertTrue(float(self.widget.guinierB.text()) < -10000)
        self.assertTrue(float(self.widget.porodK.text()) > 10)
        self.assertTrue(float(self.widget.porodSigma.text()) > 10)

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
