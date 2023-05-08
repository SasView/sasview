import os
import pytest
from PySide6.QtWidgets import QWidget, QLineEdit, QComboBox, QCheckBox

from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Utilities.PreferencesPanel import *


class PreferencesPanelTest:
    @pytest.fixture(autouse=True)
    def widget(self, qapp):
        class DummyClass:
            def __init__(self):
                self.path = None

            @staticmethod
            def showHelp(location):
                """Simulate a help window"""
                return location == "/user/qtgui/MainWindow/preferences_help.html"

        w = QWidget()
        w.guiManager = DummyClass()
        panel = PreferencesPanel(w)
        yield panel
        panel.close()
        panel.destroy()

    @pytest.fixture(autouse=True)
    def data(self):
        data = [Data1D(x=[1.0, 2.0, 3.0], y=[10.0, 11.0, 12.0])]
        yield data

    def testDefaults(self, widget):
        """Test the freshly-opened panel with no changes made"""
        assert widget.stackedWidget.count() == widget.listWidget.count()
        assert -1 == widget.stackedWidget.currentIndex()

    def testPreferencesInteractions(self, widget):
        """Test the base interactions in window behavior"""
        # Check the list widget and stacked widget are tied together
        last_row = widget.listWidget.count() - 1
        widget.listWidget.setCurrentRow(last_row)
        assert widget.stackedWidget.currentIndex() == widget.listWidget.currentRow()

    def testPreferencesExtensibility(self, widget):
        """Test ability to add and remove items from the listWidget and stackedWidget"""
        # Create fake PreferencesWidget, add to stacked widget, and add item to list widget
        new_widget = PreferencesWidget("Fake Widget")
        starting_size = widget.stackedWidget.count()
        widget.addWidget(new_widget)
        # Ensure stacked widget and list widget have the same number of elements
        assert widget.stackedWidget.count() == widget.listWidget.count()
        assert starting_size + 1 == widget.stackedWidget.count()
        # Select last item in list widget and check the stacked widget moves too
        widget.listWidget.setCurrentRow(widget.listWidget.count() - 1)
        assert widget.stackedWidget.currentIndex() == widget.listWidget.currentRow()

    def testHelp(self, widget, mocker):
        mocker.patch.object(widget, 'onClick')
        widget.buttonBox.buttons()[0].click()
        assert widget.onClick.called_once()

    def testPreferencesWidget(self, widget, mocker):
        mocker.patch.object(widget, 'checked', create=True)
        mocker.patch.object(widget, 'combo', create=True)
        mocker.patch.object(widget, 'textified', create=True)
        mocker.patch.object(widget, 'resetPref', create=True)

        pref = PreferencesWidget("Dummy Widget", widget.resetPref)
        pref.addTextInput("blah", widget.textified)
        pref.addCheckBox("ho hum", widget.checked)
        pref.addComboBox("combo", ["a", "b", "c"], widget.combo, "a")

        widget.addWidget(pref)

        widget.restoreDefaultPreferences()
        assert widget.resetPref.called_once()

        for child in pref.layout().children():
            if isinstance(child, QLineEdit):
                child.setText("new text")
            elif isinstance(child, QComboBox):
                child.setCurrentIndex(1)
            elif isinstance(child, QCheckBox):
                child.setChecked(not child.checkState())

        assert widget.textified.called_once()
        assert widget.combo.called_once()
        assert widget.checked.called_once()

