"""
FitPerspectiveCoordinator (FW-MVC-DESIGN.md §3.5, Phase 7): rename, invalidation of constraints
on other pages (register C-1), and the simultaneous fit's routing by page id.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from sas.qtgui.Perspectives.Fitting.Constraint import Constraint
from sas.qtgui.Perspectives.Fitting.coordinator import FitPerspectiveCoordinator
from sas.qtgui.Perspectives.Fitting.UnitTesting import golden_support as g


@pytest.fixture(autouse=True)
def _quiet(qapp, monkeypatch):
    monkeypatch.setattr("sas.qtgui.Perspectives.UndoRedo.QtWidgets.QMessageBox", MagicMock())


@pytest.fixture
def pages():
    """M1 and M2, cylinders; M2's radius = M1.radius and length = M1.length."""
    first = g.new_page(tab_id=1, data=g.make_data1d("d1", "data1"))
    second = g.new_page(tab_id=2, data=g.make_data1d("d2", "data2"))
    for p in (first, second):
        g.select_model(p, "Cylinder", "cylinder")
    for key in ("radius", "length"):
        second.controller.set_constraint(key, Constraint(param=key, func=f"M1.{key}", value_ex=f"M1.{key}"), fit=True)
    yield [first, second]
    for p in (first, second):
        p.shadow_checker.assert_ok()
        p.close()


@pytest.fixture
def coordinator(pages):
    messages, changed = [], []
    coordinator = FitPerspectiveCoordinator(lambda: pages, messages.append, lambda: changed.append(True))
    coordinator.messages, coordinator.changed = messages, changed
    for p in pages:
        coordinator.add_page(p)
    return coordinator


def active(page, key):
    return page.document.parameters[key].constraint.active


class RenameTest:

    def testANameMustBeNonEmptyAndUnique(self, pages, coordinator):
        first, _ = pages
        assert coordinator.rename(first, "") == "Please use a non-empty name."
        assert coordinator.rename(first, "M2") == "Please use a unique name."
        assert first.document.identity.mnemonic == "M1"

    def testEveryPageFollowsARename(self, pages, coordinator):
        first, second = pages
        assert coordinator.rename(first, "sample") is None
        assert first.document.identity.mnemonic == first.kernel().name == "sample"
        assert second.document.parameters["radius"].constraint.func == "sample.radius"
        assert active(second, "radius") and active(second, "length")


class ConstraintTest:

    def testSymbolsAndActiveConstraintsOfEveryPage(self, pages, coordinator):
        first, second = pages
        symbols = coordinator.symbols()
        assert {"M1.radius", "M2.radius"} <= set(symbols)
        assert not any(name.startswith("M1.") for name in coordinator.symbols(exclude=first))
        assert coordinator.active_constraints() == [("M2.radius", "M1.radius"), ("M2.length", "M1.length")]

    def testANewConstraintIsCheckedAgainstEveryPage(self, pages, coordinator):
        first, second = pages
        assert coordinator.add_constraint(first, "scale", Constraint(param="scale", func="M2.scale")) == []
        assert first.document.parameters["scale"].constraint.func == "M2.scale"
        assert first.document.parameters["scale"].fit
        assert coordinator.messages[-1] == "Constraint added"
        # A cycle across the pages: M1.radius = M2.radius, and M2.radius = M1.radius already
        errors = coordinator.add_constraint(first, "radius", Constraint(param="radius", func="M2.radius"))
        assert errors and first.document.parameters["radius"].constraint is None
        assert "M3.sld" in coordinator.add_constraint(first, "sld", Constraint(param="sld", func="M3.sld"))

    def testAChangeOfConstraintsRefreshesTheConstraintTab(self, pages, coordinator):
        first, _ = pages
        coordinator.changed.clear()
        first.controller.set_constraint("scale", Constraint(param="scale", func="M2.scale"))
        assert coordinator.changed
        coordinator.changed.clear()
        first.controller.remove_constraint("scale")
        assert coordinator.changed

    def testNames(self, pages, coordinator):
        first, second = pages
        assert coordinator.check_name(first, "M1") is None
        assert coordinator.check_name(None, "M1") == "Please use a unique name."
        assert coordinator.check_name(second, "") == "Please use a non-empty name."


class InvalidationTest:

    def testConstraintsOnAParameterThatWentAwayAreDeactivated(self, pages, coordinator):
        first, second = pages
        g.select_model(first, "Sphere", "sphere")       # radius stays, length goes
        assert active(second, "radius")
        assert not active(second, "length")
        assert second.document.parameters["length"].constraint.func == "M1.length"   # kept, not deleted
        assert coordinator.messages and "M2.length" in coordinator.messages[-1]
        assert coordinator.changed

    def testAPageThatClosesDeactivatesTheConstraintsOnIt(self, pages, coordinator):
        first, second = pages
        coordinator.remove_page(first)
        pages.remove(first)
        assert not active(second, "radius") and not active(second, "length")
        pages.append(first)          # closed at teardown

    def testAChangeWithinTheLayoutDeactivatesNothing(self, pages, coordinator):
        first, second = pages
        g.set_cell(first._model_model, "radius", 1, "33")
        g.select_model(first, "Cylinder", "hollow_cylinder")
        assert active(second, "radius") and active(second, "length")
        assert not coordinator.messages


class SimultaneousFitTest:

    def testResultsAreRoutedByPageId(self, pages, coordinator, monkeypatch):
        first, second = pages
        for p in pages:
            g.set_checked(p._model_model, "scale")
        fitter = g._RecordingFit()
        g._RecordingFit.calls = []
        coordinator.prepare_simultaneous_fit(fitter, [(first, 1.0), (second, 1.0)])
        assert [call["fit_id"] for call in g._RecordingFit.calls] == [0, 1]
        assert coordinator.fit_pages() == [[first.page_id], [second.page_id]]
        routed = []
        for p in pages:
            monkeypatch.setattr(p, "fitComplete", lambda result, p=p: routed.append((p, result)))
        results = [SimpleNamespace(model=SimpleNamespace(name="M1")), SimpleNamespace(model=SimpleNamespace(name="M2"))]
        pages.reverse()              # the page order does not matter
        coordinator.route_fit_results(results, 0.5)
        assert [(p, r[0][0][0]) for p, r in routed] == [(first, results[0]), (second, results[1])]

    def testAPageClosedDuringTheFitGetsNothing(self, pages, coordinator, monkeypatch):
        first, second = pages
        for p in pages:
            g.set_checked(p._model_model, "scale")
        coordinator.prepare_simultaneous_fit(g._RecordingFit(), [(first, 1.0), (second, 1.0)])
        routed = []
        monkeypatch.setattr(second, "fitComplete", lambda result: routed.append(result))
        pages.remove(first)
        coordinator.route_fit_results([SimpleNamespace(model=SimpleNamespace(name="M1")),
                                       SimpleNamespace(model=SimpleNamespace(name="M2"))], 0.5)
        assert len(routed) == 1
        pages.append(first)
