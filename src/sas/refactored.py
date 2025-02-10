from abc import abstractmethod
from PySide6.QtWidgets import QDialog, QWidget
from sasdata.data import SasData

# This is ugly but necessary to avoid a cyclic dependency
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sas.data_manager import NewDataManager as DataManager

# TODO: None of these classes belong in here. This is a temporary location of
# them so I can sketch out what they should look like.

# NOTE: The main difference in this class is that it takes in SasData objects
# rather than QT Oobjects.
class Perspective(QDialog):
    def __init__(self, data_manager: "DataManager", parent : QWidget | None) -> None:
        super().__init__(parent)
        self._data_manager = data_manager

    @property
    @abstractmethod
    def name(self) -> str:
        """ Name of the perspective"""

    @property
    @abstractmethod
    def title(self) -> str:
        """ Window title"""

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

class Theory():
    # TODO: Need to put stuff here that is unique to Theory. Right now, looking
    # at the current SasView codebase, it seems they are all just Data1Ds with
    # nothing else special.
    pass
