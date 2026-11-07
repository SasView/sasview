"""
Derived rules of the fit page document (FW-MVC-DESIGN.md §2.5).

Pure functions of the document. ``apply_rules`` runs at the end of every
transaction, before commit, so observers never see stale editability.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from sasdata.dataloader.data_info import Data2D

from sas.qtgui.Perspectives.Fitting.model.parameters import Parameter, Table

if TYPE_CHECKING:
    from sas.qtgui.Perspectives.Fitting.model.document import FitPageDocument

# Smearing combo entries (SmearingWidget)
SMEARING_NONE = "None"
SMEARING_QD = "Use dQ Data"
SMEARING_SESANS = "Hankel Transform"
SMEARING_1D = ("Custom Pinhole Smear", "Custom Slit Smear")
SMEARING_2D = ("Custom Pinhole Smear",)


def is_loaded(doc: FitPageDocument) -> bool:
    """Real data is on the page (a theory-only page holds a synthetic grid)."""
    return any(not d.synthetic for d in doc.datasets.values())


def is_2d(doc: FitPageDocument) -> bool:
    """The active data is 2D when data is loaded; otherwise the user's 2D-view toggle."""
    if is_loaded(doc):
        return isinstance(doc.data(), Data2D)
    return doc.flags.view_2d


def is_sesans(doc: FitPageDocument) -> bool:
    return is_loaded(doc) and bool(getattr(doc.data(), "isSesans", False))


def can_have_magnetism(doc: FitPageDocument) -> bool:
    """2D, and the selected model has magnetic parameters (not FittingConstants.MAGNETIC_MODELS)."""
    return is_2d(doc) and doc.parameters.capabilities.magnetic


def keys_to_fit(doc: FitPageDocument) -> list[str]:
    return doc.parameters.keys_to_fit(
        poly_active=doc.flags.polydispersity,
        magnet_active=doc.flags.magnetism and can_have_magnetism(doc))


def can_fit(doc: FitPageDocument) -> bool:
    return is_loaded(doc) and bool(keys_to_fit(doc))


def smearing_options(doc: FitPageDocument) -> list[str]:
    """The smearing combo entries for the active data (SmearingWidget.updateKernelModel)."""
    options = [SMEARING_NONE]
    active = doc.datasets.get(doc.active_id) if doc.active_id else None
    resolution = active.resolution if active is not None else None
    if resolution == SMEARING_SESANS:
        options.append(SMEARING_SESANS)
    elif resolution is not None:
        options.append(SMEARING_QD)
    if len(doc.parameters):
        options.extend(SMEARING_2D if is_2d(doc) and active is not None and isinstance(active.data, Data2D)
                       else SMEARING_1D)
    return options


def _set_enabled(p: Parameter, enabled: bool) -> bool:
    """Make *p* fittable and editable, or neither. The user's fit choice is kept. True if changed."""
    if p.fittable == enabled and p.editable == enabled:
        return False
    p.fittable = p.editable = enabled
    return True


def apply_rules(doc: FitPageDocument) -> set[str]:
    """Apply the derived rules in place; return the keys whose fields changed."""
    changed = set()
    params = doc.parameters
    # Effective radius is editable only when unconstrained (processEffectiveRadius)
    if "radius_effective" in params and "radius_effective_mode" in params:
        if _set_enabled(params["radius_effective"], int(params["radius_effective_mode"].value) == 0):
            changed.add("radius_effective")
    # Background is fixed at zero for SESANS data (onSesansData / respondToModelStructure)
    if "background" in params and params["background"].table is Table.MAIN:
        background = params["background"]
        sesans = is_sesans(doc)
        if _set_enabled(background, not sesans):
            changed.add("background")
        if sesans and background.value != 0.0:
            background.value = 0.0
            changed.add("background")
    return changed
