import sys
import unittest
import numpy

from PyQt5 import QtGui, QtWidgets
from unittest.mock import MagicMock
import matplotlib as mpl

# set up import paths
import path_prepare

from sas.qtgui.Plotting.PlotterData import Data2D
import sas.qtgui.Plotting.Plotter2D as Plotter2D
from UnitTesting.TestUtils import WarningTestNotImplemented
from UnitTesting.TestUtils import QtSignalSpy

# Local
from sas.qtgui.Plotting.ColorMap import ColorMap

if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)

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
        self.assertIsInstance(self.widget, QtWidgets.QDialog)

        self.assertEqual(self.widget._cmap_orig, "jet")
        self.assertEqual(len(self.widget.all_maps), 160)
        self.assertEqual(len(self.widget.maps), 80)
        self.assertEqual(len(self.widget.rmaps), 80)

        self.assertEqual(self.widget.lblWidth.text(), "0")
        self.assertEqual(self.widget.lblHeight.text(), "0")
        self.assertEqual(self.widget.lblQmax.text(), "15.8")
        self.assertEqual(self.widget.lblStopRadius.text(), "-1")
        self.assertFalse(self.widget.chkReverse.isChecked())
        self.assertEqual(self.widget.cbColorMap.count(), 80)
        self.assertEqual(self.widget.cbColorMap.currentIndex(), 64)

        # validators
        self.assertIsInstance(self.widget.txtMinAmplitude.validator(), QtGui.QDoubleValidator)
        self.assertIsInstance(self.widget.txtMaxAmplitude.validator(), QtGui.QDoubleValidator)

        # Ranges
        self.assertEqual(self.widget.txtMinAmplitude.text(), "0")
        self.assertEqual(self.widget.txtMaxAmplitude.text(), "100")
        self.assertIsInstance(self.widget.slider, QtWidgets.QSlider)

    def testOnReset(self):
        '''Check the dialog reset function'''
        # Set some controls to non-default state
        self.widget.cbColorMap.setCurrentIndex(20)
        self.widget.chkReverse.setChecked(True)
        self.widget.txtMinAmplitude.setText("20.0")

        # Reset the widget state
        self.widget.onReset()

        # Assure things went back to default
        self.assertEqual(self.widget.cbColorMap.currentIndex(), 20)
        self.assertFalse(self.widget.chkReverse.isChecked())
        self.assertEqual(self.widget.txtMinAmplitude.text(), "0")

    def testOnApply(self):
        '''Check the dialog apply function'''
        # Set some controls to non-default state
        self.widget.show()
        self.widget.cbColorMap.setCurrentIndex(20) # PuRd_r
        self.widget.chkReverse.setChecked(True)
        self.widget.txtMinAmplitude.setText("20.0")

        spy_apply = QtSignalSpy(self.widget, self.widget.apply_signal)
        # Reset the widget state
        self.widget.onApply()

        # Assure the widget is still up and the signal was sent.
        self.assertTrue(self.widget.isVisible())
        self.assertEqual(spy_apply.count(), 1)
        self.assertIn('PuRd_r', spy_apply.called()[0]['args'][1])

    def testInitMapCombobox(self):
        '''Test the combo box initializer'''
        # Set a color map from the direct list
        self.widget._cmap = "gnuplot"
        self.widget.initMapCombobox()

        # Check the combobox
        self.assertEqual(self.widget.cbColorMap.currentIndex(), 59)
        self.assertFalse(self.widget.chkReverse.isChecked())

        # Set a reversed value
        self.widget._cmap = "hot_r"
        self.widget.initMapCombobox()
        # Check the combobox
        self.assertEqual(self.widget.cbColorMap.currentIndex(), 60)
        self.assertTrue(self.widget.chkReverse.isChecked())

    def testInitRangeSlider(self):
        '''Test the range slider initializer'''
        # Set a color map from the direct list
        self.widget._cmap = "gnuplot"
        self.widget.initRangeSlider()

        # Check the values
        self.assertEqual(self.widget.slider.minimum(), 0)
        self.assertEqual(self.widget.slider.maximum(), 100)
        self.assertEqual(self.widget.slider.orientation(), 1)

        # Emit new low value
        self.widget.slider.lowValueChanged.emit(5)
        # Assure the widget received changes
        self.assertEqual(self.widget.txtMinAmplitude.text(), "5")

        # Emit new high value
        self.widget.slider.highValueChanged.emit(45)
        # Assure the widget received changes
        self.assertEqual(self.widget.txtMinAmplitude.text(), "45")

    def testOnMapIndexChange(self):
        '''Test the response to the combo box index change'''

        self.widget.canvas.draw = MagicMock()
        mpl.colorbar.ColorbarBase = MagicMock()

        # simulate index change
        self.widget.cbColorMap.setCurrentIndex(1)

        # Check that draw() got called
        self.assertTrue(self.widget.canvas.draw.called)
        self.assertTrue(mpl.colorbar.ColorbarBase.called)

    def testOnColorMapReversed(self):
        '''Test reversing the color map functionality'''
        # Check the defaults
        self.assertEqual(self.widget._cmap, "jet")
        self.widget.cbColorMap.addItems = MagicMock()

        # Reverse the choice
        self.widget.onColorMapReversed(True)

        # check the behaviour
        self.assertEqual(self.widget._cmap, "jet_r")
        self.assertTrue(self.widget.cbColorMap.addItems.called)

    def testOnAmplitudeChange(self):
        '''Check the callback method for responding to changes in textboxes'''
        self.widget.canvas.draw = MagicMock()
        mpl.colors.Normalize = MagicMock()
        mpl.colorbar.ColorbarBase = MagicMock()

        self.widget.vmin = 0.0
        self.widget.vmax = 100.0

        # good values in fields
        self.widget.txtMinAmplitude.setText("1.0")
        self.widget.txtMaxAmplitude.setText("10.0")

        self.widget.onAmplitudeChange()

        # Check the arguments to Normalize
        mpl.colors.Normalize.assert_called_with(vmin=1.0, vmax=10.0)
        self.assertTrue(self.widget.canvas.draw.called)

        # Bad values in fields
        self.widget.txtMinAmplitude.setText("cake")
        self.widget.txtMaxAmplitude.setText("more cake")

        self.widget.onAmplitudeChange()

        # Check the arguments to Normalize - should be defaults
        mpl.colors.Normalize.assert_called_with(vmin=0.0, vmax=100.0)
        self.assertTrue(self.widget.canvas.draw.called)


if __name__ == "__main__":
    unittest.main()
