from typing import Optional, Dict, Any, List
import json
import logging
from sas.config_system.schema_elements import create_schema_element, CoercionError, SchemaElement



logger = logging.getLogger("sas.config_system")

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
        self._schema: Dict[str, SchemaElement] = {}
        self._deleted_attributes: List[str] = []

    def finalise(self):
        """ Call this at the end of the config to make this class 'final'
            and to set up the config file schema"""

        self._schema = self.generate_schema()
        self._locked = True

    def update(self, data: Dict[str, Any]):
        """ Set the fields of the config from a dictionary"""

        for key in data:

            # Skip over any deleted attributes
            if key in self._deleted_attributes:
                continue

            # Check the variable is in the schema
            if key in self._schema:

                try:
                    coerced = self._schema[key].coerce(data[key])
                    setattr(self, key, coerced)

                except CoercionError as e:
                    logger.error(f"Cannot set set variable '{key}', improper type ({e.message})")

            else:
                logger.error(f"Unknown config key: '{key}', skipping")


    def generate_schema(self):
        """ Auto-generate schema for the current config class and validate config class

        Note: there is an assumption here that the class of the value in the default
        config file is
        """

        schema = {}
        variables = vars(self)
        for variable_name in variables:
            if variable_name in ["_locked", "_schema", "_deleted_attributes"]:
                continue

            schema[variable_name] = create_schema_element(variable_name, variables[variable_name])

        return schema

    def load(self, file_object: StringIO):

        # TODO: Add check for major version change

        {}

        pass

    def save(self, file_object: StringIO):
        """ Save the configuration to a file"""
        #TODO: Implement save functionality to yaml (and load, with schema)
        raise NotImplementedError()

    def __setattr__(self, key, value):
        if hasattr(self, "_locked") and self._locked:
            if key not in self.__dict__:
                raise ConfigLocked("New attribute attempt")

        super().__setattr__(key, value)


