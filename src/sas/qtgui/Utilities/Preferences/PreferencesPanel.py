import logging
import os
import sys
from collections.abc import Callable
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QMessageBox, QWidget

from sas.qtgui.Perspectives.perspective import Perspective
from sas.qtgui.Utilities.Preferences.PreferencesWidget import PreferencesWidget
from sas.qtgui.Utilities.Preferences.UI.PreferencesUI import Ui_preferencesUI
from sas.system import config

# The PreferencesPanel object will instantiate all widgets during its instantiation.
#  e.g:
#  `from foo.bar import BarWidget  # BarWidget is a child of PreferencesWidget`
#  `BASE_PANELS = {"Bar Widget Options": BarWidget}`
# PreferenceWidget Imports go here and then are added to the BASE_PANELS, but not instantiated.
from .DisplayPreferencesWidget import DisplayPreferencesWidget
from .PlottingPreferencesWidget import PlottingPreferencesWidget

# Pre-made option widgets

BASE_PANELS = {"Plotting Settings": PlottingPreferencesWidget,
               "Display Settings": DisplayPreferencesWidget,
               }  # Type: Dict[str, Union[Type[PreferencesWidget], Callable[[],QWidget]]
ConfigType = str | bool | float | int | list[str | float | int]

logger = logging.getLogger(__name__)


def restart_main():
    # Restart the application...
    executable = sys.executable
    executable_filename = os.path.split(executable)[1]
    if executable_filename.lower().startswith('python'):
        # application is running within a python interpreter
        python = executable
        os.execv(python, [python, ] + sys.argv)
    else:
        # application is running as a standalone executable
        os.execv(executable, sys.argv)


class PreferencesPanel(QDialog, Ui_preferencesUI):
    """A preferences panel to house all SasView related settings. The left side of the window is a listWidget with a
    options menus available. The right side of the window is a stackedWidget object that houses the options
    associated with each listWidget item.
    """

    def __init__(self, parent: Any | None = None):
        super(PreferencesPanel, self).__init__(parent)
        self.setupUi(self)
        self._staged_changes = {}
        self._staged_non_config_changes = {}
        self._staged_requiring_restart = set()
        self._staged_invalid = set()
        self.parent = parent
        self.setWindowTitle("Preferences")
        # Add predefined widgets to window
        self.addWidgets(BASE_PANELS)
        # Set defaults values for the list and stacked widgets
        self.stackedWidget.setCurrentIndex(0)
        self.listWidget.setCurrentRow(0)
        # Add window actions
        self.listWidget.currentItemChanged.connect(self.prefMenuChanged)
        self.buttonBox.button(QDialogButtonBox.RestoreDefaults).clicked.connect(self.restoreDefaultPreferences)
        self.buttonBox.button(QDialogButtonBox.Ok).clicked.connect(self._okClicked)
        self.buttonBox.button(QDialogButtonBox.Cancel).clicked.connect(self._cancelStaging)
        self.buttonBox.button(QDialogButtonBox.Apply).clicked.connect(self._saveStagedChanges)
        self.buttonBox.button(QDialogButtonBox.Help).clicked.connect(self.help)
        self._set_accept()

        self.registered_perspectives: list[str] = []

    def addWidgets(self, widgets: dict[str, Callable]):
        """Add a list of named widgets to the window"""
        for name, widget in widgets.items():
            if isinstance(widget, PreferencesWidget):
                self.addWidget(widget, name)
            elif callable(widget):
                self.addWidget(widget(), name)

    def prefMenuChanged(self):
        """When the preferences menu selection changes, change to the appropriate preferences widget """
        self.setWidgetIndex(self.listWidget.currentRow())

    def setMenuByName(self, name: str):
        """Set the index of the listWidget and stackedWidget, using the display name as the search term"""
        for item in self.listWidget.findItems(name, Qt.MatchContains):
            if item.text() == name:
                self.listWidget.setCurrentItem(item)
        self.setWidgetIndex(self.listWidget.currentRow())

    def setWidgetIndex(self, row: int):
        """Set the menu and options stack to a given index"""
        self.listWidget.setCurrentRow(row)
        self.stackedWidget.setCurrentIndex(row)

    def restoreDefaultPreferences(self):
        """Reset preferences for the active widget to the default values."""
        widget = self.stackedWidget.currentWidget()
        if hasattr(widget, 'restoreDefaults') and callable(widget.restoreDefaults):
            widget.restoreDefaults()
        self._set_accept()

    def stageSingleChange(self, key: str, value: ConfigType, config_restart_message: str | None = ""):
        """ Preferences widgets should call this method when changing a variable to prevent direct configuration
        changes"""
        if getattr(config, key, None) is None:
            self._staged_non_config_changes[key] = value
        else:
            self._staged_changes[key] = value
        self._staged_requiring_restart.add(config_restart_message)
        self.unset_invalid_input(key)
        self._set_accept()

    def unStageSingleChange(self, key: str, config_restart_message: str | None = ""):
        """Preferences widgets should call this method when removing an invalid value from the staged changes."""
        self._staged_changes.pop(key, None)
        self._staged_requiring_restart.discard(config_restart_message)
        self._set_accept()

    def set_invalid_input(self, key: str):
        """Widgets should call this if an input is invalid to disable the 'OK' and 'Apply' buttons."""
        self._staged_invalid.add(key)
        self._set_accept()

    def unset_invalid_input(self, key: str):
        """Remove the key from the invalid staged values, if necessary"""
        self._staged_invalid.discard(key)
        self._set_accept()

    def _set_accept(self):
        """Enable/disable the 'Accept' and 'OK' buttons based on the current state."""
        # If any inputs aren't valid -or- if no changes are staged, disable the buttons
        staged = any(self._staged_changes.keys()) or any(self._staged_non_config_changes.keys())
        toggle = not any(self._staged_invalid) and staged
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(toggle)
        self.buttonBox.button(QDialogButtonBox.Apply).setEnabled(toggle)

    def _okClicked(self):
        """ Action triggered when the OK button is clicked"""
        self._saveStagedChanges()
        self.close()

    def _saveStagedChanges(self):
        """ When OK or Apply are clicked, all staged changes should be applied to the config. """
        for i in range(self.stackedWidget.count()):
            self.stackedWidget.widget(i).applyNonConfigValues()
        for k, v in self._staged_changes.items():
            setattr(config, k, v)
        if any(self._staged_requiring_restart):
            message = "SasView must restart for the following values to take effect. Do you wish to restart?:\n"
            for val in self._staged_requiring_restart:
                message += f" -{val}\n"
            msgBox = QMessageBox(QMessageBox.Information, "", message, QMessageBox.Yes|QMessageBox.No)
            msgBox.show()
            if msgBox.exec() == QMessageBox.Yes:
                self.parent.guiManager.quitApplication()
                restart_main()
        self._reset_state()

    def _cancelStaging(self):
        """ When the Cancel button is clicked, throw away any staged changes and hide the window"""
        for i in range(self.stackedWidget.count()):
            self.stackedWidget.widget(i).restoreGUIValuesFromConfig()
        self._reset_state()
        self.close()

    def _reset_state(self):
        self._staged_requiring_restart = set()
        self._staged_invalid = set()
        self._staged_changes = {}
        self._staged_non_config_changes = {}
        self._set_accept()

    def closeEvent(self, event):
        """Capture all window close events and ensure the window is in a base state"""
        self._cancelStaging()

    def close(self):
        """Save the configuration values when the preferences window is closed"""
        super(PreferencesPanel, self).close()

    def addWidget(self, widget: QWidget, name: str | None = None):
        """Add a single widget to the panel"""

        # Set the parent of the new widget to the parent of this window
        widget.parent = self
        self.stackedWidget.addWidget(widget)
        # Set display name in the listWidget with the priority of
        #  name passed to method > widget.name > "Generic Preferences"
        name = name if name is not None else getattr(widget, 'name', None)
        name = name if name is not None else "Generic Preferences"
        # Add the widget default reset method to the global set

        self.listWidget.addItem(name)

    def registerPerspectivePreferences(self, perspective: Perspective):
        """ Register preferences from a perspective"""

        if perspective.name not in self.registered_perspectives:

            for preference_widget in perspective.preferences:

                self.addWidget(preference_widget)
                self.registered_perspectives.append(perspective.name)

    def help(self):
        """Open the help window associated with the preferences window"""
        tree_location = "/user/qtgui/MainWindow/preferences_help.html"
        self.parent.guiManager.showHelp(tree_location)
