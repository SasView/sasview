import os.path

import numpy as np
import pytest

from sasdata.dataloader.data_info import Data1D
from sasdata.dataloader.loader import Loader


@pytest.fixture
def linear_data():
    """Linear distribution (y=x) with uncertainties."""
    x = np.asarray([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0])
    y = x.copy()
    dy = y / 10.0
    return Data1D(x=x, y=y, dy=dy)


@pytest.fixture
def real_data():
    """Real 100nm spheres neutron scattering data loaded from file."""
    path = os.path.join(os.path.dirname(__file__), "data", "100nmSpheresNodQ.txt")
    data = Loader().load(path)
    result = data[0]
    result.dxl = None
    return result


@pytest.fixture
def guinier_data():
    """Guinier distribution with scale=1.5 and the radius of gyration Rg=30."""
    scale = 1.5
    rg = 30.0
    x = np.arange(0.0001, 0.1, 0.0001)
    y = scale * np.exp(-((x * rg) ** 2) / 3.0)
    dy = y * 0.1
    return Data1D(x=x, y=y, dy=dy)


@pytest.fixture
def power_law_data():
    """Power law distribution with scale=1.5 and exponent m=3."""
    scale = 1.5
    m = 3.0
    x = np.arange(0.0001, 0.1, 0.0001)
    y = scale * np.power(x, -m)
    dy = y * 0.1
    return Data1D(x=x, y=y, dy=dy)
