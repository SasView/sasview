"""
Results and job state of a fit page (FW-MVC-DESIGN.md §2.4, Phase 7). Qt-free.

A result is valid for the inputs it was computed from. ``Provenance`` records them when the
request is made: the page's *inputs revision* (the document revision of the last change that
was not ``DERIVED``, so that the effective radius a theory writes back does not make that very
theory stale), the layout generation and the dataset's revision.

Results are derived state: not undoable, not in the snapshot. The controller owns them.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Provenance:
    request_id: int
    revision: int
    layout_generation: int
    dataset_id: str
    dataset_revision: int


@dataclass
class DatasetResult:
    provenance: Provenance
    theory: Any                   # Data1D | Data2D, from services/plots.py; no slider hooks
    residuals: Any = None         # None for a page without data
    components: list = field(default_factory=list)      # P(Q), S(Q), beta(Q) ... curves (1D)
    polydispersity: list = field(default_factory=list)  # the distributions of the poly widths
    chi2: float | None = None
    radius_effective: float | None = None


@dataclass
class Results:
    per_dataset: dict[str, DatasetResult] = field(default_factory=dict)
    batch: list | None = None     # the batch fit's per-dataset results, as the grid shows them

    def current(self, dataset_id: str, revision: int) -> DatasetResult | None:
        """The dataset's result, if it was computed from the page's current inputs."""
        result = self.per_dataset.get(dataset_id)
        return result if result is not None and result.provenance.revision == revision else None


@dataclass
class JobState:
    theory: dict[str, int] = field(default_factory=dict)   # dataset id -> latest theory request id
    fit: int | None = None                                   # request id of the running fit

    def cancel(self) -> None:
        """Late completions of every request are dropped."""
        self.theory.clear()
        self.fit = None
