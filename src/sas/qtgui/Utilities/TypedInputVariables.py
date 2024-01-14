from abc import ABC, abstractmethod
from typing import Optional, Sequence, Generic, TypeVar, Any

from PySide6.QtWidgets import QWidget, QLabel, QDoubleSpinBox, QSpinBox, QCheckBox, QFormLayout, QVBoxLayout
from PySide6.QtCore import Signal

#
# Note on typing: There are some limitations on typing that makes it hard to internally type everything exactly
#                 however, the outward facing types should be mostly all there. One has to be careful nonetheless.
#

class NotInitialised(Exception):
    """ Exception thrown when variables are not initialised (should not happen if coded correctly)"""
    def __init__(self):
        super().__init__("Variable not initialised")


T = TypeVar("T")


class InputVariable(ABC, Generic[T]):
    """
    A variable that contains all the information needed to correctly display in an edit dialog,
    along with appropriate accessors and functions to create appropriate Qt objects.

    Immutable

    """
    def __init__(self,
                 variable_name: str,
                 value: T, tool_tip: str = "",
                 display_name: Optional[str] = None,
                 user_editable: bool = True):

        self.variable_name = variable_name
        self._value = value
        self.display_name = display_name
        self.tool_tip = tool_tip
        self.user_editable=user_editable

    @abstractmethod
    def create_qt_input(self) -> "QtVariableField":
        """ Create an input box for this variable,

        this needs to be a QtVariableField - remember to set the signals up

        :return: A QWidget that works as an input """

    def create_qt_input_label(self) -> QLabel:
        """ Return a label for this variable"""
        label = QLabel(self.variable_name if self.display_name is None else self.display_name)
        label.setToolTip(self.tool_tip)

        return label

    @property
    def value(self) -> T:
        if self._value is None:
            raise NotInitialised()
        else:
            return self._value

    @abstractmethod
    def replace_value(self, value: T):
        """ Get a copy of this variable with the value replaced with a new one"""

    def __repr__(self):
        return f"{self.__class__.__name__}[{self.variable_name, self.value}]"


S = TypeVar("S")


class QtVariableField(QWidget, Generic[S]):
    """ General qt field for entering inputs of a given type """
    variableChanged = Signal()

    def __init__(self, base_variable: S):
        super().__init__()

        # Variable used to build this, the actual value should never be used for anything other than setting up
        self.base_variable = base_variable


    def emitVariableChanged(self):
        """ Send a signal from the variableChanged slot """
        self.variableChanged.emit()

    def getValue(self):
        # TODO Implement metaclass to allow making this abstract
        """ Get the value for this field, should be of a type compatible with the replace_value of variable """
        pass

    def _setValue(self, value):
        # TODO Implement metaclass to allow making this abstract
        pass

    def getVariable(self) -> S:
        """ Get the variable for this field with whatever value has been set """

        return self.base_variable.replace_value(self.getValue())

    def update(self, variables: list[InputVariable[Any]]):
        """ Update field based on variable data"""
        for variable in variables:
            if self.base_variable.variable_name == variable.variable_name:
                self._setValue(variable.value)


U = TypeVar("U")

class MutableInputVariableContainer(Generic[U]):
    """ A container for input variables that is mutable, to allow for updating """
    def __init__(self, variable: InputVariable[U]):
        self.variable = variable

    @property
    def value(self) -> U:
        return self.variable.value

    def updateFromVariable(self, input_variable: InputVariable[Any]):
        """ Update the state based on an (immutable) input variable"""
        if input_variable.variable_name == self.variable.variable_name:
            self.variable = input_variable

    def updateFromList(self, input_variables: list[InputVariable[Any]]):
        """ Update the state based on a list of (immutable) input variables"""
        for variable in input_variables:
            self.updateFromVariable(variable)



class FloatVariable(InputVariable[float]):
    """ Representation for a float valued variable"""
    def __init__(self, variable_name: str, value: float=0.0, tool_tip: str="", display_name: Optional[str]=None,
                       lower_bound: Optional[float] = None, upper_bound: Optional[float] = None,
                       user_editable: bool = True):

        super().__init__(variable_name=variable_name,
                         value=value,
                         tool_tip=tool_tip,
                         display_name=display_name,
                         user_editable=user_editable)

        self.lower_bound = lower_bound
        self.upper_bound = upper_bound

    def create_qt_input(self) -> "FloatVariableField":

        return FloatVariableField(self)

    def replace_value(self, value: float):
        return FloatVariable(variable_name=self.variable_name,
                             tool_tip=self.tool_tip,
                             display_name=self.display_name,
                             value=value,
                             lower_bound=self.lower_bound,
                             upper_bound=self.upper_bound,
                             user_editable=self.user_editable)


class FloatVariableField(QtVariableField[FloatVariable]):
    """ Input field associated with float variable """
    def __init__(self, variable: FloatVariable):

        super().__init__(variable)

        self.spinner = QDoubleSpinBox()
        self.spinner.setRange(variable.lower_bound if variable.lower_bound is not None else -1e12,
                              variable.upper_bound if variable.upper_bound is not None else 1e12)
        self.spinner.setValue(variable.value)
        self.spinner.setEnabled(variable.value)
        self.spinner .setToolTip(variable.tool_tip)

        self.spinner.valueChanged.connect(self.emitVariableChanged)

        layout = QVBoxLayout()
        layout.addWidget(self.spinner)
        self.setLayout(layout)

    def getValue(self) -> float:
        return self.spinner.value()

    def _setValue(self, value):
        self.spinner.setValue(value)


class IntegerVariable(InputVariable[int]):
    """ Representation for an integer valued variable"""
    def __init__(self, variable_name: str, value: int=0, tool_tip: str="", display_name: Optional[str]=None,
                 lower_bound: Optional[int] = None, upper_bound: Optional[int] = None,
                 user_editable: bool = True):

        super().__init__(variable_name=variable_name,
                         value=value,
                         tool_tip=tool_tip,
                         display_name=display_name,
                         user_editable=user_editable)

        self.lower_bound = lower_bound
        self.upper_bound = upper_bound

    def create_qt_input(self) -> QWidget:

        return IntegerVariableField(self)

    def replace_value(self, value: int):
        return IntegerVariable(variable_name=self.variable_name,
                               value=value,
                               tool_tip=self.tool_tip,
                               display_name=self.display_name,
                               lower_bound=self.lower_bound,
                               upper_bound=self.upper_bound,
                               user_editable=self.user_editable)


class IntegerVariableField(QtVariableField[IntegerVariable]):
    """ Input field associated with float variable """
    def __init__(self, variable: IntegerVariable):

        super().__init__(variable)

        self.spinner = QSpinBox()
        self.spinner.setRange(variable.lower_bound if variable.lower_bound is not None else -2147483648,
                              variable.upper_bound if variable.upper_bound is not None else 2147483647)
        self.spinner.setToolTip(variable.tool_tip)
        self.spinner.setValue(variable.value)
        self.spinner.setEnabled(variable.user_editable)
        self.spinner.valueChanged.connect(self.emitVariableChanged)

        layout = QVBoxLayout()
        layout.addWidget(self.spinner)
        self.setLayout(layout)

    def getValue(self) -> int:
        return self.spinner.value()

    def _setValue(self, value):
        self.spinner.setValue(value)


class BooleanVariable(InputVariable[bool]):
    """ Representation for a float valued variable """

    def __init__(self, variable_name: str, value: bool = True, tool_tip: str = "", display_name: Optional[str] = None,
                 user_editable: bool=True):

        super().__init__(variable_name=variable_name,
                         value=value,
                         tool_tip=tool_tip,
                         display_name=display_name,
                         user_editable=user_editable)

    def create_qt_input(self):
        return BooleanVariableField(self)

    def replace_value(self, value: bool):
        return BooleanVariable(variable_name=self.variable_name,
                               value=value,
                               tool_tip=self.tool_tip,
                               display_name=self.display_name,
                               user_editable=self.user_editable)


class BooleanVariableField(QtVariableField[BooleanVariable]):
    """ Input field associated with float variable """
    def __init__(self, variable: BooleanVariable):

        super().__init__(variable)
        self.checkbox = QCheckBox("")
        self.checkbox.setChecked(variable.value)
        self.checkbox.setEnabled(variable.user_editable)
        self.checkbox.setToolTip(variable.tool_tip)

        layout = QVBoxLayout()
        layout.addWidget(self.checkbox)
        self.setLayout(layout)

    def getValue(self) -> bool:
        return self.checkbox.isChecked()

    def _setValue(self, value):
        self.checkbox.setChecked(value)

class VariableTable(QWidget):
    """ Qt GUI Widget showing a list of variables """

    variablesChanged = Signal()

    def __init__(self, variables: Sequence[InputVariable], parent=None):
        super().__init__(parent)

        self.variables = variables
        self.fields = []

        # Create rows of entries in table
        layout = QFormLayout()

        for i, variable in enumerate(self.variables):
            label = variable.create_qt_input_label()
            field = variable.create_qt_input()
            field.variableChanged.connect(self.emitVariablesChanged)

            self.fields.append(field)

            layout.insertRow(i, label, field)

        self.setLayout(layout)

    def emitVariablesChanged(self):
        self.variablesChanged.emit()

    def getVariables(self) -> list[InputVariable[Any]]:
        return [field.getVariable() for field in self.fields]

    def updateVariables(self, variables: list[InputVariable[Any]]):
        for field in self.fields:
            field.update(variables)


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
        IntegerVariable("x", tool_tip="Integer Value"),
        FloatVariable("y", tool_tip= "Double Value"),
        BooleanVariable("z",tool_tip= "Boolean Value")]


    mainWidget = VariableTable(variables)

    def callback():
        print("Update")
        for variable in mainWidget.getVariables():
            print("  ", variable)

    mainWidget.variablesChanged.connect(callback)

    mainWindow.setCentralWidget(mainWidget)

    mainWindow.show()

    mainWindow.resize(600, 600)
    app.exec()


if __name__ == "__main__":
    show_demo()

