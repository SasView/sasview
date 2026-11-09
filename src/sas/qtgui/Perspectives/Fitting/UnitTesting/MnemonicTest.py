"""
Register R-3, fixed in Phase 3a (FW-MVC-DESIGN.md §6): a renamed page mnemonic survives
save and reload, and model or S(Q) switches, so constraints between pages keep resolving.
"""
import json
from unittest.mock import MagicMock

import pytest

from sas.qtgui.Perspectives.Fitting.services import constraints as constraint_service
from sas.qtgui.Perspectives.Fitting.UnitTesting import golden_support as g
from sas.qtgui.Perspectives.Fitting.UnitTesting.fitting_test_support import dummy_manager
from sas.qtgui.Utilities import GuiUtils
from sas.sascalc.fit.BumpsFitting import BumpsFit, ParameterExpressions, SasFitness


@pytest.fixture(autouse=True)
def _quiet(qapp, monkeypatch):
    monkeypatch.setattr("sas.qtgui.Perspectives.UndoRedo.QtWidgets.QMessageBox", MagicMock())


@pytest.fixture
def opened():
    """Pages a test opens, closed after the shadow checks."""
    pages = []
    yield pages
    for page in pages:
        page.shadow_checker.assert_ok()
        page.close()


@pytest.fixture
def renamed(opened):
    """The golden two-page case: page 1 renamed 'sample' (radius 33), page 2's radius = sample.radius."""
    first, second = g.case_two_pages()
    g.set_cell(first._model_model, "radius", 1, "33.0")
    g.set_checked(first._model_model, "length")
    opened += [first, second]
    return first, second


def join(manager, *pages):
    """Put *pages* in one perspective, as open tabs."""
    for page in pages:
        page.parent = manager
        manager.perspective().fit_tabs.append(page)


def save(pages) -> dict:
    """The project dict of *pages* (FittingPerspective.getSerializedFitpage), after a round trip through JSON."""
    project = {}
    for page in pages:
        rows = {r[0]: r[1:] for r in page.getFitPage() + page.getFitModel() if len(r) > 1}
        project[rows["data_id"][0][0]] = {"fit_params": [rows]}
    return json.loads(json.dumps(project))


def load(project, manager, opened, first_tab_id=3) -> list:
    """Open one page per saved page and apply the constraints, as DataExplorer's project load does."""
    pages = []
    for tab_id, (data_id, value) in enumerate(project.items(), start=first_tab_id):
        page = g.new_page(tab_id=tab_id, data=g.make_data1d(data_id, f"data_{data_id}"))
        opened.append(page)
        join(manager, page)
        page.createPageForParameters(value["fit_params"][0])
        pages.append(page)
    manager.perspective().updateFromConstraints(GuiUtils.getConstraints(project))
    return pages


def simultaneous_fit(pages) -> dict:
    """The fit problem ConstraintWidget builds, up to the run: {page name: fitness}, constraints applied."""
    fitter, fit_id = BumpsFit(), 0
    for page in pages:
        _, fit_id = page.controller.prepare_fitters(fitter, fit_id)
    models = [SasFitness(model=d.get_model(), data=d.get_data(), constraints=d.constraints, fitted=d.pars)
              for d in fitter.fit_arrange_dict.values()]
    ParameterExpressions(models)()       # fails if a constraint names a page that is not in the fit
    return {m.name: m for m in models}


def testRenameSaveReloadFit(renamed, opened):
    project = save(renamed)
    assert [p["fit_params"][0]["tab_name"] for p in project.values()] == [["sample"], ["M2"]]

    first, second = load(project, dummy_manager(), opened)
    assert (first.kernel().name, first.document.identity.mnemonic) == ("sample", "sample")
    assert constraint_service.active(second.document) == [("radius", "sample.radius")]

    fit = simultaneous_fit([first, second])
    assert set(fit) == {"sample", "M2"}           # every page takes its saved name
    assert fit["M2"].parameters()["radius"].value == 33.0


@pytest.mark.parametrize("switch", [
    lambda page: g.select_model(page, "Cylinder", "hollow_cylinder"),
    lambda page: g.select_model(page, "Cylinder", "cylinder", structure="hardsphere"),
], ids=["model", "structure factor"])
def testRenameSurvivesModelSwitch(renamed, switch):
    first, second = renamed
    switch(first)
    g.set_cell(first._model_model, "radius", 1, "33.0")
    g.set_checked(first._model_model, "scale")
    assert (first.kernel().name, first.document.identity.mnemonic) == ("sample", "sample")
    assert simultaneous_fit([first, second])["M2"].parameters()["radius"].value == 33.0


def testLoadedNameRefreshesTheConstraintTab(renamed, opened):
    manager = dummy_manager()
    page = g.new_page(tab_id=3, data=g.make_data1d("d3", "data3"))
    opened.append(page)
    join(manager, page)
    names = []
    page.newModelSignal.connect(lambda: names.append(page.kernel().name))
    page.createPageForParameters(save(renamed[:1])["d1"]["fit_params"][0])
    assert names[-1] == "sample"


def testLoadingANameInUseFallsBackToTheDefault(renamed, opened):
    first, _ = renamed
    manager = dummy_manager()
    join(manager, first)
    messages = []
    GuiUtils.communicator.statusBarUpdateSignal.connect(messages.append)
    try:
        (page,) = load(save([first]), manager, opened)
    finally:
        GuiUtils.communicator.statusBarUpdateSignal.disconnect(messages.append)
    assert (page.kernel().name, page.document.identity.mnemonic) == ("M3", "M3")
    assert first.document.identity.mnemonic == "sample"
    assert "Fit page name sample is already in use, so this page is named M3." in messages
