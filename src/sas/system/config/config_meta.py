from typing import Dict, Any, List
import os
import logging
import json
from copy import deepcopy

import sas
from sas.system.config.schema_elements import create_schema_element, CoercionError, SchemaElement

logger = logging.getLogger("sas.config")


class MalformedFile(Exception):
    def __init__(self, message):
        super().__init__(message)


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
        #   they are referenced as strings via _meta_attributes
        #   you need to keep this up to date (probably shouldn't be
        #   changing it anyway)
        self._locked = False
        self._schema: Dict[str, SchemaElement] = {}
        self._defaults: Dict[str, SchemaElement] = {}
        self._deleted_attributes: List[str] = []
        self._write_disabled = False
        self._meta_attributes = ["_locked", "_schema", "_defaults",
                                 "_deleted_attributes", "_meta_attributes", "_write_disabled"]

    def finalise(self):
        """ Call this at the end of the config to make this class 'final'
            and to set up the config file schema"""

        self._schema = self._generate_schema()
        self._defaults = self._state_copy()
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

    def save(self):
        if self._write_disabled:
            logger.error("Write disabled, this is probably because it will overwrite an outdated config.")
            return

        with open("config.json", 'w') as file:
            self.save_to_file_object(file)

    def save_to_file_object(self, file):
        """ Save config file

        Only changed variables will be included in the saved file
        """
        data = {}
        for key in self._defaults:
            old_value = self._defaults[key]
            new_value = getattr(self, key)
            if new_value != old_value:
                data[key] = new_value

        output_data = {
            "sasview_version": sas.__version__,
            "config_data": data}

        json.dump(output_data, file)

    def load(self):
        filename = "config.json"
        if os.path.exists(filename):
            with open("config.json", 'r') as file:
                self.load_from_file_object(file)

    def load_from_file_object(self, file):
        """ Load config file """
        data = json.load(file)

        if "sasview_version" not in data:
            raise MalformedFile("Malformed config file - no 'sasview_version' key")

        try:
            parts = [int(s) for s in data["sasview_version"].split(".")]
            if len(parts) != 3:
                raise Exception

        except Exception:
            raise MalformedFile("Malformed version in config file, should be a string of the form 'X.Y.Z'")

        if "config_data" not in data:
            raise MalformedFile("Malformed config file - no 'config_data' key")

        if not isinstance(data["config_data"], dict):
            raise MalformedFile("Malformed config file - expected 'config_data' to be a dictionary")


        # Check major version
        file_version = data["sasview_version"]
        file_major_version = file_version.split(".")[0]
        sasview_major_version = sas.__version__.split(".")[0]

        if int(file_major_version) != int(sasview_major_version):
            logger.warning(f"Attempting to used outdated config file (config is"
                           f" for {file_version}, this SasView version is {sas.__version__})")
            self._write_disabled = True

        self.update(data["config_data"])

    def _state_copy(self) -> Dict[str, Any]:
        """ Get a copy of all the data in the config"""
        state: Dict[str, Any] = {}
        variables = vars(self)
        for variable_name in variables:
            if variable_name in self._meta_attributes:
                continue

            state[variable_name] = deepcopy(variables[variable_name])

        return state

    def _generate_schema(self) -> Dict[str, SchemaElement]:
        """ Auto-generate schema for the current config class and validate config class

        Note: there is an assumption here that the class of the value in the default
        config file is
        """

        schema: Dict[str, SchemaElement] = {}
        variables = vars(self)
        for variable_name in variables:
            if variable_name in self._meta_attributes:
                continue

            schema[variable_name] = create_schema_element(variable_name, variables[variable_name])

        return schema

    def __setattr__(self, key, value):
        if hasattr(self, "_locked") and self._locked:
            if key not in self.__dict__:
                raise ConfigLocked("New attribute attempt")



        super().__setattr__(key, value)


