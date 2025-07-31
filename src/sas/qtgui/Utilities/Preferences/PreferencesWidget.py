import logging

from PySide6.QtGui import QDoubleValidator, QIntValidator, QValidator
from PySide6.QtWidgets import QCheckBox, QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QVBoxLayout, QWidget

from sas.system import config

ConfigType = str | bool | float | int | list[str | float | int]
logger = logging.getLogger(__name__)


class PrefIntEdit(QLineEdit):
    def __init__(self, parent):
        super().__init__(parent)
        self.setValidator(QIntValidator())

    def text(self):
        text = super().text()
        try:
            text = int(text)
        except ValueError:
            pass
        return text


class PrefFloatEdit(QLineEdit):
    def __init__(self, parent):
        super().__init__(parent)
        self.setValidator(PrefDoubleValidator())

    def text(self):
        text = super().text()
        try:
            text = float(text)
        except ValueError:
            pass
        return text


class PrefDoubleValidator(QDoubleValidator):
    """Override the base validator class to return a floating point value when validated."""
    def fixup(self, input: str) -> None:
        super().fixup(input)
        input.replace(",", "")

    def validate(self, arg__1: str, arg__2: int):
        if "," in str(arg__1):
            return QValidator.Invalid
        return super().validate(arg__1, arg__2)


def cb_replace_all_items_with_new(cb: QComboBox, new_items: list[str], default_item: str | None = None):
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

    def __init__(self, name: str, build_gui=True):
        super(PreferencesWidget, self).__init__()
        # Keep parent as None until widget is added to preferences panel, then this will become th
        self.parent = None
        self.name: str = name
        # All parameter names used in this panel
        self.config_params: list[str] = []
        # A mapping of parameter names to messages displayed when prompting for a restart
        self.restart_params: dict[str, str] = {}
        if build_gui:
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

    def _stageChange(self, key: str, value: ConfigType):
        """ All inputs should call this method when attempting to change config values. """
        if str(value) == str(getattr(config, key, None)):
            # Input changed back to previous value - no need to stage
            self._unStageChange(key)
            # Ensure key is not in invalid list when coming from invalid to valid, but unchanged state
            self.parent.unset_invalid_input(key)
        else:
            # New value for input - stage
            message = self.restart_params.get(key, None)
            self.parent.stageSingleChange(key, value, message)

    def _unStageChange(self, key: str):
        """ A private class method to unstage a single configuration change. Typically when the value is not valid. """
        message = self.restart_params.get(key, None)
        self.parent.unStageSingleChange(key, message)

    def _setInvalid(self, key: str):
        """Adds the input key to a set to ensure the preference panel does not try to apply invalid values"""
        self.parent.set_invalid_input(key)

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

    def applyNonConfigValues(self):
        """Applies values that aren't stored in config. Only widgets that require this need to override this method."""
        pass


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

    def addComboBox(self, title: str, params: list[str | int | float], default: str | None = None) -> QComboBox:
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

    def addTextInput(self, title: str, default_text: str | None = "") -> QLineEdit:
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

    def addIntegerInput(self, title: str, default_number: int | None = 0) -> QLineEdit:
        """Similar to the text input creator, this creates a text input with an integer validator assigned to it.
        :param title: The title of the text box to be added to the preferences panel.
        :param default_number: An optional value to be put within the text box as a default. Defaults to an empty string.
        :return: QLineEdit instance to allow subclasses to assign instance name
        """
        layout = self._createLayoutAndTitle(title)
        int_box = PrefIntEdit(self)
        if default_number:
            int_box.setText(str(default_number))
        layout.addWidget(int_box)
        self.verticalLayout.addLayout(layout)
        return int_box

    def _validate_input_and_stage(self, edit: QLineEdit, key: str):
        """A generic method to validate values entered into QLineEdit inputs. If the value is acceptable, it is staged,
        otherwise, the input background color is changed to yellow and any previous changes will be unstaged until the
        value is corrected.
        :param edit: The QLineEdit input that is being validated.
        :param key: The string representation of the key the QLineEdit value is stored as in the configuration system.
        :return: None
        """
        edit.setStyleSheet("background-color: white")
        validator = edit.validator()
        text = edit.text()
        (state, val, pos) = validator.validate(str(text), 0) if validator else (0, text, 0)
        # Certain inputs, added using class methods, will have a coerce method to coerce the value to the expected type
        if state == QValidator.Acceptable or not validator:
            self._stageChange(key, text)
        else:
            edit.setStyleSheet("background-color: yellow")
            self._unStageChange(key)
            self._setInvalid(key)

    def addFloatInput(self, title: str, default_number: int | None = 0) -> QLineEdit:
        """Similar to the text input creator, this creates a text input with an float validator assigned to it.
        :param title: The title of the text box to be added to the preferences panel.
        :param default_number: An optional value to be put within the text box as a default. Defaults to an empty string.
        :return: QLineEdit instance to allow subclasses to assign instance name
        """
        layout = self._createLayoutAndTitle(title)
        float_box = PrefFloatEdit(self)
        if default_number:
            float_box.setText(str(default_number))
        layout.addWidget(float_box)
        self.verticalLayout.addLayout(layout)
        return float_box

    def addCheckBox(self, title: str, checked: bool | None = False) -> QCheckBox:
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
