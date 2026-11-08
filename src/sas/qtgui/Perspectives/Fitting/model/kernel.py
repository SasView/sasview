"""
Parameter layout of a model selection (FW-MVC-DESIGN.md §3.2).

``KernelBuilder.layout(selection, is2D)`` returns the ``ParameterSet`` that
the fit page shows for a selection: the main table in today's exact row
order, the polydispersity table and the magnetism table. It is the Qt-free
part of ``fromModelToQModel``, ``fromStructureFactorToQModel``,
``addExtraShells``, ``FittingUtilities.add*ToModel`` and the poly/magnet
``set*Model`` methods.

``KernelBuilder.build(doc)`` returns a new engine instance with the document's
effective state (since Phase 6: the legacy table builders that made the kernel are gone).
"""
from __future__ import annotations

import math
from collections.abc import Mapping

import numpy as np

from sasmodels import modelinfo
from sasmodels.product import RADIUS_MODE_ID, STRUCTURE_MODE_ID, VOLFRAC_ID
from sasmodels.sasview_model import MultiplicationModel
from sasmodels.weights import MODELS as DISTRIBUTIONS

from sas.qtgui.Perspectives.Fitting.FittingConstants import CATEGORY_STRUCTURE, DEFAULT_POLYDISP_FUNCTION, MODEL_DEFAULT
from sas.qtgui.Perspectives.Fitting.model.parameters import (
    Capabilities,
    Dispersion,
    ModelSelection,
    Parameter,
    ParameterSet,
    Row,
    RowKind,
    Table,
    ValueKind,
)

SCALE = Parameter("scale", "scale", Table.MAIN, "", ValueKind.FLOAT, 1.0, 0.0, math.inf, "")
BACKGROUND = Parameter("background", "background", Table.MAIN, "", ValueKind.FLOAT, 0.001, -math.inf, math.inf, "1/cm")
POLY_SECTION = "polydispersity"
MAGNET_SECTION = "magnetism"
PRODUCT_SECTION = "product"

# -- pure helpers on sasmodels parameter tables (also used by FittingUtilities) --


def replaceShellName(param_name: str, value: int) -> str:
    """<param_name>[n] -> <param_name><value>"""
    assert '[' in param_name
    return param_name[:param_name.index('[')] + str(value)


def getIterParams(model) -> list:
    """All multi-shell parameters of the parameter table *model*."""
    return [par for par in model.iq_parameters if "[" in par.name]


def getMultiplicity(model) -> tuple[str, int]:
    """(name of the shell-count parameter, number of shells), or ("", 0)."""
    iter_params = getIterParams(model)
    param_name = ""
    param_length = 0
    if iter_params:
        param_length = iter_params[0].length
        param_name = iter_params[0].length_control
        if param_name is None and '[' in iter_params[0].name:
            param_name = iter_params[0].name[:iter_params[0].name.index('[')]
    return (param_name, param_length)


def fixed_choices(param) -> list[str] | None:
    """The choices of a fixed-choice parameter, or None (createFixedChoiceComboBox)."""
    if isinstance(param.choices, (list, tuple)) and len(param.choices) > 0:
        return list(param.choices)
    if isinstance(param.units, (list, tuple)):
        return [str(x) for x in param.units]
    return None


def shell_limits(shell_par) -> tuple[int, int]:
    """Shell-count limits as addExtraShells computes them (an infinite maximum becomes 9)."""
    try:
        return int(shell_par.limits[0]), int(shell_par.limits[1])
    except OverflowError:
        return 0, 9 if float(shell_par.limits[1]) == math.inf else 0


def _table_parameters(table, is2D: bool) -> list:
    """The parameters a table shows: all non-magnetic kernel parameters in 2D, I(q) parameters in 1D."""
    if is2D:
        return [p for p in table.kernel_parameters if p.type != 'magnetic']
    return list(table.iq_parameters)


def _structure_only(selection: ModelSelection) -> bool:
    """A placeholder model text, or the Structure Factor category, means no form factor."""
    return selection.category == CATEGORY_STRUCTURE or selection.model in ("", MODEL_DEFAULT)


class KernelBuilder:
    """Builds parameter layouts and engine instances for model selections."""

    def __init__(self, models: Mapping[str, type]) -> None:
        self._models = models     # model name -> SasviewModel class

    def build(self, doc):
        """A new engine instance for *doc* (§3.2), or None if the page has no parameters.

        It carries the document's effective state (``apply``) and the mnemonic as its name.
        """
        params, selection = doc.parameters, doc.selection
        if not len(params):
            return None
        if _structure_only(selection):
            kernel = self._models[selection.structure]()
        else:
            kernel = self._models[selection.model]()
            if selection.structure and params.capabilities.structure_factor:
                # As the legacy builder did: the product is made with the most shells
                if kernel.is_multiplicity_model:
                    kernel.multiplicity = kernel.multiplicity_info.number
                kernel = MultiplicationModel(kernel, self._models[selection.structure]())
            if selection.multiplicity is not None:
                kernel.multiplicity = selection.multiplicity
        self.apply(kernel, doc)
        return kernel

    def apply(self, kernel, doc) -> None:
        """Push the document's effective state into *kernel*, an instance for the same selection:
        values (a fixed choice as its index), bounds, dispersions (array weights included), the
        name, poly widths at 0 while polydispersity is off, magnetic values at 0 while magnetism is off."""
        kernel.name = doc.identity.mnemonic
        flags = doc.flags
        names = set(kernel.getParamList())
        for p in doc.parameters:
            if p.kind is ValueKind.INT or p.key not in names:
                continue
            if p.dispersion is not None:
                # First: a new distribution resets the width
                self._set_dispersion(kernel, p.key[:-len(".width")], p.dispersion)
            off = (p.table is Table.POLY and not flags.polydispersity) or                   (p.table is Table.MAGNET and not flags.magnetism)
            kernel.setParam(p.key, 0.0 if off else p.value)
            if p.min is not None and p.kind is ValueKind.FLOAT and p.key in kernel.details:
                kernel.details[p.key][1:3] = [p.min, p.max]

    @staticmethod
    def _set_dispersion(kernel, name: str, d) -> None:
        if d.array is not None or kernel.dispersion[name]["type"] != d.type:
            distribution = DISTRIBUTIONS[d.type]()
            if d.array is not None:
                distribution.set_weights(np.array(d.array.x), np.array(d.array.w))
            kernel.set_dispersion(name, distribution)
        kernel.setParam(f"{name}.npts", d.npts)
        kernel.setParam(f"{name}.nsigmas", d.nsigmas)

    def layout(self, selection: ModelSelection, is2D: bool) -> ParameterSet:
        """The parameter layout of *selection*. A placeholder model text, or the Structure Factor
        category, means no form factor (the combo boxes may show either)."""
        if _structure_only(selection):
            if not selection.structure:
                return ParameterSet()
            return self._structure_only(selection.structure, is2D)

        kernel = self._models[selection.model]()
        info = kernel._model_info.parameters
        params: list[Parameter] = []
        rows: list[Row] = []

        def add(p: Parameter, kind: RowKind = RowKind.PARAMETER) -> None:
            params.append(p)
            rows.append(Row(kind, p.key))

        add(Parameter(**vars(SCALE)))
        add(Parameter(**vars(BACKGROUND)))
        rows.append(Row(RowKind.HEADING, selection.model))
        shell_name, _ = getMultiplicity(info)
        shell_params = getIterParams(info)
        for par in _table_parameters(info, is2D):
            if par.name == shell_name or par in shell_params:
                continue
            add(self._main_parameter(par, selection.model))

        shells = 0
        if shell_name:
            shells = self._add_shells(kernel, info, shell_name, selection.multiplicity, add)

        capabilities = Capabilities(magnetic=len(kernel.magnetic_params) > 0,
                                    structure_factor=bool(kernel.is_form_factor))
        if selection.structure and capabilities.structure_factor:
            self._add_structure_factor(kernel, selection.structure, is2D, params, rows)

        kernel = self._kernel_with_shells(selection.model, shells)
        params += self._poly_parameters(kernel, info, is2D, shells)
        params += self._magnet_parameters(kernel, info, shells)
        return ParameterSet(params, rows, capabilities=capabilities)

    # -- main table -----------------------------------------------------

    @staticmethod
    def _main_parameter(par, section: str, key: str | None = None, simple: bool = False) -> Parameter:
        """A main-table row. *simple* rows (S(Q), product) with fixed choices have no checkbox and no bounds."""
        choices = fixed_choices(par)
        no_bounds = simple and choices is not None
        return Parameter(
            key=key or par.name, label=par.name, table=Table.MAIN, section=section,
            kind=ValueKind.CHOICE if choices else ValueKind.FLOAT,
            value=int(par.default) if choices else float(par.default),
            min=None if no_bounds else par.limits[0], max=None if no_bounds else par.limits[1],
            units=str(par.units), fittable=not no_bounds,
            choices=tuple(choices) if choices else None)

    def _add_shells(self, kernel, info, shell_name: str, count: int | None, add) -> int:
        """The multiplicity row and the expanded shell parameters; returns the shell count."""
        shell_par = next(p for p in kernel._model_info.parameters.kernel_parameters
                         if p.name.split('[')[0] == shell_name)
        low, high = shell_limits(shell_par)
        shells = int(shell_par.default) if count is None else count
        add(Parameter(shell_name, shell_name, Table.MAIN, "shells", ValueKind.INT, shells, low, high,
                      fittable=False), RowKind.MULTIPLICITY)
        for i in range(1, shells + 1):
            for par in getIterParams(info):
                p = self._main_parameter(par, "shells", key=replaceShellName(par.name, i))
                p.label = p.key
                if p.choices:
                    p.min = p.max = None
                add(p)
        return shells

    def _add_structure_factor(self, p_kernel, structure: str, is2D: bool,
                              params: list[Parameter], rows: list[Row]) -> None:
        """The S(Q) section and the product-only rows (FittingWidget._volfraction_hack)."""
        if p_kernel.is_multiplicity_model:
            p_kernel.multiplicity = p_kernel.multiplicity_info.number
        s_kernel = self._models[structure]()
        product = MultiplicationModel(p_kernel, s_kernel).\
            _model_info.parameters.kernel_parameters
        p_info = p_kernel._model_info.parameters
        p_names = {p.id for p in p_info.kernel_parameters}
        s_pars = [p for p in s_kernel._model_info.parameters.kernel_parameters
                  if not (p.id == VOLFRAC_ID and VOLFRAC_ID in p_names)]
        rows.append(Row(RowKind.HEADING, structure))
        for par in _table_parameters(modelinfo.ParameterTable(s_pars), is2D):
            key = par.name + "_S" if par.name in p_names else par.name
            p = self._main_parameter(par, structure, key=key, simple=True)
            params.append(p)
            rows.append(Row(RowKind.PARAMETER, p.key))
        # Product-only choice rows go directly after scale and background
        extras = [p for mode in (STRUCTURE_MODE_ID, RADIUS_MODE_ID) for p in product if p.id == mode]
        for offset, par in enumerate(_table_parameters(modelinfo.ParameterTable(extras), is2D)):
            p = self._main_parameter(par, PRODUCT_SECTION, simple=True)
            params.append(p)
            rows.insert(2 + offset, Row(RowKind.PARAMETER, p.key))

    def _structure_only(self, structure: str, is2D: bool) -> ParameterSet:
        """Only an S(Q) is selected: its own parameters, no scale/background, no poly/magnet tables."""
        kernel = self._models[structure]()
        params = [self._main_parameter(par, structure, simple=True)
                  for par in _table_parameters(kernel._model_info.parameters, is2D)]
        rows = [Row(RowKind.HEADING, structure)] + [Row(RowKind.PARAMETER, p.key) for p in params]
        return ParameterSet(params, rows, capabilities=Capabilities(structure_factor=True))

    # -- poly and magnet tables ----------------------------------------

    def _kernel_with_shells(self, model: str, shells: int):
        kernel = self._models[model]()
        if kernel.is_multiplicity_model:
            kernel.multiplicity = shells
        return kernel

    @staticmethod
    def _poly_parameters(kernel, info, is2D: bool, shells: int) -> list[Parameter]:
        """PolydispersityWidget.setPolyModel: form-volume (and, in 2D, orientation) parameters."""
        candidates = list(info.form_volume_parameters)
        if is2D:
            candidates += info.orientation_parameters
        names = []
        for par in candidates:
            if not par.polydisperse:
                continue
            if '[' in par.name:
                names += [replaceShellName(par.name, i) for i in range(1, shells + 1)]
            else:
                names.append(par.name)
        result = []
        for name in names:
            width = name + '.width'
            _, low, high = kernel.details[width]
            result.append(Parameter(
                key=width, label="Distribution of " + name, table=Table.POLY, section=POLY_SECTION,
                kind=ValueKind.FLOAT, value=float(kernel.getParam(width)), min=low, max=high,
                dispersion=Dispersion(npts=int(kernel.getParam(name + '.npts')),
                                      nsigmas=float(kernel.getParam(name + '.nsigmas')),
                                      type=DEFAULT_POLYDISP_FUNCTION)))
        return result

    @staticmethod
    def _magnet_parameters(kernel, info, shells: int) -> list[Parameter]:
        """MagnetismWidget.setMagneticModel: magnetic parameters of the shells that are shown."""
        shell_names = {replaceShellName(p.name, i) for p in getIterParams(info)
                       for i in range(1, kernel.multiplicity_info.number + 1)}
        result = []
        for par in info.call_parameters:
            if par.type != 'magnetic':
                continue
            basename = par.name.rsplit('_', 1)[0] if '_' in par.name else par.name
            if basename in shell_names:
                digits = basename[-2:] if basename[-2:].isdigit() else basename[-1:]
                if int(digits) > shells:
                    continue
            result.append(Parameter(
                key=par.name, label=par.name, table=Table.MAGNET, section=MAGNET_SECTION,
                kind=ValueKind.FLOAT, value=float(par.default), min=par.limits[0], max=par.limits[1],
                units=str(par.units)))
        return result
