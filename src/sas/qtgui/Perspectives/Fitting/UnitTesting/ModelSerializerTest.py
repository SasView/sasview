"""
Qt-free tests of KernelBuilder.layout and the legacy codecs against the Phase 0 goldens
(FW-MVC-DESIGN.md, Phase 1).

Each golden case is rebuilt here as a document, without any widget: the
layout comes from ``KernelBuilder.layout`` and the case's edits are made
through transactions. The document's legacy outputs must then equal the
goldens. Numbers are compared numerically (register R-6: the document stores
numbers, and the table's text spelling, e.g. "1" versus "1.0", is not kept).
"""
from types import SimpleNamespace

import pytest

from sas.qtgui.Perspectives.Fitting.Constraint import Constraint
from sas.qtgui.Perspectives.Fitting.model import serializer
from sas.qtgui.Perspectives.Fitting.model.events import Origin
from sas.qtgui.Perspectives.Fitting.model.parameters import (
    ArrayDistribution,
    Dispersion,
    Smearing,
)
from sas.qtgui.Perspectives.Fitting.UnitTesting.document_fixtures import d1, edit, flags, jsonable, page, same
from sas.qtgui.Perspectives.Fitting.UnitTesting.golden_data import GOLDEN_DIR, load_golden, make_data2d


def case_cylinder():
    doc = page("Cylinder", "cylinder", data=[d1()])
    edit(doc, "radius", value=35.5, fit=True)
    edit(doc, "length", max=1000.0)
    edit(doc, "scale", fit=True)
    return [doc]


def case_core_multi_shell():
    doc = page("Sphere", "core_multi_shell", data=[d1()], multiplicity=3)
    edit(doc, "thickness2", value=12.0, fit=True)
    return [doc]


def case_sphere_hardsphere():
    doc = page("Sphere", "sphere", "hardsphere", data=[d1()])
    edit(doc, "volfraction", value=0.3)
    edit(doc, "radius", fit=True)
    return [doc]


def case_vesicle_hardsphere():
    doc = page("Sphere", "vesicle", "hardsphere", data=[d1()])
    edit(doc, "volfraction", value=0.25)
    return [doc]


def case_plugin():
    doc = page("Plugin Models", "plugin_template", data=[d1()])
    edit(doc, "scale", fit=True)
    return [doc]


def case_magnetism_2d():
    doc = page("Sphere", "sphere", data=[make_data2d("d2", "data2d")])
    flags(doc, magnetism=True)
    edit(doc, "sld_M0", value=2.5, fit=True)
    edit(doc, "radius", fit=True)
    return [doc]


def case_fixed_choice():
    doc = page("Sphere", "sphere", "hardsphere", data=[d1()])
    edit(doc, "radius_effective_mode", value=0)
    edit(doc, "radius_effective", value=45.0)
    return [doc]


def case_disabled_parameter():
    doc = page("Sphere", "sphere", "hardsphere", data=[d1()])
    edit(doc, "radius_effective_mode", value=0)
    edit(doc, "radius_effective", fit=True)
    edit(doc, "radius_effective_mode", value=1)
    return [doc]


def case_polydispersity():
    doc = page("Cylinder", "cylinder", data=[d1()])
    flags(doc, polydispersity=True)
    edit(doc, "length.width", value=0.1, fit=True)
    array = ArrayDistribution((10.0, 20.0, 30.0), (0.2, 0.5, 0.3), "weights.txt")
    edit(doc, "radius.width", dispersion=Dispersion(35, 3.0, "array", array))
    edit(doc, "scale", fit=True)
    return [doc]


def case_fit_errors():
    doc = page("Cylinder", "cylinder", data=[d1()])
    edit(doc, "radius", value=25.5, error=0.75, fit=True)
    edit(doc, "scale", value=0.95, error=0.02, fit=True)
    return [doc]


def case_sesans():
    doc = page("Sphere", "sphere", data=[d1("ds", "sesans", sesans=True)], resolution="Hankel Transform")
    with doc.transaction(Origin.LOAD) as tx:
        tx.set_smearing(Smearing("Hankel Transform", "", 0.0, 0.0))
    edit(doc, "radius", fit=True)
    return [doc]


def case_structure_only():
    doc = page("Structure Factor", structure="hardsphere", data=[d1()])
    edit(doc, "volfraction", fit=True)
    return [doc]


def case_batch_one():
    doc = page("Cylinder", "cylinder", data=[d1("b1", "batch1")], batch=True)
    edit(doc, "radius", fit=True)
    return [doc]


def case_batch_two():
    doc = page("Cylinder", "cylinder", data=[d1("b1", "same"), d1("b2", "same")], batch=True)
    edit(doc, "radius", fit=True)
    return [doc]


def case_two_pages():
    first = page("Cylinder", "cylinder", data=[d1()], tab_id=1)
    second = page("Cylinder", "cylinder", data=[d1("d2", "data2")], tab_id=2)
    with first.transaction(Origin.SYSTEM) as tx:
        tx.set_mnemonic("sample")
    with second.transaction(Origin.USER) as tx:
        tx.set_constraint("radius", Constraint(param="radius", func="sample.radius", value_ex="sample.radius"))
        tx.set_parameter("radius", fit=True)
        tx.set_parameter("length", fit=True)
    return [first, second]


def case_theory_only():
    doc = page("Cylinder", "cylinder")
    edit(doc, "radius", value=40.0)
    return [doc]


CASES = {name[len("case_"):]: fn for name, fn in sorted(globals().items()) if name.startswith("case_")}


@pytest.fixture(params=sorted(CASES))
def case(request):
    return request.param, CASES[request.param](), load_golden(request.param)


class KernelLayoutAndCodecTest:

    def testGoldensExist(self):
        assert sorted(CASES) == sorted(p.stem for p in GOLDEN_DIR.glob("*.json"))

    def testLegacyRows(self, case):
        name, docs, goldens = case
        for doc, golden in zip(docs, goldens, strict=True):
            same(jsonable(serializer.legacy_rows(doc)), golden["rows"], name)

    def testProjectDict(self, case):
        name, docs, goldens = case
        for doc, golden in zip(docs, goldens, strict=True):
            same(jsonable(serializer.project_dict(doc)) if doc.is_loaded() else {}, golden["serialized"], name)

    def testSymbols(self, case):
        name, docs, goldens = case
        for doc, golden in zip(docs, goldens, strict=True):
            same(doc.symbol_table(), golden["symbols"], name)

    def testPageState(self, case):
        name, docs, goldens = case
        for doc, golden in zip(docs, goldens, strict=True):
            if not doc.is_loaded():
                continue   # a theory-only page holds the widget's synthetic grid, which the codec does not build
            state = SimpleNamespace()
            serializer.page_state(doc, state, kernel=None, chi2=golden["fit_state"]["tcChi"])
            result = jsonable(vars(state))
            result["data"] = [type(state.data).__name__, state.data.id]
            expected = dict(golden["fit_state"])
            del result["orientation_params_disp"], expected["orientation_params_disp"]   # engine state (Phase 7)
            same(result, expected, name)

    def testTextEncodersReproduceGoldens(self, case):
        """The extracted encoders give the golden text from the golden rows, byte for byte."""
        name, _, goldens = case
        for golden in goldens:
            rows = golden["rows"]
            parameters = rows[:rows.index(next(r for r in rows if r[0] == "is_data"))]
            assert serializer.formatParameters(_tuples(rows)) == golden["clipboard"], name
            assert serializer.formatParametersExcel(_tuples(parameters)[1:]) == golden["excel"], name
            assert serializer.formatParametersLatex(_tuples(parameters)[1:]) == golden["latex"], name


def _tuples(rows):
    """Back from JSON: the last entry of a parameter row is a constraint tuple."""
    return [[tuple(v) if isinstance(v, list) and i == len(r) - 1 and len(r) == 7 else v
             for i, v in enumerate(r)] for r in rows]


class DecodeTest:

    def testClipboardRoundTripKeepsValues(self):
        doc = CASES["cylinder"]()[0]
        rows = serializer.parse_clipboard(serializer.clipboard_text(doc))
        payload = serializer.decode(rows)
        assert payload.model == "cylinder" and payload.category == "Cylinder"
        assert payload.tab_name is None                      # paste ignores tab_name
        assert payload.parameters["radius"].value == 35.5
        assert payload.parameters["radius"].fit is True
        assert payload.parameters["length"].max == 1000.0
        assert "cylinder" not in payload.parameters          # the model's heading row is not a parameter
        assert (payload.qmin, payload.qmax) == (0.005, 0.4)

    def testPolyRowsDecodeDispersion(self):
        doc = CASES["polydispersity"]()[0]
        payload = serializer.decode(serializer.line_dict(serializer.legacy_rows(doc)))
        row = payload.parameters["radius.width"]
        assert (row.npts, row.nsigmas, row.function) == (35, 3.0, "array")
        assert payload.flags["polydispersity"] is True

    def testProjectRowsKeepConstraintAndDataIds(self):
        _, second = CASES["two_pages"]()
        payload = serializer.decode(serializer.line_dict(serializer.legacy_rows(second)))
        assert payload.parameters["radius"].constraint[-1] == "sample.radius"
        assert payload.data_ids == ["d2"]
        assert payload.tab_name == "M2"

    def testTabNameIsTheMnemonic(self):
        first, _ = CASES["two_pages"]()
        assert serializer.line_dict(serializer.legacy_rows(first))["tab_name"] == ["sample"]

    def testForeignTextIsRejected(self):
        assert serializer.parse_clipboard("something else") is None
