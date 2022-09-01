from typing import Optional, Dict, Any
import json
import logging
from sas.config_system.schema_elements import create_schema_element, CoercionError

class ConfigLocked(Exception):
    def __init__(self, message):
        super().__init__(self, f"{message}: The Config class cannot be subclassed or added to dynamically, "
                               "see config class definition for details")


class ConfigMeta(type):
    def __new__(mcs, name, bases, classdict):
        for b in bases:
            if isinstance(b, ConfigMeta):
                raise ConfigLocked("Subclass attempt")
        return type.__new__(mcs, name, bases, dict(classdict))


class ConfigBase:
    """ Base class for Config, keep the definition of config variables and workings as separate as possible """
    def __init__(self):

        # Note on editing the following variables:
        #   they are referenced as strings in functions below
        #   remember that the strings will have to be updated
        self._locked = False
        self._schema = {}
        self._modified_values = set()

    def finalise(self):
        """ Call this to make this class 'final' """

        self._schema = self.generate_schema()
        self._locked = True

    def update(self, data: Dict[str, Any]):
        """ Set the fields of the config from a dictionary"""

        for key in data:

            if key not in self._schema:
                logging.error(f"Unknown config key: '{key}', skipping")

            else:
                try:
                    coerced = self._schema[key].coerce(data[key])
                    setattr(self, key, coerced)

                except CoercionError as e:
                    logging.error(f"Cannot set set variable '{key}', improper type ({e.message})")


    def generate_schema(self):
        """ Auto-generate schema for the current config class and validate config class

        Note: there is an assumption here that the class of the value in the default
        config file is
        """

        schema = {}
        variables = vars(self)
        for variable_name in variables:
            if variable_name in ["_locked", "_schema", "_modified_values"]:
                continue

            schema[variable_name] = create_schema_element(variable_name, variables[variable_name])

        return schema

    def load(self, filename: str):
        pass

    def save(self, filename: Optional[str]=None):
        """ Save the configuration to a file"""
        #TODO: Implement save functionality to yaml (and load, with schema)
        raise NotImplementedError()

    def __setattr__(self, key, value):
        if hasattr(self, "_locked") and self._locked:
            if key not in self.__dict__:
                raise ConfigLocked("New attribute attempt")


        # if not self._locked:
        #     self._modified_values.add(key)

        super().__setattr__(key, value)


