import unittest

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget
from PyQt5.QtTest import QTest

from sas import get_custom_config
from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Utilities.PreferencesPanel import *


class PreferencesPanelTest(unittest.TestCase):

    def setUp(self):
        """
        Prepare the unit test window
        """
        class DummyClass():
            def __init__(self):
                pass

            def writeCustomConfig(self, config):
                """
                Write custom configuration
                """
                path = './custom_config.py'
                # Just clobber the file - we already have its content read in
                with open(path, 'w') as out_f:
                    out_f.write("#Application appearance custom configuration\n")
                    for key, item in config.__dict__.items():
                        if key[:2] == "__":
                            continue
                        if isinstance(item, str):
                            item = '"' + item + '"'
                        out_f.write("%s = %s\n" % (key, str(item)))

        self.dummy_parent = QWidget()
        self.dummy_parent.guiManager = DummyClass()
        self.pref_panel = PreferencesPanel(self.dummy_parent)
        self.custom_config = get_custom_config()
        self.data = [Data1D(x=[1.0, 2.0, 3.0], y=[10.0, 11.0, 12.0])]

    def tearDown(self) -> None:
        """Close the panel and reset class variables"""
        self.dummy_parent = None
        self.pref_panel.close()
        self.pref_panel = None

    def testDefaults(self):
        """Test the freshly-opened panel with no previous changes made"""
        self.warning = None
        # Some check boxes should be prechecked
        self.assertTrue(self.pref_panel.checkBoxPlotIAsLoaded.isChecked())
        self.assertTrue(self.pref_panel.checkBoxPlotQAsLoaded.isChecked())
        # Some checkboxes should not be checked
        self.assertFalse(self.pref_panel.checkBoxLoadIOverride.isChecked())
        self.assertFalse(self.pref_panel.checkBoxLoadQOverride.isChecked())
        # Check default values are set when new window opens
        self.assertEqual(self.pref_panel.cbLoadIUnitType.currentText(), DEFAULT_I_CATEGORY)
        self.assertEqual(self.pref_panel.cbLoadQUnitType.currentText(), DEFAULT_Q_CATEGORY)
        self.assertEqual(self.pref_panel.cbLoadIUnitSelector.currentText(), DEFAULT_I_UNIT)
        self.assertEqual(self.pref_panel.cbLoadQUnitSelector.currentText(), DEFAULT_Q_UNIT)
        self.assertEqual(self.pref_panel.cbPlotIAbs.currentText(), DEFAULT_I_UNIT)
        self.assertEqual(self.pref_panel.cbPlotIAbsSquared.currentText(), DEFAULT_I_ABS2_UNIT)
        self.assertEqual(self.pref_panel.cbPlotISesans.currentText(), DEFAULT_I_SESANS_UNIT)
        # Check number of widgets equals the number of list items and the list is set to the first element
        self.assertEqual(self.pref_panel.stackedWidget.count(), self.pref_panel.listWidget.count())
        self.assertEqual(0, self.pref_panel.stackedWidget.currentIndex())
        # Test default enabled state of widgets
        enabled_on_load = [self.pref_panel.checkBoxPlotIAsLoaded, self.pref_panel.checkBoxPlotQAsLoaded,
                           self.pref_panel.checkBoxLoadIOverride, self.pref_panel.checkBoxLoadQOverride,
                           self.pref_panel.cbLoadIUnitType, self.pref_panel.cbLoadIUnitType,
                           self.pref_panel.cbLoadIUnitSelector, self.pref_panel.cbLoadQUnitSelector]
        disabled_on_load = [self.pref_panel.cbPlotIAbs, self.pref_panel.cbPlotIArbitrary,
                            self.pref_panel.cbPlotISesans, self.pref_panel.cbPlotIAbsSquared,
                            self.pref_panel.cbPlotQLength, self.pref_panel.cbPlotQInvLength]
        for enabled in enabled_on_load:
            self.assertTrue(enabled.isEnabled())
        for disabled in disabled_on_load:
            self.assertFalse(disabled.isEnabled())

    def testPreferencesInteractions(self):
        """Test the base interactions in window behavior"""
        # Check the list widget and stacked widget are tied together
        last_row = self.pref_panel.listWidget.count() - 1
        self.pref_panel.listWidget.setCurrentRow(last_row)
        self.assertEqual(self.pref_panel.stackedWidget.currentIndex(), self.pref_panel.listWidget.currentRow())
        # Test the plotting check boxes are tied to their appropriate behavior
        self.pref_panel.checkBoxPlotIAsLoaded.setChecked(False)
        self.assertNotIn(False, [self.pref_panel.cbPlotIAbs.isEnabled(), self.pref_panel.cbPlotIArbitrary.isEnabled(),
                                 self.pref_panel.cbPlotIAbsSquared, self.pref_panel.cbPlotISesans])
        self.pref_panel.checkBoxPlotQAsLoaded.setChecked(False)
        self.assertNotIn(False, [self.pref_panel.cbPlotQLength.isEnabled(), self.pref_panel.cbPlotQInvLength])
        # Test the data loading check boxes are tied to their appropriate behavior
        # Cancel an override behavior
        self.pref_panel.checkBoxLoadQOverride.setChecked(True)
        while not self.pref_panel.warning:
            pass
        cancel_button = self.pref_panel.warning.button(QMessageBox.Cancel)
        cancel_button.click()
        self.assertFalse(self.pref_panel.checkBoxLoadQOverride.isChecked())
        # Allow the override behavior
        self.pref_panel.checkBoxLoadQOverride.setChecked(True)
        while not self.pref_panel.warning:
            pass
        ok_button = self.pref_panel.warning.button(QMessageBox.Ok)
        QTest.mouseClick(ok_button, Qt.LeftButton)
        self.assertTrue(self.pref_panel.checkBoxLoadQOverride.isChecked())

    def testPreferencesExtensibility(self):
        """Test ability to add and remove items from the listWidget and stackedWidget"""
        # Create fake QWidget, add to stacked widget, and add item to list widget
        new_widget = QWidget()
        starting_size = self.pref_panel.stackedWidget.count()
        self.pref_panel.stackedWidget.addWidget(new_widget)
        self.pref_panel.listWidget.addItem("Fake Widget")
        # Ensure stacked widget and list widget have the same number of elements
        self.assertEqual(self.pref_panel.stackedWidget.count(), self.pref_panel.listWidget.count())
        self.assertEqual(starting_size + 1, self.pref_panel.stackedWidget.count())
        # Select last item in list widget and check the stacked widget moves too
        self.pref_panel.listWidget.setCurrentRow(self.pref_panel.listWidget.count() - 1)
        self.assertEqual(self.pref_panel.stackedWidget.currentIndex(), self.pref_panel.listWidget.currentRow())

    def testConfigChangesLocal(self):
        """Test changes to custom config that happen in a single instance of the preferences window"""
        # TODO: Change preferences and check config is changed accordingly
        pass

    def testConfigChangesGlobal(self):
        """Test changes to custom config between instances of the preferences window"""
        # TODO: Change config items, open new preferences window, check preferences match
        pass