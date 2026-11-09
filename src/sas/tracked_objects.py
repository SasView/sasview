"""Non-GUI objects tracked by the data manager alongside the raw data.

Like any other user of the data manager, these hold the tracked objects they
use through `DataReference` fields. Values only they own are plain fields.

This module must stay free of Qt imports, as it is imported by
:mod:`sas.data_manager`. The windows displaying these objects are managed by
the GUI, which listens to the data manager's hooks.
"""
from abc import ABC
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from sasdata.data import SasData, SasMeasurement

from sas.refactored_plotting.PlotModifiers import PlotModifier

if TYPE_CHECKING:
    from sas.data_manager import DataReference


class FitModelParameters(ABC):
    pass


# eq=False keeps identity based equality and hashing: two fits with the same
# values are still different items in the explorer.
@dataclass(eq=False)
class TrackedFit:
    """The result of fitting a model to data (or a theory, without data)."""
    model_parameters: FitModelParameters
    # The fitted curve, owned by this object.
    fit: SasMeasurement
    data: "DataReference[SasData] | None" = None

    @property
    def formatName(self) -> str:
        if self.data:
            return f"Fit of {self.data.get().name}"
        else:
            # TODO: Could potentially return a more elaborate name of what the
            # theory object is about.
            return "Theory"


@dataclass(eq=False)
class TrackedPlot:
    """Description of a plot: what is plotted and how. The window showing it is
    created by the GUI; call `DataManager.notify_changed` on this object to
    have it (re)drawn."""
    data: "DataReference[SasMeasurement] | None" = None
    fit: "DataReference[TrackedFit] | None" = None
    modifiers: "list[DataReference[PlotModifier]]" = field(default_factory=list)

    @property
    def formatName(self) -> str:
        if self.data:
            return f"Plot of {self.data.get().name}"
        else:
            return "Empty Plot"
