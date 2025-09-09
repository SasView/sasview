import os
import platform

import pytest
from run import prepare

from src.sas.system import config

prepare()

config.override_with_defaults()


@pytest.fixture(scope="session", autouse=True)
def set_env():
    # pytest and numba do not play nicely together on windows, see: https://github.com/numba/numba/issues/8223#issuecomment-1175213066
    if platform.system() == "Windows":
        os.environ["SAS_NUMBA"] = "0"
