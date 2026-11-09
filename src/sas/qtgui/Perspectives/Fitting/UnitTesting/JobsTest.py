"""
Background jobs of a fit page (FW-MVC-DESIGN.md §3.3, Phase 7), with fake jobs: a theory
calculation completes when, and in the order, the test says.

- two requests that complete in reverse order: the older is dropped;
- the model or the dataset changes while a calculation is pending (the combo boxes are disabled
  while it is, so the model changes as an undo or a paste would change it: an intent);
- a value edit while a calculation is pending: the result is shown, but is not current;
- undo during a fit, and a model change during a fit;
- closing the page; cancelling (restarting) a fit.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

import numpy as np
import pytest

from sas.qtgui.Perspectives.Fitting import FittingUtilities
from sas.qtgui.Perspectives.Fitting.UnitTesting import golden_support as g


class FakeJobs:
    """Theory calculations that wait for the test."""

    def __init__(self, page) -> None:
        self.pending = []
        page.theory_service.runner = lambda request, complete, use_threads=True: \
            self.pending.append((request, complete))

    def requests(self):
        return [request for request, _ in self.pending]

    def complete(self, request) -> None:
        """Complete *request* with a flat theory curve."""
        complete = next(c for r, c in self.pending if r is request)
        data = request.data
        complete({"x": data.x, "y": np.ones_like(data.x), "model": request.kernel, "data": data,
                  "page_id": 0, "intermediate_results": {}})


@pytest.fixture(autouse=True)
def _quiet(qapp, monkeypatch):
    monkeypatch.setattr("sas.qtgui.Perspectives.UndoRedo.QtWidgets.QMessageBox", MagicMock())
    monkeypatch.setattr(FittingUtilities, "checkConstraints", lambda *a, **kw: None)


@pytest.fixture
def page():
    p = g.new_page(data=g.make_data1d("d1", "data1"))
    p.jobs = FakeJobs(p)
    g.select_model(p, "Cylinder", "cylinder")
    p.jobs.complete(p.jobs.requests()[-1])
    yield p
    p.shadow_checker.assert_ok()
    p.close()


def result_of(page, dataset_id="d1"):
    return page.controller.results.per_dataset.get(dataset_id)


class TheoryJobTest:

    def testReverseOrderCompletionKeepsTheNewest(self, page):
        page.calculateQGridForModel()
        page.calculateQGridForModel()
        first, second = page.jobs.requests()[-2:]
        page.jobs.complete(second)
        page.jobs.complete(first)          # older: superseded, dropped
        assert result_of(page).provenance.request_id == second.request_id
        assert page.controller.current_result() is result_of(page)
        assert page.cmdPlot.isEnabled()

    def testEachRequestHasItsOwnKernel(self, page):
        page.calculateQGridForModel()
        page.calculateQGridForModel()
        first, second = page.jobs.requests()[-2:]
        assert first.kernel is not second.kernel
        g.set_cell(page._model_model, "radius", 1, "33")
        assert first.kernel.getParam("radius") == 20.0

    def testAValueEditWhilePendingMakesTheResultStale(self, page):
        page.calculateQGridForModel()
        request = page.jobs.requests()[-1]
        g.set_cell(page._model_model, "radius", 1, "33")
        page.jobs.complete(request)
        # Shown, as before, but not current
        assert page.model_data is result_of(page).theory
        assert page.controller.current_result() is None
        page.calculateQGridForModel()
        page.jobs.complete(page.jobs.requests()[-1])
        assert page.controller.current_result() is result_of(page)

    def testAModelSwitchWhilePendingDropsTheOldLayout(self, page):
        page.calculateQGridForModel()
        request = page.jobs.requests()[-1]
        page.controller.select_model("Cylinder", "hollow_cylinder")
        newest = page.jobs.requests()[-1]
        assert newest.provenance.layout_generation != request.provenance.layout_generation
        page.jobs.complete(request)
        assert result_of(page).provenance.request_id < request.request_id
        page.jobs.complete(newest)
        assert result_of(page).provenance.request_id == newest.request_id

    def testAModelSwitchOnATheoryPageDropsThePendingResult(self, qapp):
        """No data: a model switch computes no theory, so the old request stays the latest."""
        p = g.new_page()
        jobs = FakeJobs(p)
        g.select_model(p, "Cylinder", "cylinder")
        p.onPlot()
        request = jobs.requests()[-1]
        p.controller.select_model("Cylinder", "hollow_cylinder")
        jobs.complete(request)
        assert result_of(p, request.dataset_id) is None
        assert p.cmdPlot.isEnabled()          # the page is usable again
        p.close()

    def testADatasetSwitchWhilePendingRoutesTheResultByItsDataset(self, qapp):
        p = g.new_page(data=[g.make_data1d("b1", "same"), g.make_data1d("b2", "same")])
        jobs = FakeJobs(p)
        g.select_model(p, "Cylinder", "cylinder")
        on_first = jobs.requests()[-1]
        p.cbFileNames.setCurrentIndex(1)
        on_second = jobs.requests()[-1]
        assert (on_first.dataset_id, on_second.dataset_id) == ("b1", "b2")
        jobs.complete(on_first)
        jobs.complete(on_second)
        assert result_of(p, "b1").theory.name != "" and result_of(p, "b2") is not None
        # The page stays on the dataset it shows (B-4), and each item got its own theory
        assert p.data_index == 1
        for dataset_id, item in zip(p.document.dataset_order, p.all_data):
            assert any(item.child(i).text() == result_of(p, dataset_id).theory.name for i in range(item.rowCount()))
        p.close()

    def testClosingThePageDropsPendingResults(self, page):
        page.calculateQGridForModel()
        request = page.jobs.requests()[-1]
        page.controller.close()
        page.jobs.complete(request)
        assert result_of(page).provenance.request_id < request.request_id

    def testTheEffectiveRadiusIsADerivedWrite(self, qapp):
        p = g.new_page(data=g.make_data1d("d1", "data1"))
        jobs = FakeJobs(p)
        g.select_model(p, "Sphere", "sphere", "hardsphere")
        request = jobs.requests()[-1]
        complete = jobs.pending[-1][1]
        depth = len(p.undo_stack._undo_stack)
        data = request.data
        complete({"x": data.x, "y": np.ones_like(data.x), "model": request.kernel, "data": data,
                  "page_id": 0, "intermediate_results": {"radius_effective": 42.0}})
        assert p.document.parameters["radius_effective"].value == 42.0
        assert len(p.undo_stack._undo_stack) == depth
        # A derived write does not make the result stale
        assert p.controller.current_result() is result_of(p)
        p.close()


def fit_result(fitness=1.0):
    return ([[SimpleNamespace(fitness=fitness)]], 0.5)


class FitJobTest:

    @pytest.fixture
    def fitting(self, page):
        g.set_checked(page._model_model, "radius")
        page.fit_service.outcome = lambda res: {"radius": (25.0, 0.5)}
        page.onPlot = lambda: None
        return page

    def testAFitIsAppliedWithItsRequest(self, fitting):
        request = fitting.controller.start_fit()
        fitting.fitComplete(fit_result(), request)
        assert fitting.document.parameters["radius"].value == 25.0
        assert fitting.controller.jobs.fit is None

    def testUndoDuringAFitKeepsTheResult(self, fitting):
        g.set_cell(fitting._model_model, "length", 1, "300")
        request = fitting.controller.start_fit()
        fitting.undo_stack.undo()          # the length edit: the same layout
        fitting.fitComplete(fit_result(), request)
        assert fitting.document.parameters["length"].value == 400.0
        assert fitting.document.parameters["radius"].value == 25.0

    def testAModelChangeDuringAFitDiscardsTheResult(self, fitting):
        g.select_model(fitting, "Cylinder", "hollow_cylinder")
        fitting.jobs.complete(fitting.jobs.requests()[-1])
        request = fitting.controller.start_fit()
        fitting.undo_stack.undo()          # the model switch: another layout
        assert fitting.document.selection.model == "cylinder"
        radius = fitting.document.parameters["radius"].value
        fitting.fitComplete(fit_result(), request)
        assert fitting.document.parameters["radius"].value == radius
        assert fitting.document.parameters["radius"].error is None
        assert fitting.cmdFit.text() == "Fit"

    def testARestartedFitDropsTheFirstOne(self, fitting):
        first = fitting.controller.start_fit()
        second = fitting.controller.start_fit()
        fitting.fitComplete(fit_result(), first)
        assert fitting.document.parameters["radius"].value == 20.0
        fitting.fitComplete(fit_result(), second)
        assert fitting.document.parameters["radius"].value == 25.0

    def testClosingThePageDropsTheFit(self, fitting):
        request = fitting.controller.start_fit()
        fitting.disableInteractiveElements()
        fitting.controller.close()
        fitting.fitComplete(fit_result(), request)
        assert fitting.document.parameters["radius"].value == 20.0
        assert fitting.cmdFit.text() == "Stop fit"     # untouched: the page is gone
