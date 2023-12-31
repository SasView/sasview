from abc import ABC, abstractmethod
from typing import Optional, Sequence, Generic, TypeVar

from PySide6.QtWidgets import QWidget, QLabel, QDoubleSpinBox, QSpinBox, QCheckBox, QFormLayout
from PySide6.QtCore import Signal

T = TypeVar("T")

class NotInitialised(Exception):
    """ Exception thrown when variables are not initialised (should not happen if coded correctly)"""
    def __init__(self):
        super().__init__("Variable not initialised")

class InputVariable(ABC, Generic[T]):
    """
    A variable that contains all the information needed to correctly display in an edit dialog,
    along with appropriate accessors and functions to create appropriate Qt objects.

    This functions as a model for an input form view.

    """
    def __init__(self, variable_name: str, tool_tip: str, display_name: Optional[str]=None):
        self.variable_name = variable_name
        self.display_name = display_name if display_name is not None else variable_name
        self.tool_tip = tool_tip
        self._value: Optional[T] = None

        # Stuff for setting values from form
        self._buffer_value: Optional[T] = None
        self._apply_instantly = True

        self.changed = Signal()


    @abstractmethod
    def create_qt_input(self) -> QWidget:
        """ Create an input box for this variable

        :return: A QWidget that works as an input """

    def create_qt_input_label(self) -> QLabel:
        """ Return a label for this variable"""
        label = QLabel(self.display_name)
        label.setToolTip(self.tool_tip)

        return label

    @property
    def value(self) -> T:
        if self._value is None:
            raise NotInitialised()
        else:
            return self._value

    @value.setter
    def value(self, value):
        self._value = value
        self.changed.emmit()

    def setBufferValue(self, value: T):
        """ Set the value of this variable, used by callbacks """
        self._buffer_value = value

    def updateFromBuffer(self):
        """ Update value to that in the buffer """
        if self._buffer_value is None:
            raise NotInitialised()
        else:
            self.value = self._buffer_value


class FloatVariable(InputVariable[float]):
    """ Representation for a float valued variable"""
    def __init__(self, variable_name: str, tool_tip: str, display_name: Optional[str]=None,
                       default: float = 0.0, lower_bound: Optional[float] = None, upper_bound: Optional[float] = None):

        super().__init__(variable_name, tool_tip, display_name)

        self.value = default
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound

    def create_qt_input(self) -> QWidget:

        widget = QDoubleSpinBox()

        widget.setRange(self.lower_bound if self.lower_bound is not None else -1e12,
                        self.upper_bound if self.upper_bound is not None else 1e12)
        widget.setValue(self.value)

        widget.setToolTip(self.tool_tip)

        return widget


class IntegerVariable(InputVariable[int]):
    """ Representation for an integer valued variable"""
    def __init__(self, variable_name: str, tool_tip: str, display_name: Optional[str]=None,
                       default: int = 0, lower_bound: Optional[int] = None, upper_bound: Optional[int] = None):

        super().__init__(variable_name, tool_tip, display_name)

        self.value = default
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound

    def create_qt_input(self) -> QWidget:

        widget = QSpinBox()

        widget.setRange(self.lower_bound if self.lower_bound is not None else -2147483648,
                        self.upper_bound if self.upper_bound is not None else 2147483647)
        widget.setToolTip(self.tool_tip)

        widget.setValue(self.value)

        return widget


class BooleanVariable(InputVariable[bool]):
    """ Representation for a float valued variable """

    def __init__(self, variable_name: str, tool_tip: str, display_name: Optional[str] = None, default=True):

        super().__init__(variable_name, tool_tip, display_name)
        self.value = default

    def create_qt_input(self) -> QWidget:
        widget = QCheckBox("")
        widget.setChecked(self.value)
        widget.setToolTip(self.tool_tip)

        return widget


class VariableTable(QWidget):
    """ Qt GUI Widget showing a list of variables """
    def __init__(self, variables: Sequence[InputVariable], auto_update: bool=False, parent=None):
        super().__init__(parent)

        self.variables = variables

        layout = QFormLayout()


        for i, variable in enumerate(self.variables):
            label = variable.create_qt_input_label()
            field = variable.create_qt_input()

            layout.insertRow(i, label, field)

        self.setLayout(layout)



def show_demo():
    """Demo showing the automatic construction of an input dialog"""


    import os
    from PySide6 import QtWidgets
    from PySide6.QtCore import Qt

    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    app = QtWidgets.QApplication([])

    # app.setAttribute(Qt.AA_EnableHighDpiScaling)
    app.setAttribute(Qt.AA_ShareOpenGLContexts)


    mainWindow = QtWidgets.QMainWindow()

    variables = [
        IntegerVariable("x", "Integer Value"),
        FloatVariable("y", "Double Value"),
        BooleanVariable("z", "Boolean Value")]


    mainWidget = VariableTable(variables)

    mainWindow.setCentralWidget(mainWidget)

    mainWindow.show()

    mainWindow.resize(600, 600)
    app.exec()

if __name__ == "__main__":
    show_demo()

