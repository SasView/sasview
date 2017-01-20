import sys
import unittest
import numpy

from PyQt4 import QtGui
from mock import MagicMock

# set up import paths
import path_prepare

from sas.sasgui.guiframe.dataFitting import Data2D
import sas.qtgui.Plotter2D as Plotter2D
from UnitTesting.TestUtils import WarningTestNotImplemented

# Local
from sas.qtgui.ColorMap import ColorMap

app = QtGui.QApplication(sys.argv)

class ColorMapTest(unittest.TestCase):
    '''Test the ColorMap'''
    def setUp(self):
        '''Create the ColorMap'''
        self.plotter = Plotter2D.Plotter2D(None, quickplot=True)

        self.data = Data2D(image=[0.1]*4,
                           qx_data=[1.0, 2.0, 3.0, 4.0],
                           qy_data=[10.0, 11.0, 12.0, 13.0],
                           dqx_data=[0.1, 0.2, 0.3, 0.4],
                           dqy_data=[0.1, 0.2, 0.3, 0.4],
                           q_data=[1,2,3,4],
                           xmin=-1.0, xmax=5.0,
                           ymin=-1.0, ymax=15.0,
                           zmin=-1.0, zmax=20.0)

        self.data.title="Test data"
        self.data.id = 1
        self.widget = ColorMap(parent=self.plotter, data=self.data)

    def tearDown(self):
        '''Destroy the GUI'''
        self.widget.close()
        self.widget = None

    def testDefaults(self):
        '''Test the GUI in its default state'''
        self.assertIsInstance(self.widget, QtGui.QDialog)

        WarningTestNotImplemented()

    def testOnReset(self):
        '''Check the dialog reset function'''
        WarningTestNotImplemented()

    def testInitDetectorData(self):
        '''Check the detector data generator'''
        # possibly to fold into testDefaults
        WarningTestNotImplemented()

    def testInitMapCombobox(self):
        '''Test the combo box initializer'''
        # possible to fold into testDefaults
        WarningTestNotImplemented()

    def testOnMapIndexChange(self):
        '''Test the response to the combo box index change'''
        WarningTestNotImplemented()

    def testRedrawColorBar(self):
        '''Test the color bar redrawing'''
        WarningTestNotImplemented()

    def testOnColorMapReversed(self):
        '''Test reversing the color map functionality'''
        WarningTestNotImplemented()

    def testOnAmplitudeChange(self):
        '''Check the callback method for responding to changes in textboxes'''
        WarningTestNotImplemented()


if __name__ == "__main__":
    unittest.main()
