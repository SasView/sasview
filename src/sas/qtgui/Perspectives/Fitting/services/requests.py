"""
The immutable requests of the background jobs (FW-MVC-DESIGN.md §3.3, Phase 7).

The GUI thread builds a request at launch; the worker sees only the request. Each owns its
engine instance (``KernelBuilder.build``) and the smearer built against it, so no job shares
state with the page or with another job.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sas.qtgui.Perspectives.Fitting.model.results import Provenance


@dataclass(frozen=True)
class TheoryRequest:
    provenance: Provenance
    kernel: Any
    data: Any
    smearer: Any
    weight: Any
    qmin: float
    qmax: float

    @property
    def request_id(self) -> int:
        return self.provenance.request_id

    @property
    def dataset_id(self) -> str:
        return self.provenance.dataset_id


@dataclass(frozen=True)
class FitRequest:
    request_id: int
    layout_generation: int
    batch: bool
    fitters: tuple
