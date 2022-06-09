from abc import ABC, abstractmethod
from typing import List, Optional, Union, Dict
from PyQt5.QtGui import QStandardItem

class Perspective(ABC):

    """
    Mixin class for all perspectives,
    all perspectives should have these methods
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """ Name of the perspective"""
        pass

    @property
    @abstractmethod
    def title(self) -> str:
        """ Window title"""
        pass


    #
    # Data I/O calls
    #

    @abstractmethod
    def setData(self, data_item: List[QStandardItem], is_batch: bool=False):
        """ Set the data to be processed in this perspective, called when
        the 'send data' button is pressed"""
        pass # TODO: Should we really be passing Qt objects around, rather than actual data

    @abstractmethod
    def removeData(self, data_list: Optional[Union[QStandardItem, List[QStandardItem]]]):
        """ Remove data from """

    def allowBatch(self) -> bool:
        """ Can this perspective handle batch processing, default no"""
        return False # TODO: Make into property

    def allowSwap(self) -> bool:
        """ Does this perspective allow swapping of data,
        i.e. replacement of data without changing parameters,
        default no"""
        return False # TODO: Make into property

    def swapData(self, new_data: QStandardItem):
        """ Swap in new data without changing parameters"""
        raise NotImplementedError(f"{self.name} perspective does not current support swapping data sets")

    #
    # State loading/saving
    #

    @property
    @abstractmethod
    def ext(self) -> str:
        """ File extension used when saving perspective data"""
        pass # TODO: Refactor to save_file_extension

    def isSerializable(self) -> bool:
        """ Can this perspective be serialised - default is no"""
        return False # TODO: Refactor to serializable property

    def serialiseAll(self) -> dict:
        raise NotImplementedError(f"{self.name} perspective is not serializable")

    @ abstractmethod
    def updateFromParameters(self, params: dict): # TODO: Pythonic name
        """ Update the perspective using a dictionary of parameters
        e.g. those loaded via open project or open analysis menu items"""
        pass

    # TODO: Use a more ordered datastructure for constraints
    @abstractmethod
    def updateFromConstraints(self, constraints: Dict[str, list]):
        """
        Updates all tabs with constraints present in *constraint_dict*, where
        *constraint_dict*  keys are the fit page name, and the value is a
        list of constraints. A constraint is represented by a list [value,
        param, value_ex, validate, function] of attributes of a Constraint
        object""" # TODO: Sort out docstring
        pass


    #
    # Other shared functionality
    #

    def getReport(self) -> Optional[ReportData]: # TODO: Refactor to just report, or report_html
        """ A string containing the HTML to be shown in the report"""
        raise NotImplementedError(f"Report not implemented for {self.name}")


    #
    # Window behavior
    #

    @abstractmethod
    def setClosable(self, value: bool):
        """ Set whether this perspective can be closed"""
        pass # TODO: refactor to closable property

    @abstractmethod
    def isClosable(self) -> bool:
        pass # TODO: refactor to closable property


