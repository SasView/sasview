import os
import unittest

from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Utilities.PreferencesPanel import *


class PreferencesPanelTest(unittest.TestCase):

    def setUp(self):
        """
        Prepare the unit test window
        """
        class DummyClass:
            def __init__(self):
                self.path = None

            def writeCustomConfig(self, config):
                """
                Write custom configuration
                """
                path = './custom_config.py'
                # Just clobber the file - we already have its content read in
                with open(path, 'w') as out_f:
                    self.path = os.path.abspath(path)
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
        self.data = [Data1D(x=[1.0, 2.0, 3.0], y=[10.0, 11.0, 12.0])]

    def tearDown(self) -> None:
        """Restore global defaults, close the panel and reset class variables"""
        self.pref_panel.restoreDefaultPreferences()
        self.pref_panel.close()
        if self.dummy_parent.guiManager.path:
            os.remove(self.dummy_parent.guiManager.path)
        self.dummy_parent.close()
        self.dummy_parent = None
        self.pref_panel = None

    def testDefaults(self):
        """Test the freshly-opened panel with no changes made"""
        self.assertEqual(self.pref_panel.stackedWidget.count(), self.pref_panel.listWidget.count())
        self.assertEqual(-1, self.pref_panel.stackedWidget.currentIndex())

    def testPreferencesInteractions(self):
        """Test the base interactions in window behavior"""
        # Check the list widget and stacked widget are tied together
        last_row = self.pref_panel.listWidget.count() - 1
        self.pref_panel.listWidget.setCurrentRow(last_row)
        self.assertEqual(self.pref_panel.stackedWidget.currentIndex(), self.pref_panel.listWidget.currentRow())

    def testPreferencesExtensibility(self):
        """Test ability to add and remove items from the listWidget and stackedWidget"""
        # Create fake PreferencesWidget, add to stacked widget, and add item to list widget
        new_widget = PreferencesWidget("Fake Widget")
        starting_size = self.pref_panel.stackedWidget.count()
        self.pref_panel.addWidget(new_widget)
        # Ensure stacked widget and list widget have the same number of elements
        self.assertEqual(self.pref_panel.stackedWidget.count(), self.pref_panel.listWidget.count())
        self.assertEqual(starting_size + 1, self.pref_panel.stackedWidget.count())
        # Select last item in list widget and check the stacked widget moves too
        self.pref_panel.listWidget.setCurrentRow(self.pref_panel.listWidget.count() - 1)
        self.assertEqual(self.pref_panel.stackedWidget.currentIndex(), self.pref_panel.listWidget.currentRow())
