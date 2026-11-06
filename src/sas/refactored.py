import logging
from abc import abstractmethod
from collections.abc import Callable

# This is ugly but necessary to avoid a cyclic dependency
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QDialog, QWidget

from sasdata.data import SasData
from sasdata.dataset_types import DatasetType

if TYPE_CHECKING:
    from sas.data_manager import NewDataManager as DataManager
    from sas.data_manager import TrackedData

# A data format is either a sasdata DatasetType (e.g. one_dim), which matches
# SasData of exactly that type, or a class (e.g. SasData, Trend), which matches
# any instance of it.
DataFormat = DatasetType | type
DataHandler = Callable[["TrackedData"], None]


def matches_format(datum: "TrackedData", data_format: DataFormat) -> bool:
    if isinstance(data_format, DatasetType):
        return isinstance(datum, SasData) and datum.dataset_type == data_format
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
        return self._data_manager.get_all_associations(self)

class Theory:
    # TODO: Need to put stuff here that is unique to Theory. Right now, looking
    # at the current SasView codebase, it seems they are all just Data1Ds with
    # nothing else special.
    pass

