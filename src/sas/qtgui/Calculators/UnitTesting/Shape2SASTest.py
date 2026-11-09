"""Shape2SAS tests that don't construct the window.

Constructing DesignWindow needs OpenGL and crashes under the offscreen platform;
see MainWindow/UnitTesting/ToolsTest.py for its construction test.
"""
import numpy as np
import pytest

from sasdata.dataset_types import one_dim
from sasdata.quantities import units

from sas.data_manager import NewDataManager
from sas.qtgui.Calculators.Shape2SAS.DesignWindow import simulatedSAXSToSasData


def test_simulated_saxs_becomes_1d_sasdata():
    q = np.array([0.01, 0.02, 0.03])
    intensity = np.array([10.0, 8.0, 5.0])
    error = np.array([0.1, 0.2, 0.3])

    data = simulatedSAXSToSasData("Model_1", q, intensity, error)

    assert data.name == "Model_1"
    assert data.dataset_type is one_dim
    assert data["Q"].value == pytest.approx(q)
    assert data["Q"].units == units.per_angstrom
    assert data["I"].value == pytest.approx(intensity)
    assert data["I"].units == units.none
    assert np.sqrt(data["I"].variance.value) == pytest.approx(error)


def test_simulated_saxs_can_be_added_to_the_data_manager():
    data = simulatedSAXSToSasData("Model_1", np.array([0.01, 0.02]), np.array([1.0, 2.0]), np.array([0.1, 0.1]))
    manager = NewDataManager()
    manager.add_data(data)
    assert data in manager.all_data
