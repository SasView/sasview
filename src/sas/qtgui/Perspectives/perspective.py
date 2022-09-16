from abc import ABCMeta, abstractmethod
from typing import List, Optional, Union, Dict

from PyQt5.QtGui import QStandardItem
from PyQt5 import QtCore

from sas.qtgui.Utilities.Reports.reportdata import ReportData


class PerspectiveMeta(type(QtCore.QObject), ABCMeta):
    """ Metaclass for both ABC and Qt objects

    This is needed to enable the mixin of Perspective until
    a future refactoring unified the Qt functionality  of
    all the perspectives and brings it into the base class
    """


class Perspective(object, metaclass=PerspectiveMeta):

    """
    Mixin class for all perspectives,
    all perspectives should have these methods
    """

    @classmethod
    @property
    @abstractmethod
    def name(cls) -> str:
        """ Name of the perspective"""

    @property
    @abstractmethod
    def title(cls) -> str:
        """ Window title"""


    #
    # Data I/O calls
    #

    @abstractmethod
    def setData(self, data_item: List[QStandardItem], is_batch: bool=False):
        """ Set the data to be processed in this perspective, called when
        the 'send data' button is pressed"""
        pass # TODO: Should we really be passing Qt objects around, rather than actual data

    def removeData(self, data_list: Optional[Union[QStandardItem, List[QStandardItem]]]):
        """ Remove data from """
        raise NotImplementedError(f"Remove data not implemented in {self.name}")

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

    @classmethod
    @property
    @abstractmethod
    def ext(cls) -> str:
        """ File extension used when saving perspective data"""
        # TODO: Refactor to save_file_extension

    def isSerializable(self) -> bool:
        """ Can this perspective be serialised - default is no"""
        return False

    def serialiseAll(self) -> dict:
        raise NotImplementedError(f"{self.name} perspective is not serializable")

    @abstractmethod
    def updateFromParameters(self, params: dict):
        """ Update the perspective using a dictionary of parameters
        e.g. those loaded via open project or open analysis menu items"""
        pass

    # TODO: Use a more ordered datastructure for constraints
    def updateFromConstraints(self, constraints: Dict[str, list]):
        """
        Updates all tabs with constraints present in *constraint_dict*, where
        *constraint_dict*  keys are the fit page name, and the value is a
        list of constraints. A constraint is represented by a list [value,
        param, value_ex, validate, function] of attributes of a Constraint
        object""" # TODO: Sort out docstring



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

    def isClosable(self) -> bool:
        """ Flag that determines whether this perspective can be closed"""
        return False # TODO: refactor to closable property

    #
    # Menubar option
    #

    @property
    def supports_reports(self) -> bool:
        """ Does this perspective have a report functionality (currently used by menus and toolbar)"""
        return False

    @property
    def supports_fitting_menu(self) -> bool:
        """ Should the fitting menu be shown when using this perspective (unless its Fitting, probably not)"""
        return False

