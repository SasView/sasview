"""
The services of a fit page (FW-MVC-DESIGN.md §3.2 to §3.4, Phase 7): the smearer of a request,
the resolution a dataset carries, the plot and dataset factories, the model catalog and the
reading of a fit result.
"""
from types import SimpleNamespace

import numpy as np
import pytest

from sasmodels.resolution import Pinhole1D, Slit1D

from sas.qtgui.Perspectives.Fitting.FittingConstants import CATEGORY_CUSTOM, CATEGORY_STRUCTURE, SUPPRESSED_MODELS
from sas.qtgui.Perspectives.Fitting.model.catalog import ModelCatalog
from sas.qtgui.Perspectives.Fitting.model.parameters import FitOptions, Smearing
from sas.qtgui.Perspectives.Fitting.services import plots
from sas.qtgui.Perspectives.Fitting.services.fit import FitService
from sas.qtgui.Perspectives.Fitting.services.theory import build_smearer, resolution_of
from sas.qtgui.Perspectives.Fitting.UnitTesting.document_fixtures import BUILDER, d1, page
from sas.qtgui.Perspectives.Fitting.UnitTesting.golden_data import make_data1d, make_data2d


def with_dq(data, percent=5.0):
    data.dx = percent / 100.0 * data.x
    return data


@pytest.fixture
def kernel():
    return BUILDER.build(page("Cylinder", "cylinder", data=[d1()]))


class SmearerTest:

    def testNoneAndMissingData(self, kernel):
        assert build_smearer(Smearing("None"), make_data1d("d", "d"), kernel) is None
        assert build_smearer(Smearing("Custom Pinhole Smear", d_up=5.0), None, kernel) is None
        assert build_smearer(Smearing("Custom Pinhole Smear", d_up=0.0), make_data1d("d", "d"), kernel) is None

    def testTheDataResolution(self, kernel):
        smearer = build_smearer(Smearing("Use dQ Data"), with_dq(make_data1d("d", "d")), kernel)
        assert isinstance(smearer.resolution, Pinhole1D) and smearer.model is kernel
        assert build_smearer(Smearing("Use dQ Data"), make_data1d("d", "d"), kernel) is None

    def testACustomPinholeLeavesTheDataAlone(self, kernel):
        data = make_data1d("d", "d")
        smearer = build_smearer(Smearing("Custom Pinhole Smear", d_up=5.0), data, kernel)
        assert isinstance(smearer.resolution, Pinhole1D)
        assert data.dx is None

    def testASlitTakesTheLargerValueAsItsLength(self, kernel):
        data = make_data1d("d", "d")
        swapped = build_smearer(Smearing("Custom Slit Smear", d_down=0.5, d_up=0.01), data, kernel)
        right = build_smearer(Smearing("Custom Slit Smear", d_down=0.01, d_up=0.5), data, kernel)
        assert isinstance(swapped.resolution, Slit1D)
        assert np.allclose(swapped.resolution.q_calc, right.resolution.q_calc)

    def testA2DPinholeHasTheTabsAccuracy(self, kernel):
        smearer = build_smearer(Smearing("Custom Pinhole Smear", accuracy="High", d_up=5.0),
                                make_data2d("d", "d"), kernel)
        assert smearer.accuracy == "high"

    def testResolutionOfTheData(self):
        assert resolution_of(with_dq(make_data1d("d", "d"))) == "Pinhole"
        assert resolution_of(make_data1d("d", "d")) is None
        assert resolution_of(make_data1d("s", "s", sesans=True)) == "Hankel Transform"
        assert resolution_of(None) is None


class PlotsTest:

    def testDefaultDatasets(self):
        log = plots.default_dataset(FitOptions(0.001, 0.5, 50, True), False, 3)
        assert len(log.x) == 50 and log.x[0] == pytest.approx(0.001) and log.x[-1] == pytest.approx(0.5)
        assert (log.id, log.group_id, log.is_data) == ("3 data", "3 Model1D", False)
        linear = plots.default_dataset(FitOptions(0.0, 0.5, 11, False), False, 3)
        assert linear.x[1] == pytest.approx(0.05)
        two_d = plots.default_dataset(FitOptions(0.0, 0.5, 10, False), True, 3)
        assert len(two_d.data) == 100 and two_d.xmax == pytest.approx(0.5 / np.sqrt(2))

    def testDataRangeAndErrors(self):
        data = make_data1d("d", "d")
        assert plots.data_range(data) == (pytest.approx(0.005), pytest.approx(0.4), 40)
        assert plots.data_range(make_data2d("d", "d"))[0] == 0
        assert plots.has_errors(data)
        data.dy = np.zeros(40)
        assert not plots.has_errors(data)

    def testTheoryAndComponentPlots(self, kernel):
        data = make_data1d("d", "data")
        return_data = {"x": data.x, "y": np.ones(40), "model": kernel, "data": data,
                       "intermediate_results": {"P(Q)": np.ones(40), "radius_effective": 12.0}}
        theory = plots.theory_1d(return_data, 4)
        assert (theory.name, theory.id) == ("M1 [data]", "4 cylinder")
        assert [p.name for p in plots.product_plots(return_data, 4)] == ["M1 P(Q) [data]"]
        assert plots.scalar_results(return_data) == {"radius_effective": 12.0}


class CatalogTest:

    @pytest.fixture(scope="class")
    def catalog(self):
        plugin = SimpleNamespace(is_structure_factor=True)
        return ModelCatalog(lambda: {"my_plugin": plugin})

    def testCategoriesAndModels(self, catalog):
        names = catalog.category_names()
        assert names[-1] == CATEGORY_STRUCTURE and "Cylinder" in names and CATEGORY_CUSTOM in names
        models = catalog.models_in("Cylinder")
        assert "cylinder" in models and models == sorted(models)
        assert not set(models) & set(SUPPRESSED_MODELS)

    def testStructureFactorsCanBeLoaded(self, catalog):
        factors = catalog.structure_factors()
        assert "hardsphere" in factors and "my_plugin" in factors
        assert all(name in catalog.models for name in factors)

    def testPluginsAreReloadedInPlace(self, catalog):
        models = catalog.models
        catalog._plugin_models = lambda: {}
        catalog.reload_plugins()
        assert catalog.models is models and "my_plugin" not in models

    def testModelsSasmodelsNoLongerHasAreDropped(self, catalog):
        catalog.categories["Cylinder"].append(["no_such_model", True])
        catalog.regenerate()
        assert "no_such_model" not in catalog.models_in("Cylinder")


class FitOutcomeTest:

    def testValuesAndErrors(self):
        result = SimpleNamespace(pvec=[1.5, 2.0], fitness=1.0, mesg="", param_list=["a", "b"], stderr=[0.1, 0.2])
        assert FitService.outcome(result) == {"a": (1.5, 0.1), "b": (2.0, 0.2)}

    def testAFitThatDidNotConverge(self):
        result = SimpleNamespace(pvec=[np.inf], fitness=1.0, mesg=" (diverged)", param_list=["a"], stderr=[0.1])
        assert FitService.outcome(result) is None
