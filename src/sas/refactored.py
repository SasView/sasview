import logging
from abc import abstractmethod

# This is ugly but necessary to avoid a cyclic dependency
from typing import TYPE_CHECKING, cast

from PySide6.QtWidgets import QDialog, QWidget

from sasdata.data import SasData, SasMeasurement

from sas.tracked_objects import TrackedPlot

if TYPE_CHECKING:
    from sas.data_manager import DataReference, TrackedData
    from sas.data_manager import NewDataManager as DataManager

# TODO: None of these classes belong in here. This is a temporary location of
# them so I can sketch out what they should look like.

# NOTE: The main difference in this class is that it takes in SasData objects
# rather than QT Oobjects.
class Perspective(QDialog):
    def __init__(self, data_manager: "DataManager", parent : QWidget | None) -> None:
        super().__init__(parent)
        self._data_manager = data_manager
        self.perspective_number: int = -1 # Assigned by number_perspective.
        # The data sent to this perspective, and the plots it shows.
        self._data_references: list["DataReference[TrackedData]"] = []
        self._plot_references: list["DataReference[TrackedPlot]"] = []
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
    def supported_data(self) -> set[type["TrackedData"]]:
        """The types of data that can be sent to the perspective"""

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
        if self._data_manager.is_tracked(self):
            self._data_manager.remove_data(self)
        logging.info(f'Perspective {self.title} done.')

    # TODO: Maybe we want to pass the new association. I was thinking that
    # perhaps the perspective will need to do a full update, and then this won't
    # be relevant.
    @abstractmethod
    def newAssocation(self):
        pass

    @abstractmethod
    def newData(self):
        pass

    def acceptData(self, datum: "TrackedData"):
        """Send datum to this perspective. Raises a ValueError if it can't
        accept it (see `checkCanAccept`)."""
        self.checkCanAccept(datum)
        self._data_references.append(self._data_manager.reference(self, datum))
        if isinstance(datum, SasData):
            self.newData()
        else:
            self.newAssocation()

    def addPlot(self, plot: TrackedPlot):
        """Show plot as one of this perspective's plots."""
        self._plot_references.append(self._data_manager.reference(self, plot))

    @property
    def associatedData(self) -> list["TrackedData"]:
        """The data sent to this perspective."""
        return [ref.get() for ref in self._data_references if ref]

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

    def checkCanAccept(self, datum: object):
        """Raise a ValueError if datum can't be sent to this perspective."""
        if not any(isinstance(datum, supported_type) for supported_type in self.supported_data):
            raise ValueError(f"{self.title} does not support this data.")
        if not self.supports_multiple_data and len(self.associatedData) > 0:
            raise ValueError(f"{self.title} doesn't support multiple data being sent to it.")

    @property
    def associatedPlots(self) -> list[TrackedPlot]:
        return [ref.get() for ref in self._plot_references if ref]

class Theory:
    # TODO: Need to put stuff here that is unique to Theory. Right now, looking
    # at the current SasView codebase, it seems they are all just Data1Ds with
    # nothing else special.
    pass


def number_perspective(to_number: Perspective, existing: list[Perspective]):
    """Give to_number the lowest number not used by an existing perspective of
    the same kind. Must be called before the perspective is added to the data
    manager, as its name depends on the number."""
    number = 1
    # TODO: Comparing titles might not be the best way to do this.
    relevant_perspective_numbers = [p.perspective_number for p in existing if p.title == to_number.title]
    while number in relevant_perspective_numbers:
        number += 1
    to_number.perspective_number = number
