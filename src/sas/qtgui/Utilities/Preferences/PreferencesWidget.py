import functools
import logging

from PyQt5.QtWidgets import QComboBox, QWidget, QLabel, QHBoxLayout, QVBoxLayout, QLineEdit, QCheckBox, QFrame
from typing import Optional, List, Union, Callable, Any

from sas.system import config

logger = logging.getLogger(__name__)


def set_config_value(attr: str, value: Any, dtype: Optional[Callable] = None):
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
            raise TypeError(f"Data type mismatch: {value} has type {type(value)}, expected {type(config.attr)}")
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


def config_value_setter_generator(attr: str, dtype: Optional[Any] = None):
    """Helper method that generates a callback to set a config value.

    :param attr: name of the attribute to set
    :param dtype: The datatype to cast the input value to if casting is desired
    :return: a function that takes a single argument, which will be cast to dtype
            and set in config as attr
    """
    return functools.partial(set_config_value, attr=attr, dtype=dtype)


class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)


class PreferencesWidget(QWidget):
    """A helper class that bundles all values needed to add a new widget to the preferences panel
    """
    # Name that will be added to the PreferencesPanel listWidget
    name = None  # type: str

    def __init__(self, name: str, default_method: Optional[Callable] = None):
        super(PreferencesWidget, self).__init__()
        self.parent = None
        self.name = name
        self.resetDefaults = default_method
        self.verticalLayout = QVBoxLayout()
        self.setLayout(self.verticalLayout)
        self._addAllWidgets()
        self.verticalLayout.addStretch()
        self.adjustSize()

    def _addAllWidgets(self):
        """
        Psuedo-abstract class that children should override. All widgets should be added here to push all items to the
        top of the window.
        """
        pass

    def _createLayoutAndTitle(self, title: str):
        """A private class method that creates a vertical layout to hold the title and interactive item.
        :param title: The title of the interactive item to be added to the preferences panel.
        :return: A QVBoxLayout instance with a title box already added
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
        self.verticalLayout.addWidget(QHLine())

    def addHeaderText(self, text: str):
        label = QLabel()
        label.setText(text)
        self.verticalLayout.addWidget(label)
