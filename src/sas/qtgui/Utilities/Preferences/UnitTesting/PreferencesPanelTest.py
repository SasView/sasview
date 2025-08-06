import pytest
from PySide6.QtWidgets import QWidget

from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Utilities.Preferences.PreferencesPanel import PreferencesPanel
from sas.qtgui.Utilities.Preferences.PreferencesWidget import PreferencesWidget


class DummyPrefWidget(PreferencesWidget):
    def __init__(self, name):
        super(DummyPrefWidget, self).__init__(name)

    def _restoreFromConfig(self):
        pass

    def _toggleBlockAllSignaling(self, toggle: bool):
        pass

    def _addAllWidgets(self):
        pass


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
        assert widget.listWidget.currentRow() == widget.stackedWidget.currentIndex()

    def testPreferencesInteractions(self, widget):
        """Test the base interactions in window behavior"""
        # Check the list widget and stacked widget are tied together
        last_row = widget.listWidget.count() - 1
        widget.listWidget.setCurrentRow(last_row)
        assert widget.stackedWidget.currentIndex() == widget.listWidget.currentRow()

    def testPreferencesExtensibility(self, widget):
        """Test ability to add and remove items from the listWidget and stackedWidget"""
        # Create fake PreferencesWidget, add to stacked widget, and add item to list widget
        new_widget = DummyPrefWidget("Fake Widget")
        starting_size = widget.stackedWidget.count()
        widget.addWidget(new_widget)
        # Ensure stacked widget and list widget have the same number of elements
        assert widget.stackedWidget.count() == widget.listWidget.count()
        assert starting_size + 1 == widget.stackedWidget.count()
        # Select last item in list widget and check the stacked widget moves too
        widget.listWidget.setCurrentRow(widget.listWidget.count() - 1)
        assert widget.stackedWidget.currentIndex() == widget.listWidget.currentRow()

    def testHelp(self, widget, mocker):
        mocker.patch.object(widget, 'close')
        widget.buttonBox.buttons()[0].click()
        assert widget.close.called_once()

    def testPreferencesWidget(self, widget, mocker):
        mocker.patch.object(widget, 'checked', create=True)
        mocker.patch.object(widget, 'combo', create=True)
        mocker.patch.object(widget, 'textified', create=True)
        mocker.patch.object(widget, 'resetPref', create=True)
        mocker.patch.object(widget, '_validate_input_and_stage', create=True)

        pref = DummyPrefWidget("Dummy Widget")
        text_input = pref.addTextInput("blah")
        text_input.textChanged.connect(
            lambda: pref._validate_input_and_stage(text_input, "blah"))
        int_input = pref.addIntegerInput("blah_int")
        int_input.textChanged.connect(
            lambda: pref._validate_input_and_stage(int_input, "blah_int"))
        float_input = pref.addFloatInput("blah_float")
        float_input.textChanged.connect(
            lambda: pref._validate_input_and_stage(float_input, "blah_float"))
        check_box = pref.addCheckBox("ho hum")
        combo_box = pref.addComboBox("combo", ["a", "b", "c"], "a")

        widget.addWidget(pref)

        widget.restoreDefaultPreferences()
        assert widget.resetPref.called_once()

        # Explicitly modify each input type
        text_input.setText("new text")
        int_input.setText('35')
        float_input.setText('35.6')
        check_box.setChecked(not check_box.checkState())
        combo_box.setCurrentIndex(1)

        assert widget.textified.called_once()
        assert widget._validate_input_and_stage.called_once()
        assert widget.combo.called_once()
        assert widget.checked.called_once()
