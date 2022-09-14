""" Interface for environment variable access

This is intended to handle any conversion from the environment variable string to more natural types.
"""
import os
import logging

class Envrironment:

    logger = logging.getLogger(__name__)

    @property
    def sas_opencl(self) -> int:
        """
        Get the value of the environment variable SAS_OPENCL, which specifies which OpenCL device
        should be used.

        FAQ: Why use -1 to represent the no-device state, rather than None? Isn't None a better choice?
        Ans: This helps keep the config files in order (see docs on that), as the type of -1 (the default)
             can be inferred and checked online.

        """

        string_value = os.environ.get("SAS_OPENCL", "None")
        if string_value.lower() == "none":
            return -1
        else:
            try:
                int_value = int(string_value)
                return int_value
            except ValueError:
                self.logger.warning(
                    f"Failed to parse SAS_OPENCL environment variable, expected an integer or 'none', got {string_value}")
                return -1

    @sas_opencl.setter
    def sas_opencl(self, value: int):
        """
        Set the value of the environment variable SAS_OPENCL
        """

        if value == -1:
            del os.environ["SAS_OPENCL"]
        else:
            os.environ["SAS_OPENCL"] = str(value)

env = Envrironment()