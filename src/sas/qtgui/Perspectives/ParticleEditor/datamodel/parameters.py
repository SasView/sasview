from enum import Enum
from typing import NamedTuple


class ValueSource(Enum):
    """ Item that decribes where the current parameter came from"""
    DEFAULT = 0
    CODE = 1
    MANUAL = 2
    FIT = 3

class Parameter:
    """ Base class for parameter descriptions """
    is_function_parameter = False

    def __init__(self, name: str, value: float):
        self.name = name
        self.value = value

    @property
    def in_use(self):
        return True

    @in_use.setter
    def in_use(self, value):
        raise Exception("in_use is fixed for this parameter, you should not be trying to set it")

    def __repr__(self):
        in_use_string = "used" if self.in_use else "not used"
        return f"FunctionParameter({self.name}, {self.value}, {in_use_string})"

class FunctionParameter(Parameter):
    is_function_parameter = True

    def __init__(self, name: str, value: float, in_use: bool, set_by: ValueSource):
        """ Representation of an input parameter to the sld

        The set_by variable describes what the last thing to set it was,
        this allows it to be updated in a sensible way - it should
        only have its value changed by the code if it was set by the code,
        or if it has been set to a default value because nothing specified it.
        """
        super().__init__(name, value)
        self._in_use = in_use
        self.set_by = set_by
    @property
    def in_use(self):
        return self._in_use

    @in_use.setter
    def in_use(self, value):
        self._in_use = value

    def __repr__(self):
        in_use_string = "used" if self.in_use else "not used"
        return f"FunctionParameter({self.name}, {self.value}, {in_use_string}, {self.set_by})"

#
# Parameters that exist for all calculations
#


class SolventSLD(Parameter):
    """ Parameter representing the solvent SLD, always present"""
    def __init__(self):
        super().__init__("Solvent SLD", 0.0)


class Background(Parameter):
    """ Parameter representing the background intensity, always present"""
    def __init__(self):
        super().__init__("Background Intensity", 0.0001)


class Scale(Parameter):
    """ Parameter representing the scaling, always present"""
    def __init__(self):
        super().__init__("Intensity Scaling", 1.0)


class MagnetismParameterContainer(NamedTuple):
    """ Entry describing a magnetism parameter, keeps track of whether it should be linked to an SLD parameter"""
    parameter: FunctionParameter
    linked: bool


class CalculationParameters(NamedTuple):
    """ Object containing the parameters for a simulation"""
    solvent_sld: float
    background: float
    scale: float
    sld_parameters: dict
    magnetism_parameters: dict


