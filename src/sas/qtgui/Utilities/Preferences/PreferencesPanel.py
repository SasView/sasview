import logging

from PyQt5.QtWidgets import QDialog, QPushButton, QWidget
from PyQt5.QtCore import Qt
from typing import Optional, Callable, Dict, Any

from sas.qtgui.Utilities.Preferences.UI.PreferencesUI import Ui_preferencesUI
from sas.qtgui.Utilities.Preferences.PreferencesWidget import PreferencesWidget

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

logger = logging.getLogger(__name__)


class PreferencesPanel(QDialog, Ui_preferencesUI):
    """A preferences panel to house all SasView related settings. The left side of the window is a listWidget with a
    options menus available. The right side of the window is a stackedWidget object that houses the options
    associated with each listWidget item.
    """

    def __init__(self, parent: Optional[Any] = None):
        super(PreferencesPanel, self).__init__(parent)
        self.setupUi(self)
        self._staging = False
        self.parent = parent
        self.setWindowTitle("Preferences")
        # Add predefined widgets to window
        self.addWidgets(BASE_PANELS)
        # Set defaults values for the list and stacked widgets
        self.stackedWidget.setCurrentIndex(0)
        self.listWidget.setCurrentRow(0)
        # Add window actions
        self.listWidget.currentItemChanged.connect(self.prefMenuChanged)
        self.buttonBox.clicked.connect(self.onClick)

    def addWidgets(self, widgets: Dict[str, Callable]):
        """Add a list of named widgets to the window"""
        for name, widget in widgets.items():
            if isinstance(widget, PreferencesWidget):
                self.addWidget(widget, name)
            elif callable(widget):
                self.addWidget(widget(), name)

    def prefMenuChanged(self):
        """When the preferences menu selection changes, change to the appropriate preferences widget """
        row = self.listWidget.currentRow()
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
        """Reset preferences for the active widget to the default values."""
        widget = self.stackedWidget.currentWidget()
        if hasattr(widget, 'restoreDefaults') and callable(widget.restoreDefaults):
            widget.restoreDefaults()

    def close(self):
        """Save the configuration values when the preferences window is closed"""
        super(PreferencesPanel, self).close()

    def addWidget(self, widget: QWidget, name: Optional[str] = None):
        """Add a single widget to the panel"""
        # Set the parent of the new widget to the parent of this window
        widget.parent = self.parent
        self.stackedWidget.addWidget(widget)
        # Set display name in the listWidget with the priority of
        #  name passed to method > widget.name > "Generic Preferences"
        name = name if name is not None else getattr(widget, 'name', None)
        name = name if name is not None else "Generic Preferences"
        # Add the widget default reset method to the global set
        self.listWidget.addItem(name)

    def help(self):
        """Open the help window associated with the preferences window"""
        tree_location = "/user/qtgui/MainWindow/preferences_help.html"
        self.parent.guiManager.showHelp(tree_location)
