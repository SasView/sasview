import functools
import logging

from PyQt5.QtWidgets import QComboBox, QWidget, QLabel, QHBoxLayout, QVBoxLayout, QLineEdit, QCheckBox, QFrame
from typing import Optional, List, Union, Callable, Any

from sas.system import config

logger = logging.getLogger(__name__)


def set_config_value(value: Any, attr: str, dtype: Optional[Callable] = None):
    """Helper method to set any config value
    :param attr: The configuration attribute that will be set
    :param value: The value the attribute will be set to. This could be a str, int, bool, a class instance, or any other
    :param dtype: The datatype to cast the input value to if casting is desired
    """
    if hasattr(config, attr):
        # Attempt to coerce value to a specific type. Useful for numeric values from text boxes, etc.
        if dtype is not None:
            value = dtype(value)
        # Another sanity check - the config system would also raise on data type mismatch, so potentially redundant
        if type(getattr(config, attr)) == type(value):
            setattr(config, attr, value)
        else:
            raise TypeError(f"Data type mismatch: {value} has type {type(value)}, expected {type(getattr(config,attr))}")
    else:
        # The only way to get here **should** be during development, thus the debug log.
        logger.debug(f"Please add {attr} to the configuration and give it a sensible default value.")


def get_config_value(attr: str, default: Optional[Any] = None) -> Any:
    """Helper method to get any config value, regardless if it exists or not
    :param attr: The configuration attribute that will be returned
    :param default: The assumed value, if the attribute cannot be found
    """
    return getattr(config, attr, default) if hasattr(config, attr) else default


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


def config_value_setter_generator(attr: str, dtype: Optional[Callable] = None):
    """Helper method that generates a callback to set a config value.

    :param attr: name of the attribute to set
    :param dtype: The datatype to cast the input value to if casting is desired
    :return: a function that takes a single argument, which will be cast to dtype
            and set in config as attr
    """

    return functools.partial(set_config_value, attr=attr, dtype=dtype)


class QHLine(QFrame):
    """::CRUFT:: This creates a horizontal line in PyQt5. PyQt6 QFrame has finer shape control"""
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)


class PreferencesWidget(QWidget):
    """A helper class that bundles all values needed to add a new widget to the preferences panel"""
    # Default name that will be used in the PreferencesPanel listWidget
    name = None  # type: str

    def __init__(self, name: str):
        super(PreferencesWidget, self).__init__()
        self.parent = None
        self.name = name
        # Create generic layout
        self.verticalLayout = QVBoxLayout()
        self.setLayout(self.verticalLayout)
        # Child class generates GUI elements
        self._addAllWidgets()
        # Push all elements to the top of the window
        self.verticalLayout.addStretch()
        self.adjustSize()

    def _addAllWidgets(self):
        """A private pseudo-abstract class that children should override. All new widgets should be added using this
        method to create consistency between all preference widgets.
        """
        raise NotImplementedError(f"{self.name} has not implemented _addAllWidgets.")

    def restoreDefaults(self):
        """A pseudo-abstract class that children should override.
        """
        raise NotImplementedError(f"{self.name} has not implemented restoreDefaults.")

    def _createLayoutAndTitle(self, title: str):
        """A private class method that creates a horizontal layout to hold the title and interactive item.
        :param title: The title of the interactive item to be added to the preferences panel.
        :return: A QHBoxLayout instance with a title box already added
        """
        layout = QHBoxLayout()
        label = QLabel(title + ": ", self)
        layout.addWidget(label)
        return layout

    def addComboBox(self, title: str, params: List[Union[str, int, float]], callback: Callable,
                    default: Optional[str] = None) -> QComboBox:
        """Add a title and combo box within the widget.
        :param title: The title of the combo box to be added to the preferences panel.
        :param params: A list of options to be added to the combo box.
        :param callback: A callback method called when the combobox value is changed.
        :param default: The default option to be selected in the combo box. The first item is selected if None.
        :return: QComboBox instance to allow subclasses to assign instance name
        """
        layout = self._createLayoutAndTitle(title)
        box = QComboBox(self)
        cb_replace_all_items_with_new(box, params, default)
        box.currentIndexChanged.connect(callback)
        layout.addWidget(box)
        self.verticalLayout.addLayout(layout)
        return box

    def addTextInput(self, title: str, callback: Callable, default_text: Optional[str] = "") -> QLineEdit:
        """Add a title and text box within the widget.
        :param title: The title of the text box to be added to the preferences panel.
        :param callback: A callback method called when the combobox value is changed.
        :param default_text: An optional value to be put within the text box as a default. Defaults to an empty string.
        :return: QLineEdit instance to allow subclasses to assign instance name
        """
        layout = self._createLayoutAndTitle(title)
        text_box = QLineEdit(self)
        if default_text:
            text_box.setText(default_text)
        text_box.textChanged.connect(callback)
        layout.addWidget(text_box)
        self.verticalLayout.addLayout(layout)
        return text_box

    def addCheckBox(self, title: str, callback: Callable, checked: Optional[bool] = False) -> QCheckBox:
        """Add a title and check box within the widget.
        :param title: The title of the check box to be added to the preferences panel.
        :param callback: A callback method called when the combobox value is changed.
        :param checked: An optional boolean value to specify if the check box is checked. Defaults to unchecked.
        :return: QCheckBox instance to allow subclasses to assign instance name
        """
        layout = self._createLayoutAndTitle(title)
        check_box = QCheckBox(self)
        check_box.setChecked(checked)
        check_box.toggled.connect(callback)
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
