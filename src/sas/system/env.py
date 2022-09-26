""" Interface for environment variable access

This is intended to handle any conversion from the environment variable string to more natural types.
"""
import os
import logging

class Envrironment:

    logger = logging.getLogger(__name__)

    @property
    def sas_opencl(self) -> str:
        """
        Get the value of the environment variable SAS_OPENCL, which specifies which OpenCL device
        should be used.
        """

        return os.environ.get("SAS_OPENCL", "none")


    @sas_opencl.setter
    def sas_opencl(self, value: str):
        """
        Set the value of the environment variable SAS_OPENCL
        """

        if value.lower() == "none":
            if "SAS_OPENCL" in os.environ:
                del os.environ["SAS_OPENCL"]
        else:
            os.environ["SAS_OPENCL"] = value

env = Envrironment()