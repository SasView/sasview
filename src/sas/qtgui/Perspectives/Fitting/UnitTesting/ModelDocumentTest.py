"""
Qt-free tests of the fit page document, its rules, retention and the History core
(FW-MVC-DESIGN.md §2, §3.7; Phase 1). No QApplication is needed.
"""
import math
import subprocess
import sys

import pytest

from sas.qtgui.Perspectives.Fitting.Constraint import Constraint
from sas.qtgui.Perspectives.Fitting.model.document import FitPageDocument
from sas.qtgui.Perspectives.Fitting.model.events import (
    ConstraintsChanged,
    DataChanged,
    FlagsChanged,
    IdentityChanged,
    ModelChanged,
    Origin,
    ParametersChanged,
    ReentrancyError,
)
from sas.qtgui.Perspectives.Fitting.model.history import CompoundCommand, History, ReplayError, UndoCommand
from sas.qtgui.Perspectives.Fitting.model.parameters import (
    DataRef,
    FitOptions,
    ModelSelection,
    PageIdentity,
    PageMode,
)
from sas.qtgui.Perspectives.Fitting.model.retention import constraint_symbols, retain
from sas.qtgui.Perspectives.Fitting.UnitTesting.document_fixtures import BUILDER, d1, page
from sas.qtgui.Perspectives.Fitting.UnitTesting.golden_data import make_data2d

CYLINDER = ModelSelection("Cylinder", "cylinder")


@pytest.fixture
def doc():
    return page("Cylinder", "cylinder", data=[d1()])


@pytest.fixture
def changes(doc):
    received = []
    doc.subscribe(received.append)
    return received


class ImportBoundaryTest:

    def testModelPackageDoesNotLoadQt(self):
        """Goal 1: importing the model and services packages loads no Qt, directly or transitively (§7)."""
        modules = ", ".join([f"sas.qtgui.Perspectives.Fitting.model.{m}" for m in
                             ("document", "serializer", "history", "kernel", "retention", "rules", "commands")]
                            + ["sas.qtgui.Perspectives.Fitting.services.constraints"])
        code = (f"import sys\nimport {modules}\n"
                "loaded = [m for m in sys.modules if m.startswith(('PySide6', 'matplotlib'))]\n"
                "assert not loaded, loaded\n")
        result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=120)
        assert result.returncode == 0, result.stderr


class TransactionTest:

    def testCommitBumpsRevisionAndPublishesOneChangeSet(self, doc, changes):
        revision = doc.revision
        with doc.transaction(Origin.USER) as tx:
            tx.set_parameter("radius", value=33.0)
            tx.set_parameter("length", min=1.0, fit=True)
        assert doc.revision == revision + 1
        assert len(changes) == 1
        event = changes[0].get(ParametersChanged)
        assert event.keys == {"radius", "length"}
        assert event.fields == {"value", "min", "fit"}
        assert changes[0].origin is Origin.USER

    def testEmptyTransactionCommitsNothing(self, doc, changes):
        revision = doc.revision
        with doc.transaction(Origin.USER):
            pass
        assert doc.revision == revision and not changes

    @pytest.mark.parametrize("fields", [
        {"value": "abc"},
        {"value": math.nan},
        {"min": 500.0, "max": 100.0},   # bounds in the wrong order
        {"max": -1.0},                  # below the existing min 0.0
    ])
    def testInvalidInputRaisesAndChangesNothing(self, doc, changes, fields):
        before = doc.snapshot()
        with pytest.raises(ValueError), doc.transaction(Origin.USER) as tx:
            tx.set_parameter("length", value=1.0)        # applied, then rolled back
            tx.set_parameter("radius", **fields)
        assert doc.snapshot() == before
        assert not changes

    def testChoiceAndIntegerValidation(self):
        doc = page("Sphere", "sphere", "hardsphere", data=[d1()])
        with pytest.raises(ValueError), doc.transaction(Origin.USER) as tx:
            tx.set_parameter("radius_effective_mode", value=7)
        shells = page("Sphere", "core_multi_shell", data=[d1()])
        with pytest.raises(ValueError), shells.transaction(Origin.USER) as tx:
            tx.set_parameter("n", value=2.5)

    def testInfiniteBoundsAreLegal(self, doc):
        with doc.transaction(Origin.USER) as tx:
            tx.set_parameter("radius", min=-math.inf, max=math.inf)
        assert doc.parameters["radius"].min == -math.inf

    def testQRangeIsValidated(self, doc):
        with pytest.raises(ValueError), doc.transaction(Origin.USER) as tx:
            tx.set_options(FitOptions(qmin=0.5, qmax=0.1))

    def testUnknownKeyRaises(self, doc):
        with pytest.raises(KeyError), doc.transaction(Origin.USER) as tx:
            tx.set_parameter("no_such_parameter", value=1.0)

    def testSubscribersMayNotMutate(self, doc):
        def mutate(change):
            with doc.transaction(Origin.USER) as tx:
                tx.set_parameter("radius", value=1.0)
        doc.subscribe(mutate)
        with pytest.raises(ReentrancyError), doc.transaction(Origin.USER) as tx:
            tx.set_parameter("radius", value=2.0)

    def testSubscriberErrorIsLoggedAndCommitStands(self, doc, caplog):
        doc.strict = False
        doc.subscribe(lambda change: 1 / 0)
        with doc.transaction(Origin.USER) as tx:
            tx.set_parameter("radius", value=2.0)
        assert doc.parameters["radius"].value == 2.0
        assert "subscriber" in caplog.text

    def testSubscriberErrorIsRaisedInStrictMode(self, doc):
        doc.subscribe(lambda change: 1 / 0)
        with pytest.raises(ZeroDivisionError), doc.transaction(Origin.USER) as tx:
            tx.set_parameter("radius", value=2.0)

    def testDisposeAndUnsubscribe(self, doc):
        received = []
        subscription = doc.subscribe(received.append)
        subscription.dispose()
        doc.subscribe(received.append)
        doc.dispose()
        with doc.transaction(Origin.USER) as tx:
            tx.set_parameter("radius", value=2.0)
        assert not received

    def testLayoutChangeBumpsGeneration(self, doc, changes):
        generation = doc.parameters.layout_generation
        selection = ModelSelection("Cylinder", "hollow_cylinder")
        with doc.transaction(Origin.USER) as tx:
            tx.set_selection(selection)
            tx.set_parameters(BUILDER.layout(selection, doc.is2D()))
        assert doc.parameters.layout_generation == generation + 1
        assert changes[0].get(ModelChanged).layout_generation == generation + 1

    def testOtherEvents(self, doc, changes):
        with doc.transaction(Origin.SYSTEM) as tx:
            tx.set_mnemonic("sample")
            tx.set_flags(chain_fit=True)
            tx.set_constraint("radius", Constraint(param="radius", func="M2.radius"))
        assert {type(e) for e in changes[0].events} == {IdentityChanged, FlagsChanged, ConstraintsChanged}
        assert doc.identity.mnemonic == "sample"
        with pytest.raises(ValueError), doc.transaction(Origin.SYSTEM) as tx:
            tx.set_mnemonic("")


class DerivedRulesTest:

    def testIs2DFollowsDataOrToggle(self):
        theory = page("Cylinder", "cylinder")
        assert not theory.is_loaded() and not theory.is2D()
        with theory.transaction(Origin.USER) as tx:
            tx.set_flags(view_2d=True)
        assert theory.is2D()
        assert page("Sphere", "sphere", data=[make_data2d("d2", "d2")]).is2D()

    def testIs2DChangeFiresModelChanged(self, doc, changes):
        with doc.transaction(Origin.LOAD) as tx:
            tx.set_datasets([DataRef("d2", "d2", make_data2d("d2", "d2"))])
        assert changes[0].get(ModelChanged) is not None
        assert changes[0].get(DataChanged).ids == {"d1", "d2"}

    def testSyntheticDataIsNotLoaded(self):
        theory = page("Cylinder", "cylinder")
        with theory.transaction(Origin.SYSTEM) as tx:
            tx.set_datasets([DataRef("grid", "grid", d1("grid", "grid"), synthetic=True)])
        assert not theory.is_loaded() and not theory.can_fit()

    def testCanFitAndMagnetism(self, doc):
        assert not doc.can_fit()
        with doc.transaction(Origin.USER) as tx:
            tx.set_parameter("radius", fit=True)
        assert doc.can_fit()
        assert not doc.can_have_magnetism()                 # 1D
        magnetic = page("Sphere", "sphere", data=[make_data2d("d2", "d2")])
        assert magnetic.can_have_magnetism()

    def testEffectiveRadiusEditability(self):
        doc = page("Sphere", "sphere", "hardsphere", data=[d1()])
        assert not doc.parameters["radius_effective"].editable     # default mode 1
        with doc.transaction(Origin.USER) as tx:
            tx.set_parameter("radius_effective_mode", value=0)
        p = doc.parameters["radius_effective"]
        assert p.editable and p.fittable
        with doc.transaction(Origin.USER) as tx:
            tx.set_parameter("radius_effective", fit=True)
            tx.set_parameter("radius_effective_mode", value=1)
        assert not p.fittable and p.fit                          # the user's choice is kept ...
        assert "radius_effective" not in doc.parameters.keys_to_fit(poly_active=False, magnet_active=False)

    def testSesansDisablesBackgroundAtZero(self):
        doc = page("Sphere", "sphere", data=[d1("ds", "sesans", sesans=True)])
        background = doc.parameters["background"]
        assert (background.value, background.fittable, background.editable) == (0.0, False, False)

    def testSymbolTable(self, doc):
        assert doc.symbol_table()["M1.radius"] == 20.0
        assert "M1.cylinder" not in doc.symbol_table()
        with doc.transaction(Origin.USER) as tx:
            tx.set_flags(polydispersity=True)
            tx.set_mnemonic("sample")
        assert "sample.radius.width" in doc.symbol_table()


class SnapshotTest:

    def testSnapshotIsDetachedAndRestores(self, doc, changes):
        with doc.transaction(Origin.USER) as tx:
            tx.set_constraint("length", Constraint(param="length", func="M1.radius*2"))
        before = doc.snapshot()
        with doc.transaction(Origin.USER) as tx:
            tx.set_parameter("radius", value=99.0, error=1.0)
            tx.set_flags(polydispersity=True)
            tx.set_constraint("length", None)
        assert before.parameters["radius"].value == 20.0     # detached
        assert doc.snapshot() != before
        doc.restore_undo_state(before)
        assert doc.snapshot() == before
        assert doc.parameters["length"].constraint.func == "M1.radius*2"
        assert changes[-1].origin is Origin.UNDO

    def testRestoreAcrossLayouts(self, doc):
        cylinder = doc.snapshot()
        selection = ModelSelection("Sphere", "core_multi_shell", multiplicity=2)
        with doc.transaction(Origin.USER) as tx:
            tx.set_selection(selection)
            tx.set_parameters(BUILDER.layout(selection, False))
        assert "thickness2" in doc.parameters
        doc.restore_undo_state(cylinder)
        assert doc.selection == CYLINDER and "thickness2" not in doc.parameters

    def testSnapshotExcludesIdsAndData(self, doc):
        snap = doc.snapshot()
        assert not hasattr(snap, "datasets") and not hasattr(snap, "identity")


class RetentionTest:

    def _switch(self, doc, selection, symbols=None):
        new, dropped = retain(doc.parameters, BUILDER.layout(selection, doc.is2D()), symbols)
        return new, dropped

    def testValuesBoundsFitAndDispersionAreKeptByKey(self, doc):
        with doc.transaction(Origin.USER) as tx:
            tx.set_parameter("radius", value=33.0, min=5.0, max=90.0, fit=True, error=0.5)
            tx.set_parameter("radius.width", value=0.2, fit=True)
        new, dropped = self._switch(doc, ModelSelection("Cylinder", "hollow_cylinder"))
        radius = new["radius"]
        assert (radius.value, radius.min, radius.max, radius.fit, radius.error) == (33.0, 5.0, 90.0, True, None)
        assert new["radius.width"].value == 0.2 and new["radius.width"].fit
        assert new["thickness"].value == BUILDER.layout(ModelSelection("Cylinder", "hollow_cylinder"),
                                                        False)["thickness"].value
        assert not dropped

    def testLayoutAttributesComeFromTheNewLayout(self):
        doc = page("Sphere", "sphere", "hardsphere", data=[d1()])
        new, _ = retain(doc.parameters, BUILDER.layout(ModelSelection("Sphere", "sphere"), False))
        assert new.rows[2].name == "sphere"                 # no product rows any more
        assert "radius_effective" not in new

    def testConstraintKeptOnlyIfItsSymbolsResolve(self, doc):
        with doc.transaction(Origin.USER) as tx:
            tx.set_constraint("radius", Constraint(param="radius", func="M1.length/2"))
            tx.set_constraint("length", Constraint(param="length", func="M1.radius*2"))
        new, dropped = self._switch(doc, ModelSelection("Cylinder", "hollow_cylinder"),
                                    symbols={"M1.length", "M1.thickness"})
        assert new["radius"].constraint.func == "M1.length/2"
        assert new["length"].constraint is None and dropped == ["length"]

    def testChoiceIndexOutOfRangeIsNotCopied(self):
        doc = page("Sphere", "sphere", "hardsphere", data=[d1()])
        doc.parameters["radius_effective_mode"].value = 99   # bypassing validation on purpose
        new, _ = retain(doc.parameters, BUILDER.layout(ModelSelection("Sphere", "sphere", "hardsphere"), False))
        assert new["radius_effective_mode"].value == 1

    def testConstraintSymbols(self):
        assert constraint_symbols("2*M1.radius + sqrt(M2.length.width)") == {"M1.radius", "M2.length.width"}


class KernelLayoutTest:

    def testMultiplicityOrder(self):
        layout = BUILDER.layout(ModelSelection("Sphere", "core_multi_shell", multiplicity=2), False)
        names = [r.name for r in layout.rows]
        assert names[names.index("n"):] == ["n", "sld1", "thickness1", "sld2", "thickness2"]
        assert layout.multiplicity().value == 2
        assert [p.key for p in layout.by_table(layout["thickness1.width"].table)] == \
            ["radius.width", "thickness1.width", "thickness2.width"]

    def testTwoDimensionalAddsOrientationAndMagnetism(self):
        layout = BUILDER.layout(CYLINDER, True)
        assert {"theta", "phi"} <= set(layout.keys())
        assert "theta.width" in layout
        assert layout.capabilities.magnetic

    def testStructureOnlyHasNoScaleOrTables(self):
        layout = BUILDER.layout(ModelSelection("Structure Factor", "", "hardsphere"), False)
        assert layout.keys() == ["radius_effective", "volfraction"]

    def testEmptySelection(self):
        assert len(BUILDER.layout(ModelSelection(), False)) == 0


class _Recorder(UndoCommand):
    def __init__(self, log, name, merge_key=None):
        super().__init__(name)
        self.log, self.name, self.merge_key = log, name, merge_key

    def redo(self, target):
        self.log.append(("redo", self.name, target))

    def undo(self, target):
        self.log.append(("undo", self.name, target))

    def can_merge(self, other):
        return self.merge_key is not None and other.merge_key == self.merge_key

    def merge(self, other):
        return _Recorder(self.log, self.name + "+" + other.name, self.merge_key)


class HistoryTest:

    @pytest.fixture
    def log(self):
        return []

    @pytest.fixture
    def history(self):
        return History(target="T", max_depth=3)

    def testExecuteAppliesThenRecords(self, history, log):
        history.execute(_Recorder(log, "a"))
        assert log == [("redo", "a", "T")] and history.can_undo()
        history.undo()
        history.redo()
        assert log[1:] == [("undo", "a", "T"), ("redo", "a", "T")]

    def testPushAppliedOnlyRecords(self, history, log):
        history.push_applied(_Recorder(log, "a"))
        assert not log and history.can_undo()

    def testExecuteDuringReplayRaises(self, history, log):
        class Nested(_Recorder):
            def undo(self, target):
                history.execute(_Recorder(log, "inner"))
        history.push_applied(Nested(log, "outer"))
        history.undo()                                   # the failure is caught and reported
        assert history.can_undo() and history._consecutive_failures == 1
        with pytest.raises(ReplayError):
            history._replaying = True
            history.execute(_Recorder(log, "x"))

    def testSuppressedExecuteAppliesWithoutRecording(self, history, log):
        with history.suppressed():
            history.execute(_Recorder(log, "a"))
        assert log == [("redo", "a", "T")] and not history.can_undo()

    def testMergeDepthAndRedoInvalidation(self, history, log):
        history.push_applied(_Recorder(log, "a", merge_key="k"))
        history.push_applied(_Recorder(log, "b", merge_key="k"))
        assert history.undo_text() == "Undo a+b"
        for name in "cdef":
            history.push_applied(_Recorder(log, name))
        assert len(history._undo_stack) == 3
        history.undo()
        assert history.can_redo()
        history.push_applied(_Recorder(log, "g"))
        assert not history.can_redo()

    def testRecoveryHooks(self, log):
        restored = []
        history = History(target="T", snapshot_fn=lambda: {"v": 1}, restore_fn=restored.append)
        history.push_applied(_Recorder(log, "a"))
        history.undo()
        assert history._last_good_state == {"v": 1}
        history.reset_to_last_good()
        assert restored == [{"v": 1}]

    def testCompound(self, history, log):
        history.execute(CompoundCommand([_Recorder(log, "a"), _Recorder(log, "b")], "both"))
        history.undo()
        assert [entry[:2] for entry in log] == [("redo", "a"), ("redo", "b"), ("undo", "b"), ("undo", "a")]


class PageModeTest:

    def testBatchDocumentHoldsSeveralDatasets(self):
        doc = page("Cylinder", "cylinder", data=[d1("b1", "same"), d1("b2", "same")], batch=True)
        assert doc.mode is PageMode.BATCH and doc.dataset_order == ["b1", "b2"] and doc.active_id == "b1"
        with doc.transaction(Origin.USER) as tx:
            tx.set_active_dataset("b2")
            tx.set_chain_order(["b2", "b1"])
        assert doc.data().id == "b2" and doc.dataset_order == ["b1", "b2"]
        with pytest.raises(ValueError), doc.transaction(Origin.USER) as tx:
            tx.set_chain_order(["b1"])

    def testDuplicateDatasetIdsRejected(self):
        doc = FitPageDocument(PageIdentity(1, 1))
        with pytest.raises(ValueError), doc.transaction(Origin.LOAD) as tx:
            tx.set_datasets([DataRef("x", "a", d1("x")), DataRef("x", "b", d1("x"))])
