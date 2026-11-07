"""
Detached copy of the undoable state of a fit page (FW-MVC-DESIGN.md §2.3).

A snapshot holds the selection, the whole parameter set (layout, values,
bounds, fit flags, errors, dispersions with array samples, constraints),
the options, smearing, flags and the mnemonic. It holds no ids, datasets,
results or job state.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass

from sas.qtgui.Perspectives.Fitting.model.parameters import (
    FitOptions,
    Flags,
    ModelSelection,
    ParameterSet,
    Smearing,
)


@dataclass(frozen=True)
class PageSnapshot:
    selection: ModelSelection
    parameters: ParameterSet
    options: FitOptions
    smearing: Smearing
    flags: Flags
    mnemonic: str

    @classmethod
    def capture(cls, doc) -> PageSnapshot:
        """Deep-copy the undoable state of *doc*."""
        return cls(
            selection=doc.selection,
            parameters=doc.parameters.copy(),
            options=copy.copy(doc.options),
            smearing=copy.copy(doc.smearing),
            flags=copy.copy(doc.flags),
            mnemonic=doc.identity.mnemonic,
        )
