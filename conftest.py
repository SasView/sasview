import os
import platform

import pytest

# We are assuming that the tests are running in a virtual environment with
# sasview, sasmodels and sasdata already installed, perhaps in dev mode
# using "pip install -e".
from sas.system import config

config.override_with_defaults()

@pytest.fixture(scope="session", autouse=True)
def set_env():
    # pytest and numba do not play nicely together on windows, see: https://github.com/numba/numba/issues/8223#issuecomment-1175213066
    if platform.system() == "Windows":
        os.environ["SAS_NUMBA"] = "0"
