import logging

from PyQt5.QtWidgets import QDialog, QPushButton, QWidget, QListWidgetItem
from typing import Optional, Callable, Dict, Type

from sas.system.config.config import config
from sas.qtgui.Utilities.Preferences.UI.PreferencesUI import Ui_preferencesUI
from sas.qtgui.Utilities.Preferences.PreferencesWidget import PreferencesWidget

# The PreferencesPanel object will instantiate all widgets during its instantiation.
#  e.g:
#  `from foo.bar import BarWidget  # BarWidget is a child of PreferencesWidget`
#  `BASE_PANELS = {"Bar Widget Options": BarWidget}`
# PreferenceWidget Imports go here and then are added to the BASE_PANELS, but not instantiated.
from .PlottingPreferencesWidget import PlottingPreferencesWidget
from .FittingOptionsWidget import FittingOptions
from sas.qtgui.Utilities.Preferences.DisplayPreferencesWidget import DisplayPreferencesWidget
# Pre-made option widgets

BASE_PANELS = {"Plotting Settings":PlottingPreferencesWidget,
               "Display Settings":DisplayPreferencesWidget,
               FittingOptions.name: FittingOptions,
            }  # Type: Dict[str, Union[Type[PreferencesWidget], Callable[[],QWidget]]

logger = logging.getLogger(__name__)


class PreferencesPanel(QDialog, Ui_preferencesUI):
    """A preferences panel to house all SasView related settings. The left side of the window is a listWidget with a
    options menus available. The right side of the window is a stackedWidget object that houses the options
    associated with each listWidget item.
    **Important Note** When adding new preference widgets, the index for the listWidget and stackedWidget *must* match
    """

    def __init__(self, parent=None):
        super(PreferencesPanel, self).__init__(parent)
        self.setupUi(self)
        self.parent = parent
        self.setWindowTitle("Preferences")
        self.warning = None
        # A list of callables used to restore the default values for each item in StackedWidget
        self.restoreDefaultMethods = []
        # Add predefined widgets to window
        self.addWidgets(BASE_PANELS)
        # Set defaults values for the list and stacked widgets
        self.stackedWidget.setCurrentIndex(0)
        self.listWidget.setCurrentRow(0)
        # Add window actions
        self.listWidget.currentItemChanged.connect(self.prefMenuChanged)
        self.buttonBox.clicked.connect(self.onClick)

    def addWidgets(self, widgets: Dict[str, Callable]):
        """Add a list of widgets to the window"""
        for name, widget in widgets.items():
            if isinstance(widget, PreferencesWidget):
                self.addWidget(widget, name)
            elif callable(widget):
                self.addWidget(widget(), name)

    def prefMenuChanged(self):
        """When the preferences menu selection changes, change to the appropriate preferences widget """
        self.setMenuIndex(self.listWidget.currentRow())

    def setMenuByName(self, name: str):
        """Set the index to be changed by the title name"""
        self.listWidget.setCurrentItem(QListWidgetItem(name))
        self.setMenuIndex(self.listWidget.currentRow())

    def setMenuIndex(self, row: int):
        """Set the menu to a given index"""
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
        """Reset all preferences to their default preferences"""
        for method in self.restoreDefaultMethods:
            if callable(method):
                method()
            else:
                logger.warning(f'While restoring defaults, {str(method)} of type {type(method)}'
                               + ' was given. A callable object was expected.')

    def close(self):
        """Save the configuration values when the preferences window is closed"""
        config.save()
        super(PreferencesPanel, self).close()

    def addWidget(self, widget: QWidget, name: Optional[str] = None):
        widget.parent = self.parent
        self.stackedWidget.addWidget(widget)
        name = widget.name if hasattr(widget, 'name') and widget.name else name
        name = "Unknown" if not name else name
        self.listWidget.addItem(name)
        if hasattr(widget, 'resetDefaults') and callable(widget.resetDefaults):
            self.restoreDefaultMethods.append(widget.resetDefaults)

    def help(self):
        """Open the help window associated with the preferences window"""
        tree_location = "/user/qtgui/MainWindow/preferences_help.html"
        self.parent.showHelp(tree_location)
