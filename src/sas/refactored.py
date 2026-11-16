import logging
from abc import ABC, abstractmethod
from collections.abc import Callable

# This is ugly but necessary to avoid a cyclic dependency
from typing import TYPE_CHECKING, cast

from PySide6.QtWidgets import QDialog, QWidget

from sasdata.data import SasData, SasMeasurement
from sasdata.dataset_types import DatasetType

from sas.refactored_plotting.PlotModifiers import PlotModifier
from sas.refactored_plotting.PlotWindow import PlotWindow

if TYPE_CHECKING:
    from sas.data_manager import NewDataManager as DataManager
    from sas.data_manager import TrackedData, TrackedPlot

# What a perspective can accept, written in one of two ways:
#   - A DatasetType *instance*, e.g. one_dim: only SasData whose dataset_type is
#     exactly that. Use this to accept some kinds of SasData but not others.
#   - A class, e.g. SasData or Trend: any instance of that class.
DataFormat = DatasetType | type

# Called with the datum once it has been sent to the perspective.
DataHandler = Callable[["TrackedData"], None]


def matches_format(datum: "TrackedData", data_format: DataFormat) -> bool:
    """Whether datum is of the given data format (see DataFormat)."""
    if isinstance(data_format, DatasetType):
        # The format is a dataset type like one_dim, so only SasData can match,
        # and only if it is that type of dataset.
        return isinstance(datum, SasData) and datum.dataset_type == data_format
    # Otherwise the format is a class, so any instance of it (or of a subclass) matches.
    return isinstance(datum, data_format)

# TODO: None of these classes belong in here. This is a temporary location of
# them so I can sketch out what they should look like.

# NOTE: The main difference in this class is that it takes in SasData objects
# rather than QT Oobjects.
class Perspective(QDialog):
    def __init__(self, data_manager: "DataManager", parent : QWidget | None) -> None:
        super().__init__(parent)
        self._data_manager = data_manager
        self.perspective_number: int = -1 # This gets reassigned by the data manager.
        self.finished.connect(self.onDone)

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the perspective"""

    @property
    @abstractmethod
    def title(self) -> str:
        """Window title"""

    @property
    @abstractmethod
    def accepted_data(self) -> list[tuple[DataFormat, DataHandler]]:
        """Master list of the data formats this perspective accepts, each paired
        with the handler that is called when data of that format is sent to it.
        The first matching entry wins."""

    def handler_for(self, datum: "TrackedData") -> DataHandler | None:
        for data_format, handler in self.accepted_data:
            if matches_format(datum, data_format):
                return handler
        return None

    def accepts(self, datum: "TrackedData") -> bool:
        return self.handler_for(datum) is not None

    def rejection_reason(self, datum: "TrackedData") -> str | None:
        """Why this datum can't be used even though its format is accepted, or
        None if it can. Unlike accepts(), this is only checked when data is
        actually sent, so Send stays enabled and the user is told the reason."""
        return None

    def receive(self, datum: "TrackedData"):
        """Called once data has been associated with this perspective."""
        handler = self.handler_for(datum)
        if handler is None:
            raise ValueError(f"{self.title} does not accept {datum}.")
        handler(datum)

    @property
    @abstractmethod
    def supports_multiple_data(self) -> bool:
        """Whether multiple data can be sent to the perspective. If not, data
        needs to be removed before it can be sent."""

    @property
    def formatName(self) -> str:
        return f"{self.title} #{self.perspective_number}"

    @abstractmethod
    def setData(self, data_item: list[SasData], is_batch: bool=False):
        pass

    # TODO: For this to work, there needs to be some way of identifying the
    # data. This could be done by the name but this may not be ideal.
    # Alternatively, SasData objects could be made hashable, and since SasData
    # objects should be immutable, this should suffice.
    @abstractmethod
    def removeData(self, data: SasData | list[SasData]):
        raise NotImplementedError(f"Remove data not implemented in {self.name}")

    @property
    def allowBatch(self) -> bool:
        return False

    @property
    def allowSwap(self) -> bool:
        return False

    def onDone(self):
        self._data_manager.remove_data(self)
        logging.info(f'Perspective {self.title} done.')

    @property
    def associatedData(self) -> list["TrackedData"]:
        """Only returns data which is specified in `supported_data`."""
        return [data for data in self._data_manager.get_all_associations(self)
                if any(isinstance(data, t) for t in self.supported_data)]

    def _singleAssociatedItemOfType(self, expected_type: type) -> "TrackedData | None":
        if self.supported_data != {expected_type} or self.supports_multiple_data:
            raise ValueError(f"This property can only be used if the perspective only accepts one {expected_type.__name__} object.")
        if len(self.associatedData) == 0:
            return None
        return self.associatedData[0]

    @property
    def associatedSasData(self) -> SasData | None:
        return cast(SasData | None, self._singleAssociatedItemOfType(SasData))

    @property
    def associatedSasMeasurement(self) -> SasMeasurement | None:
        return cast(SasMeasurement | None, self._singleAssociatedItemOfType(SasMeasurement))

    @property
    def associatedPlots(self) -> list["TrackedPlot"]:
        return [data for data in self._data_manager.get_all_associations(self)
                if isinstance(data, TrackedPlot)]

class Theory:
    # TODO: Need to put stuff here that is unique to Theory. Right now, looking
    # at the current SasView codebase, it seems they are all just Data1Ds with
    # nothing else special.
    pass


class FitModelParameters(ABC):
    pass

class TrackedFit:
    _data_manager: "DataManager"
    model_parameters: FitModelParameters
    fit: SasMeasurement

    @property
    def data_being_fitted(self) -> SasData | None:
        return self._data_manager.get_association_of_type(self, SasData)

    @property
    def formatName(self) -> str:
        if self.data_being_fitted:
            return f"Fit of {self.data_being_fitted.name}"
        else:
            # TODO: Could potentially return a more elaborate name of what the
            # theory object is about.
            return "Theory"

    def __init__(self, data_manager: "DataManager", model_parameters: FitModelParameters, fit_data: SasMeasurement):
        self._data_manager = data_manager
        self.model_parameters = model_parameters
        self.fit = fit_data


class TrackedPlot:
    _data_manager: "DataManager"
    plot_widget: PlotWindow | None

    def __init__(self, data_manager: "DataManager"):
        self._data_manager = data_manager
        self.plot_widget = None


    @property
    def to_plot(self) -> SasMeasurement | None:
        return self._data_manager.get_association_of_type(self, SasMeasurement)

    @property
    def fit(self) -> TrackedFit | None:
        return self._data_manager.get_association_of_type(self, TrackedFit)

    @property
    def modifiers(self) -> list[PlotModifier]:
        return [assoc for assoc in self._data_manager.get_all_associations(self) if isinstance(assoc, PlotModifier)]

    @property
    def formatName(self) -> str:
        if self.to_plot:
            return f"Plot of {self.to_plot.name}"
        else:
            return "Empty Plot"

    def update_plot(self):
        # TODO: Check the old window, and remove it if necessary.
        if self.to_plot:
            new_plot_widget = PlotWindow(self)
            if self.plot_widget:
                self._data_manager.replace_plot.emit(self.plot_widget, new_plot_widget)
            else:
                self._data_manager.new_plot.emit(new_plot_widget)
            self.plot_widget = new_plot_widget



