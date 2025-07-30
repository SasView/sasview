import json
import logging
import os
from copy import deepcopy
from typing import Any

from packaging.version import InvalidVersion, parse

import sas
import sas.system.version
from sas.system import user
from sas.system.config.schema_elements import CoercionError, SchemaElement, create_schema_element

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
        self._schema: dict[str, SchemaElement] = {}
        self._defaults: dict[str, SchemaElement] = {}
        self._deleted_attributes: list[str] = []
        self._bad_entries: dict[str, Any] = {}
        self._disable_writing = False
        self._meta_attributes = ["_locked", "_schema", "_defaults",
                                 "_deleted_attributes", "_meta_attributes",
                                 "_disable_writing", "_bad_entries"]

    @property
    def defaults(self):
        """ Expose the default values to allow resetting of defaults. No setter should ever be created for this! """
        return self._defaults

    def config_filename(self, create_if_nonexistent=False):
        """Filename for saving config items"""
        version_parts = sas.system.version.__version__.split(".")
        user_dir = user.get_config_dir(create_if_nonexistent)
        return os.path.join(user_dir, f"config-{version_parts[0]}.json")

    def finalise(self):
        """ Call this at the end of the config to make this class 'final'
            and to set up the config file schema"""

        self._schema = self._generate_schema()
        self._defaults = self._state_copy()
        self._locked = True

    def update(self, data: dict[str, Any]):
        """ Set the fields of the config from a dictionary"""

        for key in data:

            # Skip over any deleted attributes
            if key in self._deleted_attributes:
                self._bad_entries[key] = data[key]
                continue

            # Check the variable is in the schema
            if key in self._schema:

                try:
                    coerced = self._schema[key].coerce(data[key])
                    setattr(self, key, coerced)

                except CoercionError as e:
                    logger.error(f"Cannot set set variable '{key}', improper type ({e.message})")

            else:
                logger.warning(f"Unknown config key: '{key}', skipping")
                self._bad_entries[key] = data[key]

    def save(self):
        with open(self.config_filename(True), 'w') as file:
            self.save_to_file_object(file)

    def override_with_defaults(self):
        """
        Set the config entries to defaults, and prevent saving from happening

        Added with the ability to disable for testing in mind
        """
        self._bad_entries.clear()
        self.update(self._defaults)
        self._disable_writing = True

    def save_to_file_object(self, file):
        """ Save config file

        Only changed and unknown variables will be included in the saved file
        """

        if self._disable_writing:
            logger.info("Config write disabled by `override_with_defaults`")

        else:

            data = {}
            for key in self._defaults:
                old_value = self._defaults[key]
                new_value = getattr(self, key)
                if new_value != old_value:
                    data[key] = new_value

            data.update(self._bad_entries)

            output_data = {
                "sasview_version": sas.system.version.__version__,
                "config_data": data}

            json.dump(output_data, file, indent=2)

    def load(self):
        filename = self.config_filename(False)

        if os.path.exists(filename):
            with open(filename) as file:
                self.load_from_file_object(file)

        else:
            logger.warning("No config file found - one will be created when sasview exits")

    def load_from_file_object(self, file):
        """ Load config file """
        data = json.load(file)

        if "sasview_version" not in data:
            raise MalformedFile("Malformed config file - no 'sasview_version' key")

        try:
            file_version = data["sasview_version"]
            parse(file_version)

        except InvalidVersion:
            raise MalformedFile("Malformed version in config file, should be a string matching PEP440 such as 'X.Y.Z'")

        if "config_data" not in data:
            raise MalformedFile("Malformed config file - no 'config_data' key")

        if not isinstance(data["config_data"], dict):
            raise MalformedFile("Malformed config file - expected 'config_data' to be a dictionary")


        # Check major version
        file_major_version = file_version.split(".")[0]
        sasview_major_version = sas.system.version.__version__.split(".")[0]

        if int(file_major_version) != int(sasview_major_version):
            logger.warning(f"Attempting to used outdated config file (config is"
                           f" for {file_version}, this SasView version is {sas.system.version.__version__})")

        self.update(data["config_data"])

    def _state_copy(self) -> dict[str, Any]:
        """ Get a copy of all the data in the config"""
        state: dict[str, Any] = {}
        variables = vars(self)
        for variable_name in variables:
            if variable_name in self._meta_attributes:
                continue

            state[variable_name] = deepcopy(variables[variable_name])

        return state

    def _generate_schema(self) -> dict[str, SchemaElement]:
        """ Auto-generate schema for the current config class and validate config class

        Note: there is an assumption here that the class of the value in the default
        config file is
        """

        schema: dict[str, SchemaElement] = {}
        variables = vars(self)
        for variable_name in variables:
            if variable_name in self._meta_attributes:
                continue

            schema[variable_name] = create_schema_element(variable_name, variables[variable_name])

        return schema

    def __setattr__(self, key, value):

        # This section deals with control variables for the config

        if not hasattr(self, "_meta_attributes") or key in self._meta_attributes:

            # The class is not set up at this point, don't do any checks
            super().__setattr__(key, value)
            return

            # otherwise continue to part that handles values

        # This section deals with config values themselves
        if hasattr(self, "_locked"):
            # Should be initialised...

            if getattr(self, "_locked"):
                # ...and locked

                if key not in self.__dict__:
                    raise ConfigLocked(f"New attribute attempt: {key} = {value}")

                try:
                    super().__setattr__(key, self._schema[key].coerce(value))

                except CoercionError:
                    raise TypeError(f"Tried to set bad value '{value}' to config entry of type '{self._schema[key]}'")

                return

        # Not fully initialised
        super().__setattr__(key, value)

    def validate(self, key, value):
        """ Check whether a value conforms to the type in the schema"""
        return self._schema[key].validate(value)
