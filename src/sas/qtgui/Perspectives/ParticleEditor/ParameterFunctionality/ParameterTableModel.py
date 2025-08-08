
""" Code that handles the parameter list backend """

import inspect

from sas.qtgui.Perspectives.ParticleEditor.datamodel.parameters import (
    Background,
    CalculationParameters,
    FunctionParameter,
    MagnetismParameterContainer,
    Scale,
    SolventSLD,
    ValueSource,
)
from sas.qtgui.Perspectives.ParticleEditor.datamodel.types import MagnetismFunction, SLDFunction


class LinkingImpossible(Exception):
    pass

class ParameterTableModel:
    """
    Parameter list backend

    The main issues that this class needs to deal with
     1) Having values that don't get overridden arbitrarily
     2) Magnetism and SLD may or may not have different values for the same parameter name
     """

    def __init__(self):
        # General parameters that are always there
        self.solvent_sld_parameter = SolventSLD()
        self.background_parameter = Background()
        self.scale_parameter = Scale()

        self.fixed_parameters = [
            self.solvent_sld_parameter,
            self.background_parameter,
            self.scale_parameter]

        self._sld_parameters: dict[str, FunctionParameter] = {}
        self._magnetism_parameters: dict[str, MagnetismParameterContainer] = {}

    @property
    def sld_parameters(self):
        sorted_keys = sorted(self._sld_parameters.keys())
        return [self._sld_parameters[key] for key in sorted_keys]

    @property
    def magnetism_parameters(self):
        sorted_keys = sorted(self._magnetism_parameters.keys())
        return [self._magnetism_parameters[key] for key in sorted_keys]

    def can_link(self, name: str):
        """ Can a magnetism be linked to an SLD parameter? """
        return (name in self._magnetism_parameters) and (name in self._sld_parameters)

    def set_link_status(self, name: str, linked: bool):
        """ Set the status of the link of a magnetism to a SLD parameter"""

        if name not in self._magnetism_parameters:
            raise LinkingImpossible(f"{name} is not a magnetic parameter")

        if linked:
            if name not in self._sld_parameters:
                raise LinkingImpossible(f"Cannot link parameters with name '{name}' - not an SLD parameter")

        self._magnetism_parameters[name].linked = linked

    def update_from_code(self, sld: SLDFunction, magnetism: MagnetismFunction | None):
        """ Update the parameter list with sld and magnetism functions """

        # Mark all SLD/magnetism parameters as not in use, we'll mark them as in use if
        # they are there in the functions passed here
        for key in self._sld_parameters:
            self._sld_parameters[key].in_use = False

        for key in self._magnetism_parameters:
            self._magnetism_parameters[key].parameter.in_use = False

        #
        # Update base on the SLD function
        #

        sig = inspect.signature(sld)
        function_parameters = list(sig.parameters.items())

        if len(function_parameters) < 3:
            raise ValueError("SLD Function must have at least 3 parameters")

        # First 3 don't count
        # This is not quite the same as what we need to do for magnetism
        for parameter_name, parameter_details in function_parameters[3:]:

            if parameter_name in self._sld_parameters:
                #
                # Parameter exists
                #

                param_model = self._sld_parameters[parameter_name]

                # Do we want to update the value? Depends on how it was set
                if parameter_details.default is not inspect.Parameter.empty:
                    if param_model.set_by == ValueSource.DEFAULT or param_model.set_by == ValueSource.CODE:
                        param_model.value = parameter_details.default
                        param_model.set_by = ValueSource.CODE

                param_model.in_use = True

            else:

                #
                # Parameter does not exist
                #

                if parameter_details.default is not inspect.Parameter.empty:
                    new_parameter = FunctionParameter(
                        name=parameter_name,
                        value=parameter_details.default,
                        in_use=True,
                        set_by=ValueSource.CODE)

                else:
                    new_parameter = FunctionParameter(
                        name=parameter_name,
                        value=1.0,
                        in_use=True,
                        set_by=ValueSource.DEFAULT)

                self._sld_parameters[parameter_name] = new_parameter

        #
        # Magnetism parameters
        #

        if magnetism is not None:
            sig = inspect.signature(magnetism)
            function_parameters = list(sig.parameters.items())

            if len(function_parameters) < 3:
                raise ValueError("SLD Function must have at least 3 parameters")

            # Again, first 3 don't count
            for parameter_name, parameter_details in function_parameters[3:]:

                if parameter_name in self._magnetism_parameters:

                    #
                    # Parameter exists
                    #

                    param_entry = self._magnetism_parameters[parameter_name]
                    param_model = param_entry.parameter

                    # Do we want to update the value? Depends on how it was set
                    if parameter_details.default is not inspect.Parameter.empty:
                        if param_model.set_by == ValueSource.DEFAULT or param_model.set_by == ValueSource.CODE:
                            param_model.value = parameter_details.default
                            param_model.set_by = ValueSource.CODE

                    param_model.in_use = True

                    # Linking status should be unchanged

                else:

                    #
                    # Parameter does not exist
                    #

                    if parameter_details.default is not inspect.Parameter.empty:
                        new_parameter = FunctionParameter(
                            name=parameter_name,
                            value=parameter_details.default,
                            in_use=True,
                            set_by=ValueSource.CODE)

                        # If it has a default, don't link it
                        new_entry = MagnetismParameterContainer(new_parameter, linked=False)

                    else:

                        new_parameter = FunctionParameter(
                            name=parameter_name,
                            value=1.0,
                            in_use=True,
                            set_by=ValueSource.DEFAULT)

                        # If it does not have a default,
                        # link it as long as there is a corresponding SLD parameter

                        if parameter_name in self._sld_parameters:
                            new_entry = MagnetismParameterContainer(new_parameter, linked=True)
                        else:
                            new_entry = MagnetismParameterContainer(new_parameter, linked=False)

                    self._magnetism_parameters[parameter_name] = new_entry

    def clean(self):
        """ Remove parameters that are not in use"""
        for key in self._sld_parameters:
            if not self._sld_parameters[key].in_use:
                del self._sld_parameters[key]

        for key in self._magnetism_parameters:
            if not self._magnetism_parameters[key].parameter.in_use:
                del self._magnetism_parameters[key]

        # For magnetic parameters that are linked to SLDs, check that
        # what they are linked to still exists, if not, remove the link flag
        for key in self._magnetism_parameters:
            if self._magnetism_parameters[key].linked:
                if key not in self._sld_parameters:
                    self._magnetism_parameters[key].linked = False

    def calculation_parameters(self) -> CalculationParameters:
        sld_parameters = {key: self._sld_parameters[key].value
                           for key in self._sld_parameters
                           if self._sld_parameters[key].in_use}

        # Currently assume no bad linking
        magnetic_parameters_linked: dict[str, FunctionParameter] = \
            {key: self._sld_parameters[key]
                    if self._magnetism_parameters[key].linked
                    else self._magnetism_parameters[key].parameter
                for key in self._magnetism_parameters}

        magnetism_parameters = {key: magnetic_parameters_linked[key].value
                                 for key in magnetic_parameters_linked
                                 if magnetic_parameters_linked[key].in_use}

        return CalculationParameters(
            solvent_sld=self.solvent_sld_parameter.value,
            background=self.background_parameter.value,
            scale=self.scale_parameter.value,
            sld_parameters=sld_parameters,
            magnetism_parameters=magnetism_parameters
        )

def main():

    def test_function_1(x, y, z, a, b, c=7): pass
    def test_function_2(x, y, z, a, d=2, c=5): pass

    param_list = ParameterTableModel()
    param_list.update_from_code(test_function_1, None)
    param_list.update_from_code(test_function_2, None)
    param_list.update_from_code(test_function_2, test_function_1)

    for parameter in param_list.sld_parameters:
        print(parameter)

    for parameter in param_list.magnetism_parameters:
        print(parameter)

if __name__ == "__main__":
    main()
