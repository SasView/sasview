"""
Legacy formats of the fit page, written from and read into the document (FW-MVC-DESIGN.md §3.6).

There are two structured formats:

- the legacy rows (``getFitPage() + getFitModel()``), from which the
  clipboard text, the project dict and paste are all derived;
- ``PageState`` (``.fitv``), which also needs chi² and the engine state.

Excel and LaTeX text are presentations of the rows. Values are written in
the canonical number format (register R-6): Python's shortest round-trip
``str(float)``, and ``str(int)`` for integer and choice values.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field

from sas.qtgui.Perspectives.Fitting.model.parameters import (
    PageMode,
    Parameter,
    RowKind,
    Table,
)
from sas.qtgui.Perspectives.Fitting.model.rules import smearing_options

CLIPBOARD_HEADER = "sasview_parameter_values"

# ---------------------------------------------------------------------------
# Text encoders over rows (extracted from FittingUtilities, which re-exports them)
# ---------------------------------------------------------------------------


def formatParameters(parameters: list, entry_sep=',', line_sep=':'):
    """
    Prepare the parameter string in the standard SasView layout
    """

    parameter_strings = [CLIPBOARD_HEADER]
    for parameter in parameters:
        parameter_strings.append(entry_sep.join([str(component) for component in parameter]))

    return line_sep.join(parameter_strings)

def formatParametersExcel(parameters: list):
    """
    Prepare the parameter string in the Excel format (tab delimited)
    """
    crlf = chr(13) + chr(10)
    tab = chr(9)

    output_string = ""
    # names
    names = ""
    values = ""
    check = ""
    for parameter in parameters:
        names += parameter[0]+tab
        if len(parameter) > 3:
            # Add the error column if fitted
            if parameter[1] == "True" and parameter[3] is not None:
                names += parameter[0]+"_err"+tab

            values += parameter[2]+tab
            check += str(parameter[1])+tab
            if parameter[1] == "True" and parameter[3] is not None:
                values += parameter[3]+tab
            # add .npts and .nsigmas when necessary
            if parameter[0][-6:] == ".width":
                names += parameter[0].replace('.width', '.nsigmas') + tab
                names += parameter[0].replace('.width', '.npts') + tab
                values += parameter[5] + tab + parameter[4] + tab
        else:
            # Empty statement for debugging purposes
            pass

    output_string = names + crlf + values + crlf + check
    return output_string

def formatParametersLatex(parameters: list):
    """
    Prepare the parameter string in latex
    """

    output_string = r'\begin{table}'
    output_string += r'\begin{tabular}[h]'

    crlf = chr(13) + chr(10)
    output_string += '{|'
    output_string += 'l|l|'*len(parameters)
    output_string += r'}\hline'
    output_string += crlf

    names = ""
    values = ""

    for index, parameter in enumerate(parameters):
        name = parameter[0] # Parameter name
        names += name.replace('_', r'\_')  # Escape underscores
        if len(parameter) > 3:
            values += f" {parameter[2]}"
            # Add the error column if fitted
            if parameter[1] == "True" and parameter[3] is not None:
                names += f" & {parameter[0]} " + r'\_err'
                values += f' & {parameter[3]}'

            if index < len(parameters) - 1:
                names += ' & '
                values += ' & '

            # add .npts and .nsigmas when necessary
            if parameter[0][-6:] == ".width":
                names += parameter[0].replace('.width', '.nsigmas') + ' & '
                names += parameter[0].replace('.width', '.npts')
                values += parameter[5] + ' & '
                values += parameter[4]

                if index < len(parameters) - 1:
                    names += ' & '
                    values += ' & '
        elif len(parameter) > 2:
            values += f' & {parameter[2]} &'
        else:
            values += f' & {parameter[1]} &'

    output_string += names
    output_string += r'\\ \hline'
    output_string += crlf

    output_string += values
    output_string += r'\\ \hline'
    output_string += crlf
    output_string += r'\end{tabular}'
    output_string += r'\end{table}'

    return output_string


# ---------------------------------------------------------------------------
# Writing rows from the document
# ---------------------------------------------------------------------------


def format_number(value) -> str:
    """The canonical text of a number (register R-6)."""
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return str(value)
    return str(float(value))


def _text(value) -> str:
    return "" if value is None else format_number(value)


def _constraint_tuple(p: Parameter) -> tuple:
    c = p.constraint
    return () if c is None else (c.value, c.param, c.value_ex, c.validate, c.func)


def _has_errors(params: list[Parameter]) -> bool:
    """A table shows its error column when any of its parameters carries an error."""
    return any(p.error is not None for p in params)


def _main_rows(doc) -> list[list]:
    params = doc.parameters
    with_errors = _has_errors(params.by_table(Table.MAIN))
    result = []
    for row in params.rows:
        error = "" if with_errors else None
        if row.kind is RowKind.HEADING:
            result.append([row.name, None, "", error, "", "", ()])
            continue
        p = params[row.name]
        if with_errors and p.error is not None:
            error = format_number(p.error)
        value = "" if row.kind is RowKind.MULTIPLICITY else format_number(p.value)
        checked = str(p.fit) if p.fittable else None
        result.append([params.legacy_key(p.key), checked, value, error, _text(p.min), _text(p.max),
                       _constraint_tuple(p)])
    return result


def _poly_rows(doc) -> list[list]:
    params = doc.parameters.by_table(Table.POLY)
    with_errors = _has_errors(params)
    rows = []
    for p in params:
        d = p.dispersion
        error = (format_number(p.error) if p.error is not None else "") if with_errors else None
        rows.append([p.key, str(p.fit), format_number(p.value), error, _text(p.min), _text(p.max),
                     str(int(d.npts)), format_number(d.nsigmas), d.type])
    return rows


def _magnet_rows(doc) -> list[list]:
    params = doc.parameters.by_table(Table.MAGNET)
    with_errors = _has_errors(params)
    rows = []
    for p in params:
        error = (format_number(p.error) if p.error is not None else "") if with_errors else None
        rows.append([p.key, str(p.fit), format_number(p.value), error, _text(p.min), _text(p.max), ()])
    return rows


def fit_parameter_rows(doc) -> list[list]:
    """``getFitParameters``: model name, parameter rows, multiplicity."""
    if not len(doc.parameters):
        return []
    rows = [["model_name", doc.selection.model]]
    rows += _main_rows(doc)
    if doc.flags.polydispersity:
        rows += _poly_rows(doc)
    if doc.flags.magnetism and doc.can_have_magnetism():
        rows += _magnet_rows(doc)
    shells = doc.parameters.multiplicity()
    if shells is not None:
        rows.append(["multiplicity", str(shells.value)])
    return rows


def fit_page_rows(doc) -> list[list]:
    """``getFitPage``: parameter rows plus data, options, smearing and flags."""
    rows = fit_parameter_rows(doc)
    loaded = doc.is_loaded()
    shown = [doc.datasets[i] for i in doc.dataset_order] if loaded else []
    if doc.mode is not PageMode.BATCH:
        shown = [doc.datasets[doc.active_id]] if loaded else []
    rows.append(["is_data", str(loaded)])
    rows.append(["tab_index", str(doc.identity.tab_id)])
    rows.append(["is_batch_fitting", str(doc.mode is PageMode.BATCH)])
    rows.append(["data_name", [str(d.data.name) for d in shown]])
    rows.append(["data_id", [str(d.data.id) for d in shown]])
    rows.append(["tab_name", f"M{doc.identity.tab_id}"])   # register R-3: not the mnemonic until Phase 3a
    options = doc.options
    rows.append(["q_range_min", str(options.qmin)])
    rows.append(["q_range_max", str(options.qmax)])
    rows.append(["q_weighting", str(options.theory_weighting)])
    rows.append(["weighting", str(options.fit_weighting)])
    smearing = doc.smearing
    choices = smearing_options(doc)
    rows.append(["smearing", str(choices.index(smearing.mode) if smearing.mode in choices else 0)])
    rows.append(["smearing_min", str(smearing.d_down)])
    rows.append(["smearing_max", str(smearing.d_up)])
    flags = doc.flags
    rows.append(["polydisperse_params", str(flags.polydispersity)])
    rows.append(["magnetic_params", str(flags.magnetism)])
    rows.append(["chainfit_params", str(flags.chain_fit)])
    rows.append(["2D_params", str(flags.view_2d)])
    return rows


def fit_model_rows(doc) -> list[list]:
    """``getFitModel``: the three combo boxes."""
    selection = doc.selection
    return [["fitpage_category", selection.category],
            ["fitpage_model", selection.model],
            ["fitpage_structure", selection.structure or "None"]]


def legacy_rows(doc) -> list[list]:
    return fit_page_rows(doc) + fit_model_rows(doc)


def clipboard_text(doc) -> str:
    return formatParameters(legacy_rows(doc))


def excel_text(doc) -> str:
    return formatParametersExcel(fit_parameter_rows(doc)[1:])


def latex_text(doc) -> str:
    return formatParametersLatex(fit_parameter_rows(doc)[1:])


def line_dict(rows: list[list]) -> dict[str, list]:
    """Rows keyed by their first entry (FittingPerspective.getSerializedFitpage)."""
    return {row[0]: row[1:] for row in rows if len(row) > 1}


def project_dict(doc) -> dict:
    """``FittingPerspective.getSerializedFitpage``: {data_id: {'fit_params': [line_dict]}}."""
    rows = line_dict(legacy_rows(doc))
    return {data_id: {'fit_params': [rows]} for data_id in rows['data_id'][0]}


def page_state(doc, state, kernel, chi2: float | None = None) -> None:
    """``getCurrentFitState``: fill *state* (a PageState) from the document.

    The engine state (``orientation_params_disp``) and chi² are explicit inputs:
    the document does not hold the kernel or results (§3.6).
    """
    selection = doc.selection
    state.categorycombobox = selection.category
    state.formfactorcombobox = selection.model
    if doc.parameters.capabilities.structure_factor:
        state.structurecombobox = selection.structure or "None"
    state.tcChi = chi2
    state.enable2D = doc.is2D()
    state.data = copy.deepcopy(doc.data())
    state.qmin = doc.options.qmin
    state.qmax = doc.options.qmax
    state.npts = doc.options.npts
    state.parameters = standard_parameters(doc)
    state.orientation_params_disp = None if kernel is None else [
        [True, name, value, "", [False, 0.0], [True, kernel.details[name][1]],
         [True, kernel.details[name][2]], kernel.details[name][0]]
        for name, value in kernel.params.items()]


def standard_parameters(doc) -> list[list]:
    """``FittingUtilities.getStandardParam`` of the main table."""
    params = doc.parameters
    with_errors = _has_errors(params.by_table(Table.MAIN))
    result = []
    for row in params.rows:
        if row.kind is RowKind.HEADING:
            error = [True, ""] if with_errors else [False, 0.0]
            result.append([False, row.name, "", "", error, [True, ""], [True, ""], ""])
            continue
        p = params[row.name]
        error = [True, _text(p.error)] if with_errors else [False, 0.0]
        value = "" if row.kind is RowKind.MULTIPLICITY else format_number(p.value)
        result.append([p.fit and p.fittable, p.label, value, "", error,
                       [True, _text(p.min)], [True, _text(p.max)], p.units])
    return result


# ---------------------------------------------------------------------------
# Reading rows
# ---------------------------------------------------------------------------


def _number(text) -> float | None:
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


@dataclass
class RowValues:
    """One decoded parameter row."""
    fit: bool | None              # None: the row had no checkbox
    value: float | None           # None: not a number (e.g. the empty multiplicity cell)
    error: float | None
    min: float | None
    max: float | None
    npts: int | None = None       # poly rows only
    nsigmas: float | None = None
    function: str | None = None
    constraint: tuple | None = None


@dataclass
class PagePayload:
    """Decoded legacy rows: the input of paste (``ParameterPatch``) and of project load
    (``ProjectPagePayload``). Fields absent from the rows are None."""
    category: str | None = None
    model: str | None = None
    structure: str | None = None
    multiplicity: int | None = None
    tab_name: str | None = None
    flags: dict[str, bool] = field(default_factory=dict)
    qmin: float | None = None
    qmax: float | None = None
    theory_weighting: int | None = None
    fit_weighting: int | None = None
    smearing_index: int | None = None
    smearing_min: float | None = None
    smearing_max: float | None = None
    data_ids: list[str] = field(default_factory=list)
    parameters: dict[str, RowValues] = field(default_factory=dict)   # by legacy key


_FLAG_KEYS = {"polydisperse_params": "polydispersity", "magnetic_params": "magnetism",
              "chainfit_params": "chain_fit", "2D_params": "view_2d"}


def _decode_row(values: list) -> RowValues:
    fit = None if values[0] in (None, "None") else values[0] == "True"
    row = RowValues(fit=fit, value=_number(values[1]), error=_number(values[2]),
                    min=_number(values[3]), max=_number(values[4]))
    if len(values) >= 8 and not isinstance(values[5], (list, tuple)) and str(values[5]).isdigit():
        row.npts, row.nsigmas, row.function = int(values[5]), _number(values[6]), str(values[7])
    elif len(values) > 5 and isinstance(values[5], (list, tuple)) and values[5]:
        row.constraint = tuple(values[5])
    return row


def decode(rows: dict[str, list]) -> PagePayload:
    """Decode a line dict (from the clipboard text or a project file)."""
    first = {k: v[0] for k, v in rows.items() if v}
    payload = PagePayload(
        category=first.get("fitpage_category"),
        model=first.get("fitpage_model"),
        structure=first.get("fitpage_structure"),
        tab_name=first.get("tab_name"),
        qmin=_number(first.get("q_range_min")),
        qmax=_number(first.get("q_range_max")),
        smearing_min=_number(first.get("smearing_min")),
        smearing_max=_number(first.get("smearing_max")),
    )
    for key, attribute in (("multiplicity", "multiplicity"), ("q_weighting", "theory_weighting"),
                           ("weighting", "fit_weighting"), ("smearing", "smearing_index")):
        number = _number(first.get(key))
        setattr(payload, attribute, None if number is None else int(number))
    payload.flags = {name: first[key] == "True" for key, name in _FLAG_KEYS.items() if key in first}
    data_ids = rows.get("data_id", [[]])[0]
    payload.data_ids = list(data_ids) if isinstance(data_ids, (list, tuple)) else [data_ids]
    names = {first.get("model_name"), payload.structure}
    payload.parameters = {key: _decode_row(values) for key, values in rows.items()
                          if len(values) > 3 and key not in names}
    return payload


def parse_clipboard(text: str) -> dict[str, list] | None:
    """The line dict of clipboard text, or None if it is not fit page text. ``tab_name`` is dropped."""
    lines = text.split(':')
    if lines[0] != CLIPBOARD_HEADER:
        return None
    result = {}
    for line in lines[1:]:
        content = line.split(',')
        if len(content) > 1 and content[0] != "tab_name":
            result[content[0]] = content[1:]
    return result


__all__ = [
    "PagePayload", "RowValues", "clipboard_text", "decode", "excel_text", "fit_model_rows",
    "fit_page_rows", "fit_parameter_rows", "formatParameters", "formatParametersExcel",
    "formatParametersLatex", "format_number", "latex_text", "legacy_rows", "line_dict",
    "page_state", "parse_clipboard", "project_dict", "standard_parameters",
]

