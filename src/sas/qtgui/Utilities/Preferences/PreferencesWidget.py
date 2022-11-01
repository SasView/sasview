import logging

from PyQt5.QtGui import QIntValidator, QDoubleValidator
from PyQt5.QtWidgets import QComboBox, QWidget, QLabel, QHBoxLayout, QVBoxLayout, QLineEdit, QCheckBox, QFrame
from typing import Optional, List, Union

from sas.system import config

logger = logging.getLogger(__name__)


def cb_replace_all_items_with_new(cb: QComboBox, new_items: List[str], default_item: Optional[str] = None):
    """Helper method that removes existing ComboBox values, replaces them and sets a default item, if defined
    :param cb: A QComboBox object
    :param new_items: A list of strings that will be used to populate the QComboBox
    :param default_item: The value to set the QComboBox to, if set
    """
    cb.clear()
    cb.addItems(new_items)
    index = cb.findText(default_item) if default_item and default_item in new_items else 0
    cb.setCurrentIndex(index)


class QHLine(QFrame):
    """::CRUFT:: This creates a horizontal line in PyQt5. PyQt6 QFrame has finer shape control"""
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)


class PreferencesWidget(QWidget):
    """A helper class that bundles all values needed to add a new widget to the preferences panel
    """

    def __init__(self, name: str):
        super(PreferencesWidget, self).__init__()
        # Keep parent as None until widget is added to preferences panel, then this will become th
        self.parent = None
        self.name: str = name
        # All parameter names used in this panel
        self.config_params: List[str] = []
        # Create generic layout
        self.verticalLayout = QVBoxLayout()
        self.setLayout(self.verticalLayout)
        # Child class generates GUI elements
        self._addAllWidgets()
        # Push all elements to the top of the window
        self.verticalLayout.addStretch()
        self.adjustSize()

    def restoreDefaults(self):
        """Generic method to restore all default values for the widget. """
        for param in self.config_params:
            default = config.defaults.get(param)
            setattr(config, param, default)
        self.restoreGUIValuesFromConfig()

    def _stageChange(self, key: str, value: Union[str, bool, float, int, List]):
        """ All inputs should call this method when attempting to change config values. """
        if self.parent is not None and hasattr(self.parent, 'stageSingleChange'):
            self.parent.stageSingleChange(key, value)

    def restoreGUIValuesFromConfig(self):
        """A generic method that blocks all signalling, and restores the GUI values from the config file.
        Called when staging is cancelled or defaults should be restored."""
        self._toggleBlockAllSignaling(True)
        self._restoreFromConfig()
        self._toggleBlockAllSignaling(False)

    def _restoreFromConfig(self):
        """A pseudo-abstract class that children should override. Recalls all config values and restores the GUI. """
        raise NotImplementedError(f"{self.name} has not implemented revertChanges.")

    def _toggleBlockAllSignaling(self, toggle: bool):
        """A pseudo-abstract class that children should override. Toggles signalling for all elements. """
        raise NotImplementedError(f"{self.name} has not implemented _toggleBlockAllSignalling.")

    #############################################################
    # GUI Helper methods for widgets that don't have a UI element

    def _addAllWidgets(self):
        """A private pseudo-abstract class that children should override. Widgets with their own UI file should pass.
        """
        raise NotImplementedError(f"{self.name} has not implemented _addAllWidgets.")

    def _createLayoutAndTitle(self, title: str):
        """A private class method that creates a horizontal layout to hold the title and interactive item.
        :param title: The title of the interactive item to be added to the preferences panel.
        :return: A QHBoxLayout instance with a title box already added
        """
        layout = QHBoxLayout()
        label = QLabel(title + ": ", self)
        layout.addWidget(label)
        return layout

    def addComboBox(self, title: str, params: List[Union[str, int, float]], default: Optional[str] = None) -> QComboBox:
        """Add a title and combo box within the widget.
        :param title: The title of the combo box to be added to the preferences panel.
        :param params: A list of options to be added to the combo box.
        :param default: The default option to be selected in the combo box. The first item is selected if None.
        :return: QComboBox instance to allow subclasses to assign instance name
        """
        layout = self._createLayoutAndTitle(title)
        box = QComboBox(self)
        cb_replace_all_items_with_new(box, params, default)
        layout.addWidget(box)
        self.verticalLayout.addLayout(layout)
        return box

    def addTextInput(self, title: str, default_text: Optional[str] = "") -> QLineEdit:
        """Add a title and text box within the widget.
        :param title: The title of the text box to be added to the preferences panel.
        :param default_text: An optional value to be put within the text box as a default. Defaults to an empty string.
        :return: QLineEdit instance to allow subclasses to assign instance name
        """
        layout = self._createLayoutAndTitle(title)
        text_box = QLineEdit(self)
        if default_text:
            text_box.setText(str(default_text))
        layout.addWidget(text_box)
        self.verticalLayout.addLayout(layout)
        return text_box

    def addIntegerInput(self, title: str, default_number: Optional[int] = 0) -> QLineEdit:
        """Similar to the text input creator, this creates a text input with an integer validator assigned to it.
        :param title: The title of the text box to be added to the preferences panel.
        :param default_number: An optional value to be put within the text box as a default. Defaults to an empty string.
        :return: QLineEdit instance to allow subclasses to assign instance name
        """
        int_box = self.addTextInput(title, str(default_number))
        int_box.setValidator(QIntValidator())
        return int_box

    def addFloatInput(self, title: str, default_number: Optional[int] = 0) -> QLineEdit:
        """Similar to the text input creator, this creates a text input with an float validator assigned to it.
        :param title: The title of the text box to be added to the preferences panel.
        :param default_number: An optional value to be put within the text box as a default. Defaults to an empty string.
        :return: QLineEdit instance to allow subclasses to assign instance name
        """
        float_box = self.addTextInput(title, str(default_number))
        float_box.setValidator(QDoubleValidator())
        return float_box

    def addCheckBox(self, title: str, checked: Optional[bool] = False) -> QCheckBox:
        """Add a title and check box within the widget.
        :param title: The title of the check box to be added to the preferences panel.
        :param checked: An optional boolean value to specify if the check box is checked. Defaults to unchecked.
        :return: QCheckBox instance to allow subclasses to assign instance name
        """
        layout = self._createLayoutAndTitle(title)
        check_box = QCheckBox(self)
        check_box.setChecked(checked)
        layout.addWidget(check_box)
        self.verticalLayout.addLayout(layout)
        return check_box

    def addHorizontalLine(self):
        """Add a horizontal line as a divider."""
        self.verticalLayout.addWidget(QHLine())

    def addHeaderText(self, text: str):
        """Add a static text box to the widget, likely as a heading to separate options
        :param text: The title of the check box to be added to the preferences panel.
        """
        label = QLabel()
        label.setText(text)
        self.verticalLayout.addWidget(label)
