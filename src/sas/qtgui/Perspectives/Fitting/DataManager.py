"""
DataManager - Handle dataset loading, weighting, and Q-range updates.

This class encapsulates data management logic for the fitting perspective,
separating data handling concerns from the main FittingWidget.
"""

from typing import Any, Callable
import copy
import numpy as np

from PySide6 import QtGui

from sas.qtgui.Plotting.PlotterData import Data1D, Data2D
from sas.qtgui.Utilities import GuiUtils
from sas.qtgui.Perspectives.Fitting.FittingLogic import FittingLogic
from sas.qtgui.Perspectives.Fitting import FittingUtilities


class DataManager:
    """
    Manages data loading, processing, and state for fitting operations.
    
    Responsibilities:
    - Load datasets from GUI items (single or batch)
    - Apply weighting to data for fitting
    - Calculate and update Q-range
    - Manage data state (is2D, batch fitting, data loaded)
    - Create default datasets for theory calculations
    """
    
    def __init__(self, parent: Any | None = None):
        """
        Initialize the DataManager.
        
        Args:
            parent: Parent widget (optional, for callbacks)
        """
        self.parent = parent
        
        # Data state
        self.data_is_loaded = False
        self.is_batch_fitting = False
        self.is2D = False
        
        # Data holders
        self.all_data: list[QtGui.QStandardItem] = []
        self.data_index = 0
        self._logic: list[FittingLogic] = [FittingLogic()]
        
        # Q-range parameters
        self.q_range_min = 0.005
        self.q_range_max = 0.1
        self.npts = 50
        self.log_points = True
        self.weighting = 0
        
        # Callbacks (set by parent)
        self.on_data_loaded: Callable[[], None] | None = None
        self.on_q_range_updated: Callable[[float, float, int], None] | None = None
        
    @property
    def logic(self) -> FittingLogic:
        """Get the current FittingLogic instance for the active data."""
        assert self._logic
        return self._logic[self.data_index]
    
    @property
    def data(self) -> Data1D | Data2D:
        """Get the current data object."""
        return self.logic.data
    
    def loadDataFromItems(self, value: QtGui.QStandardItem | list[QtGui.QStandardItem]) -> None:
        """
        Load data from GUI items (single or batch).
        
        Args:
            value: Single QStandardItem or list of items containing data
        """
        # Convert to list format
        if isinstance(value, list):
            self.is_batch_fitting = True
        else:
            value = [value]
        
        assert isinstance(value[0], QtGui.QStandardItem)
        
        # Keep reference to all datasets for batch
        self.all_data = value
        
        # Create logics with data items
        if len(value) == 1:
            # Single data - update existing logic
            self._logic[0].data = GuiUtils.dataFromItem(value[0])
        else:
            # Batch datasets - create multiple logics
            self._logic = []
            for data_item in value:
                logic = FittingLogic(data=GuiUtils.dataFromItem(data_item))
                self._logic.append(logic)
        
        # Determine data dimensionality
        self.is2D = isinstance(self.logic.data, Data2D)
        
        # Mark data as loaded
        self.data_is_loaded = True
        
        # Update Q-range from data
        self.updateQRange()
        
        # Notify parent if callback is set
        if self.on_data_loaded:
            self.on_data_loaded()
    
    def addWeightingToData(self, data: Data1D | Data2D) -> Data1D | Data2D:
        """
        Add weighting contribution to fitting data.
        
        Args:
            data: Data object to apply weighting to
            
        Returns:
            New data object with weighting applied
        """
        if not self.data_is_loaded:
            # No weighting for theories (dy = 0)
            return data
        
        new_data = copy.deepcopy(data)
        
        # Calculate weights
        weight = FittingUtilities.getWeight(
            data=data,
            is2d=self.is2D,
            flag=self.weighting
        )
        
        # Apply weights based on dimensionality
        if self.is2D:
            new_data.err_data = weight
        else:
            new_data.dy = weight
        
        return new_data
    
    def updateQRange(self) -> None:
        """
        Update Q-range from current data.
        
        Calculates Q-range from data if loaded, otherwise keeps current values.
        """
        if self.data_is_loaded:
            self.q_range_min, self.q_range_max, self.npts = \
                self.logic.computeDataRange()
        
        # Notify parent if callback is set
        if self.on_q_range_updated:
            self.on_q_range_updated(
                self.q_range_min,
                self.q_range_max,
                self.npts
            )
    
    def setQRangeParameters(
        self,
        q_min: float,
        q_max: float,
        npts: int,
        log_points: bool,
        weighting: int
    ) -> None:
        """
        Set Q-range parameters for calculations.
        
        Args:
            q_min: Minimum Q value
            q_max: Maximum Q value
            npts: Number of points
            log_points: Use logarithmic spacing
            weighting: Weighting type (0=none, 1=statistical, etc.)
        """
        self.q_range_min = q_min
        self.q_range_max = q_max
        self.npts = npts
        self.log_points = log_points
        self.weighting = weighting
    
    def createDefault1DDataset(self, tab_id: int) -> None:
        """
        Create a default 1D dataset for theory calculations.
        
        Args:
            tab_id: Tab identifier for the dataset
        """
        if self.log_points:
            qmin = -10.0 if self.q_range_min < 1.e-10 else np.log10(self.q_range_min)
            qmax = 10.0 if self.q_range_max > 1.e10 else np.log10(self.q_range_max)
            interval = np.logspace(
                start=qmin,
                stop=qmax,
                num=self.npts,
                endpoint=True,
                base=10.0
            )
        else:
            interval = np.linspace(
                start=self.q_range_min,
                stop=self.q_range_max,
                num=int(self.npts),
                endpoint=True
            )
        
        self.logic.createDefault1dData(interval, tab_id)
    
    def createDefault2DDataset(self, tab_id: int) -> None:
        """
        Create a default 2D dataset for theory calculations.
        
        Args:
            tab_id: Tab identifier for the dataset
        """
        qmax = self.q_range_max / np.sqrt(2)
        qstep = self.npts
        self.logic.createDefault2dData(qmax, qstep, tab_id)
    
    def createDefaultDataset(self, tab_id: int) -> None:
        """
        Create a default dataset (1D or 2D) based on current state.
        
        Args:
            tab_id: Tab identifier for the dataset
        """
        if self.is2D:
            self.createDefault2DDataset(tab_id)
        else:
            self.createDefault1DDataset(tab_id)
    
    def selectBatchData(self, index: int) -> None:
        """
        Select a specific dataset in batch fitting mode.
        
        Args:
            index: Index of the dataset to select
        """
        if 0 <= index < len(self.all_data):
            self.data_index = index
            self.updateQRange()
    
    def getWeight(self, data: Data1D | Data2D | None = None) -> Any:
        """
        Get weight array for the specified data.
        
        Args:
            data: Data object (uses current data if None)
            
        Returns:
            Weight array
        """
        if data is None:
            data = self.data
        
        return FittingUtilities.getWeight(
            data=data,
            is2d=self.is2D,
            flag=self.weighting
        )
    
    def reset(self) -> None:
        """Reset the data manager to initial state."""
        self.data_is_loaded = False
        self.is_batch_fitting = False
        self.is2D = False
        self.all_data = []
        self.data_index = 0
        self._logic = [FittingLogic()]
    
    def setCallbacks(
        self,
        on_data_loaded: Callable[[], None] | None = None,
        on_q_range_updated: Callable[[float, float, int], None] | None = None
    ) -> None:
        """
        Set callback functions for data manager events.
        
        Args:
            on_data_loaded: Called when data is loaded
            on_q_range_updated: Called when Q-range is updated
        """
        self.on_data_loaded = on_data_loaded
        self.on_q_range_updated = on_q_range_updated
