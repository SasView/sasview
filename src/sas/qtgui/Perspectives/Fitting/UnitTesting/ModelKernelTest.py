"""
Qt-free tests of the engine instance built from a document (``KernelBuilder.build`` and ``apply``,
FW-MVC-DESIGN.md §3.2, Phase 6) and of the constraint service (``services/constraints.py``, §3.5).
"""
from sas.qtgui.Perspectives.Fitting.Constraint import Constraint
from sas.qtgui.Perspectives.Fitting.model.events import Origin
from sas.qtgui.Perspectives.Fitting.model.parameters import ArrayDistribution, Dispersion
from sas.qtgui.Perspectives.Fitting.services import constraints as service
from sas.qtgui.Perspectives.Fitting.UnitTesting.document_fixtures import BUILDER, d1, edit, flags, page


class TestBuild:

    def test_values_bounds_and_name(self):
        doc = page("Cylinder", "cylinder", data=[d1()])
        edit(doc, "radius", value=33.5, min=1.0, max=90.0)
        kernel = BUILDER.build(doc)
        assert kernel.name == "M1"
        assert kernel.getParam("radius") == 33.5
        assert kernel.details["radius"][1:3] == [1.0, 90.0]

    def test_a_page_without_parameters_has_no_kernel(self):
        assert BUILDER.build(page("Cylinder")) is None

    def test_widths_are_zero_while_polydispersity_is_off(self):
        doc = page("Cylinder", "cylinder", data=[d1()])
        edit(doc, "radius.width", value=0.2, dispersion=Dispersion(21, 2.5, "rectangle"))
        kernel = BUILDER.build(doc)
        assert kernel.getParam("radius.width") == 0.0
        assert (kernel.getParam("radius.npts"), kernel.dispersion["radius"]["type"]) == (21, "rectangle")
        flags(doc, polydispersity=True)
        assert BUILDER.build(doc).getParam("radius.width") == 0.2

    def test_an_array_distribution_carries_its_weights_and_its_width(self):
        doc = page("Cylinder", "cylinder", data=[d1()])
        flags(doc, polydispersity=True)
        edit(doc, "radius.width", value=0.3,
             dispersion=Dispersion(35, 3.0, "array", ArrayDistribution((10.0, 20.0), (0.4, 0.6), "w.txt")))
        kernel = BUILDER.build(doc)
        assert list(kernel.dispersion["radius"]["values"]) == [10.0, 20.0]
        assert kernel.getParam("radius.width") == 0.3

    def test_products_shells_and_structure_only(self):
        doc = page("Sphere", "sphere", "hardsphere", data=[d1()])
        assert type(BUILDER.build(doc)).__name__ == "sphere@hardsphere"
        doc = page("Sphere", "core_multi_shell", data=[d1()], multiplicity=3)
        assert BUILDER.build(doc).multiplicity == 3
        assert type(BUILDER.build(page("Structure Factor", "", "hardsphere", data=[d1()]))).__name__ == "hardsphere"

    def test_apply_updates_the_same_instance(self):
        doc = page("Cylinder", "cylinder", data=[d1()])
        kernel = BUILDER.build(doc)
        edit(doc, "radius", value=44.0)
        with doc.transaction(Origin.SYSTEM) as tx:
            tx.set_mnemonic("sample")
        BUILDER.apply(kernel, doc)
        assert (kernel.getParam("radius"), kernel.name) == (44.0, "sample")


class TestConstraintService:

    def constrained(self):
        doc = page("Cylinder", "cylinder", data=[d1()])
        with doc.transaction(Origin.USER) as tx:
            tx.set_constraint("length", Constraint(param="length", func="2*M1.radius", value_ex="2*M1.radius"))
            tx.set_constraint("radius.width", Constraint(param="radius.width", func="M2.radius.width"))
            inactive = Constraint(param="scale", func="M1.background")
            inactive.active = False
            tx.set_constraint("scale", inactive)
        return doc

    def test_queries(self):
        doc = self.constrained()
        assert service.active(doc) == [("length", "2*M1.radius"), ("radius.width", "M2.radius.width")]
        assert service.complex_constraints(doc, service.TABLES["standard"]) == [("length", "2*M1.radius")]
        assert service.full_names(doc, service.TABLES["standard"]) == [("scale", "M1.background"),
                                                                       ("length", "2*M1.radius")]

    def test_multimodel_and_keys(self):
        doc = self.constrained()
        assert service.is_multimodel(doc, "M2.radius.width") and not service.is_multimodel(doc, "2*M1.radius")
        assert service.key_for(doc, "Distribution of radius") == "radius.width"
        assert service.key_for(doc, "length") == "length" and service.key_for(doc, "nothing") is None

    def test_validate(self):
        symbols = {"M1.radius": 20.0, "M1.length": 400.0}
        assert service.validate(symbols, [("M1.length", "2*M1.radius")]) == []
        errors = service.validate(symbols, [("M1.length", "2*M1.nothing")])
        assert "nothing" in errors and errors.startswith("<style")
