from sas.refactored_plotting.PlotModifiers import PlotModifier
from sas.refactored_plotting.SubTabs import SubTabs
from sas.refactored_plotting.PlotWidget import PlotWidget
import logging
from abc import abstractmethod, ABC

# This is ugly but necessary to avoid a cyclic dependency
from typing import TYPE_CHECKING, cast

from PySide6.QtWidgets import QDialog, QWidget

from sasdata.data import SasData

if TYPE_CHECKING:
    from sas.data_manager import NewDataManager as DataManager
    from sas.data_manager import TrackedData

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
        self._data_manager.remove_data(self)
        logging.info(f'Perspective {self.title} done.')

    # TODO: Maybe we want to pass the new association. I was thinking that
    # perhaps the perspective will need to do a full update, and then this won't
    # be relevant.
    @abstractmethod
    def newAssocation(self):
        pass

    @property
    def associatedData(self) -> list["TrackedData"]:
        return self._data_manager.get_all_associations(self)

    @property
    def associatedSasData(self) -> SasData | None:
        if self.supported_data != {SasData} or self.supports_multiple_data:
            raise ValueError("This property can only be used if the perspective only accepts one SasData object.")
        if len(self.associatedData) == 0:
            return None
        return cast(SasData, self.associatedData[0])
    
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

    @property
    def data_being_fitted(self) -> SasData | None:
        return self._data_manager.get_association_of_type(self, SasData)
    

class TrackedPlot:
    _data_manager: "DataManager"
    plot_widget: SubTabs | None

    def __init__(self, data_manager: "DataManager"):
        self._data_manager = data_manager
        self.plot_widget = None
        

    @property
    def to_plot(self) -> SasData | None:
        return self._data_manager.get_association_of_type(self, SasData)

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
            new_plot_widget = SubTabs(self)
            if self.plot_widget:
                self._data_manager.replace_plot.emit(self.plot_widget, new_plot_widget)
            else:
                self._data_manager.new_plot.emit(new_plot_widget)
            self.plot_widget = new_plot_widget
            
        

