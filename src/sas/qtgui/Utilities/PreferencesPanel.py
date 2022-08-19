import logging

from PyQt5.QtWidgets import QComboBox, QDialog, QPushButton, QWidget, QLabel, QHBoxLayout, QVBoxLayout, QLineEdit, QCheckBox
from typing import Optional, Any, List, Union, Callable

from sas import get_custom_config
from sas.qtgui.Utilities.UI.PreferencesUI import Ui_preferencesUI

logger = logging.getLogger(__name__)


def set_config_value(attr: str, value: Any):
    """Helper method to set any config value, regardless if it exists or not
    :param attr: The configuration attribute that will be set
    :param value: The value the attribute will be set to. This could be a str, int, bool, a class instance, or any other
    """
    custom_config = get_custom_config()
    setattr(custom_config, attr, value)


def get_config_value(attr: str, default: Optional[Any] = None) -> Any:
    """Helper method to get any config value, regardless if it exists or not
    :param attr: The configuration attribute that will be returned
    :param default: The assumed value, if the attribute cannot be found
    """
    custom_config = get_custom_config()
    return getattr(custom_config, attr, default) if hasattr(custom_config, attr) else default


def cb_replace_all_items_with_new(cb: QComboBox, new_items: List[str], default_item: Optional[str] = None):
    """Helper method that removes existing ComboBox values, replaces them and sets a default item, if defined
    :param cb: A QComboBox object
    :param new_items: A list of strings that will be used to populate the QComboBox
    :param default_item: The value to set the QComboBox to, if set
    """
    cb.clear()
    cb.addItems(new_items)
    if default_item and default_item in new_items:
        cb.setCurrentIndex(cb.findText(default_item))


class PreferencesPanel(QDialog, Ui_preferencesUI):
    """A preferences panel to house all SasView related settings. The left side of the window is a listWidget with a
    options menus available. The right side of the window is a stackedWidget object that houses the options
    associated with each listWidget item.
    **Important Note** When adding new preference widgets, the index for the listWidget and stackedWidget *must* match
    Release notes:
    SasView v5.0.5: Added defaults for loaded data units and plotted units
    """

    def __init__(self, parent=None):
        super(PreferencesPanel, self).__init__(parent)
        self.setupUi(self)
        self.parent = parent
        self.setWindowTitle("Preferences")
        self.warning = None
        # A list of callables used to restore the default values for each item in StackedWidget
        self.restoreDefaultMethods = []
        # Set defaults values for the list and stacked widgets
        self.stackedWidget.setCurrentIndex(0)
        self.listWidget.setCurrentRow(0)
        # Add window actions
        self.listWidget.currentItemChanged.connect(self.prefMenuChanged)
        self.buttonBox.clicked.connect(self.onClick)

    def prefMenuChanged(self):
        """When the preferences menu selection changes, change to the appropriate preferences widget """
        row = self.listWidget.currentRow()
        self.stackedWidget.setCurrentIndex(row)

    def onClick(self, btn: QPushButton):
        """Handle button click events in one area"""
        # Reset to the default preferences
        if btn.text() == 'Restore Defaults':
            self.restoreDefaultPreferences()
        elif btn.text() == 'OK':
            self.close()
        elif btn.text() == 'Help':
            self.help()

    def restoreDefaultPreferences(self):
        """Reset all preferences to their default preferences"""
        for method in self.restoreDefaultMethods:
            if callable(method):
                method()
            else:
                logger.warning(f'While restoring defaults, {str(method)} of type {type(method)}'
                               + ' was given. A callable object was expected.')

    def close(self):
        """Save the configuration values when the preferences window is closed"""
        if hasattr(self.parent, 'guiManager'):
            self.parent.guiManager.writeCustomConfig(get_custom_config())
        super(PreferencesPanel, self).close()

    def addWidget(self, widget: QWidget):
        self.stackedWidget.addWidget(widget)
        self.listWidget.addItem(widget.name)
        if widget.resetDefaults is not None and callable(widget.resetDefaults):
            self.restoreDefaultMethods.append(widget.resetDefaults)

    def help(self):
        """Open the help window associated with the preferences window"""
        tree_location = "/user/qtgui/MainWindow/preferences_help.html"
        self.parent.showHelp(tree_location)


class PreferencesWidget(QWidget):
    """A helper class that bundles all values needed to add a new widget to the preferences panel
    """
    # Name that will be added to the PreferencesPanel listWidget
    name = None  # type: str

    def __init__(self, name: str, default_method: Optional[Callable] = None):
        super(PreferencesWidget, self).__init__()
        self.name = name
        self.resetDefaults = default_method
        self.horizontalLayout = QHBoxLayout()
        self.setLayout(self.horizontalLayout)
        self.adjustSize()

    def _createLayoutAndTitle(self, title: str):
        """A private class method that creates a vertical layout to hold the title and interactive item.
        :param title: The title of the interactive item to be added to the preferences panel.
        :return: A QVBoxLayout instance with a title box already added
        """
        layout = QVBoxLayout(self.horizontalLayout)
        label = QLabel(title + ": ", layout)
        layout.addWidget(label)
        return layout

    def addComboBox(self, title: str, params: List[Union[str, int, float]], callback: Callable, default: Optional[str]):
        """Add a title and combo box within the widget.
        :param title: The title of the combo box to be added to the preferences panel.
        :param params: A list of options to be added to the combo box.
        :param callback: A callback method called when the combobox value is changed.
        """
        layout = self._createLayoutAndTitle(title)
        box = QComboBox(layout)
        cb_replace_all_items_with_new(box, params, default)
        box.currentIndexChanged.connect(callback)
        layout.addWidget(box)
        self.horizontalLayout.addWidget(layout)

    def addTextInput(self, title: str, callback: Callable, default_text: Optional[str] = ""):
        """Add a title and text box within the widget.
        :param title: The title of the text box to be added to the preferences panel.
        :param callback: A callback method called when the combobox value is changed.
        :param default_text: An optional value to be put within the text box as a default. Defaults to an empty string.
        """
        layout = self._createLayoutAndTitle(title)
        text_box = QLineEdit(layout)
        if default_text:
            text_box.setText(default_text)
        text_box.textChanged.connect(callback)
        layout.addWidget(text_box)
        self.horizontalLayout.addWidget(layout)

    def addCheckBox(self, title: str, callback: Callable, checked: Optional[bool] = False):
        """Add a title and check box within the widget.
        :param title: The title of the check box to be added to the preferences panel.
        :param callback: A callback method called when the combobox value is changed.
        :param checked: An optional boolean value to specify if the check box is checked. Defaults to unchecked.
        """
        layout = self._createLayoutAndTitle(title)
        check_box = QCheckBox(layout)
        check_box.setChecked(checked)
        check_box.toggled.connect(callback)
        layout.addWidget(check_box)
        self.horizontalLayout.addWidget(layout)
