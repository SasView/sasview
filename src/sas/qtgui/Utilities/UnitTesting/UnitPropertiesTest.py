import unittest

from PyQt5.QtWidgets import QWidget

from sas.sascalc.dataloader.data_info import set_loaded_units

from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Utilities.UnitChange import UnitChange


class UnitPropertiesTest(unittest.TestCase):

    def setUp(self):
        """
        Prepare the unit test window
        """
        self.dummy_parent = QWidget()
        self.data = [Data1D(x=[1.0, 2.0, 3.0], y=[10.0, 11.0, 12.0])]

    def commonTests(self, widget=None):
        if not widget:
            widget = self.widget
        x_units_loaded = [widget.cbX.itemText(i) for i in range(widget.cbX.count())]
        y_units_loaded = [widget.cbY.itemText(i) for i in range(widget.cbY.count())]
        x_units_method = widget.getAllowedQUnits()
        y_units_method = widget.getAllowedIUnits()
        # Check the number of possible units is > 0
        self.assertNotEqual(len(x_units_loaded), 0)
        self.assertNotEqual(len(y_units_loaded), 0)
        # Check the number in the GUI and the number returned by the method are equal
        self.assertEqual(len(x_units_method), len(x_units_loaded))
        self.assertEqual(len(y_units_method), len(y_units_loaded))

    def checkRealUnits(self, widget=None, x_unit=None, y_unit=None):
        if not widget:
            widget = self.widget
        if x_unit:
            x_units = widget.getAllowedQUnits()
            self.assertIn(x_unit, x_units)
        if y_unit:
            y_units = widget.getAllowedIUnits()
            self.assertIn(y_unit, y_units)

    def testDefaults(self):
        # Load no data so everything is empty
        self.widget = UnitChange(parent=self.dummy_parent)
        self.assertEqual(self.widget.windowTitle(), "Unit Conversion Tool")
        # Assure X and Y combo boxes exist and are empty
        self.assertTrue(hasattr(self.widget, "cbX"))
        self.assertEqual(self.widget.cbX.objectName(), 'cbX')
        self.assertEqual(len([self.widget.cbX.itemText(i) for i in range(self.widget.cbX.count())]), 0)
        self.assertTrue(hasattr(self.widget, "cbY"))
        self.assertEqual(self.widget.cbY.objectName(), 'cbY')
        self.assertEqual(len([self.widget.cbY.itemText(i) for i in range(self.widget.cbY.count())]), 0)
        # Assure Labels are X and Y
        self.assertEqual(self.widget.label.text(), 'Q Units')
        self.assertEqual(self.widget.label_2.text(), 'Intensity Units')
        # Check the buttons exist
        okWidget = self.widget.buttonBox.button(self.widget.buttonBox.Ok)
        cancelWidget = self.widget.buttonBox.button(self.widget.buttonBox.Cancel)
        self.assertTrue(okWidget is not None)
        self.assertTrue(cancelWidget is not None)

    def testWithOneData(self):
        # Create a unit change dialog with a single data set loaded
        self.widget = UnitChange(parent=self.dummy_parent, data=self.data)
        self.commonTests()
        # Check for real units - both lists should be the same
        self.checkRealUnits(self.widget, 'None', 'Unk')

    def testWithTwoData(self):
        # Create a unit change dialog with two data sets loaded
        data = [self.data[0], self.data[0]]
        self.widget = UnitChange(parent=self.dummy_parent, data=self.data)
        self.widget_multi = UnitChange(parent=self.dummy_parent, data=data)
        x_units_loaded = [self.widget_multi.cbX.itemText(i) for i in range(self.widget_multi.cbX.count())]
        y_units_loaded = [self.widget_multi.cbY.itemText(i) for i in range(self.widget_multi.cbY.count())]
        self.commonTests()
        self.commonTests(self.widget_multi)
        # Compare single data set to multiple datas - should only use the first data to populate the dropdowns
        x_units_method_single = self.widget.getAllowedQUnits()
        y_units_method_single = self.widget.getAllowedIUnits()
        self.assertEqual(len(x_units_loaded), len(x_units_method_single))
        self.assertEqual(len(y_units_loaded), len(y_units_method_single))
        # Check for real units - both lists should be the same
        self.checkRealUnits(self.widget, 'cts', 'a.u.')

    def testWithRealUnits(self):
        set_loaded_units(self.data[0], 'x', '1/A')
        set_loaded_units(self.data[0], 'y', '1/cm')
        # Create a unit change dialog with a single data set loaded
        self.widget = UnitChange(parent=self.dummy_parent, data=self.data)
        self.commonTests()
        # Check for real units - both lists should be the same
        self.checkRealUnits(self.widget, 'um^{-1}', 'A^{-1}')
