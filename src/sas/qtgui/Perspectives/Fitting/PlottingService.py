"""
PlottingService - Handle plotting logic for fitting perspective.

This class encapsulates plotting operations, separating plotting concerns
from the main FittingWidget and providing signal-based communication.
"""

import copy
from collections.abc import Callable
from typing import Any

from PySide6 import QtCore

from sas.qtgui.Perspectives.Fitting import FittingUtilities
from sas.qtgui.Perspectives.Fitting.ModelThread import Calc1D, Calc2D
from sas.qtgui.Plotting.PlotterData import Data1D, Data2D, DataRole
from sas.qtgui.Utilities import GuiUtils
from sas.system import config


class PlottingService(QtCore.QObject):
    """
    Manages plotting operations for fitting perspective.
    
    Responsibilities:
    - Calculate model data (1D/2D)
    - Create and manage plot objects
    - Emit signals for plot updates
    - Handle residuals calculation and plotting
    - Manage theory vs data plots
    
    Signals:
    - plotReadySignal: Emitted when plot data is ready
    - calculationStartedSignal: Emitted when calculation starts
    - calculationFinishedSignal: Emitted when calculation finishes
    - calculationFailedSignal: Emitted on calculation error
    """

    # Signals
    plotReadySignal = QtCore.Signal(list)  # list of plot objects
    calculationStartedSignal = QtCore.Signal()
    calculationFinishedSignal = QtCore.Signal()
    calculationFailedSignal = QtCore.Signal(object)  # error reason

    def __init__(self, parent: Any | None = None):
        """
        Initialize the PlottingService.
        
        Args:
            parent: Parent widget (optional)
        """
        super().__init__(parent)
        self.parent = parent

        # Current model data
        self.model_data: Data1D | Data2D | None = None
        self.theory_item: Any = None

        # State
        self.is2D = False
        self.data_is_loaded = False
        self.tab_id = 0

        # Callbacks (set by parent)
        self.get_data: Callable[[], Data1D | Data2D] | None = None
        self.get_kernel_module: Callable[[], Any] | None = None
        self.get_q_range: Callable[[], tuple[float, float]] | None = None
        self.get_weighting: Callable[[], int] | None = None
        self.get_smearer: Callable[[], Any] | None = None
        self.update_kernel_with_extra_params: Callable[[Any], None] | None = None

    def setConfiguration(
        self,
        is2D: bool,
        data_is_loaded: bool,
        tab_id: int
    ) -> None:
        """
        Set configuration parameters.
        
        Args:
            is2D: Whether data is 2D
            data_is_loaded: Whether data has been loaded
            tab_id: Tab identifier
        """
        self.is2D = is2D
        self.data_is_loaded = data_is_loaded
        self.tab_id = tab_id

    def calculateQGridForModel(
        self,
        data: Data1D | Data2D | None = None,
        model: Any | None = None,
        completefn: Callable[[dict], None] | None = None,
        use_threads: bool = True
    ) -> None:
        """
        Calculate model on Q grid (wrapper for Calc1D/2D).
        
        Args:
            data: Data object (uses callback if None)
            model: Kernel module (uses callback if None)
            completefn: Completion callback
            use_threads: Whether to use threading
        """
        # Get data if not provided
        if data is None and self.get_data:
            data = self.get_data()

        # Get model if not provided
        if model is None and self.get_kernel_module:
            kernel_module = self.get_kernel_module()
            if kernel_module is None:
                return
            model = copy.deepcopy(kernel_module)
            if self.update_kernel_with_extra_params:
                self.update_kernel_with_extra_params(model)

        # Get Q-range
        if self.get_q_range:
            q_min, q_max = self.get_q_range()
        else:
            q_min, q_max = 0.005, 0.1

        # Get smearer
        smearer = self.get_smearer() if self.get_smearer else None

        # Get weighting
        weighting = self.get_weighting() if self.get_weighting else 0
        weight = FittingUtilities.getWeight(
            data=data,
            is2d=self.is2D,
            flag=weighting
        )

        # Determine completion function
        if completefn is None:
            completefn = self.complete1D if isinstance(data, Data1D) else self.complete2D

        # Create calculation thread
        calc_class = Calc1D if isinstance(data, Data1D) else Calc2D
        calc_thread = calc_class(
            data=data,
            model=model,
            page_id=0,
            qmin=q_min,
            qmax=q_max,
            smearer=smearer,
            state=None,
            weight=weight,
            fid=None,
            toggle_mode_on=False,
            completefn=completefn,
            update_chisqr=True,
            exception_handler=self.calcException,
            source=None
        )

        # Notify calculation started
        self.calculationStartedSignal.emit()

        # Run calculation
        if use_threads:
            if config.USING_TWISTED:
                # Use Twisted
                from twisted.internet import threads
                thread = threads.deferToThread(calc_thread.compute)
                thread.addCallback(completefn)
                thread.addErrback(self.calculateDataFailed)
            else:
                # Use Python threads + Queue
                calc_thread.queue()
                calc_thread.ready(2.5)
        else:
            # Synchronous execution
            results = calc_thread.compute()
            completefn(results)

    def complete1D(self, return_data: dict) -> None:
        """
        Process completed 1D calculation.
        
        Args:
            return_data: Calculation results
        """
        self.calculationFinishedSignal.emit()

        if return_data is None:
            return

        # Delegate to parent widget's complete1D which handles everything properly
        parent_widget = self.parent()
        if parent_widget and hasattr(parent_widget, 'complete1D'):
            parent_widget.complete1D(return_data)

    def complete2D(self, return_data: dict) -> None:
        """
        Process completed 2D calculation.
        
        Args:
            return_data: Calculation results
        """
        self.calculationFinishedSignal.emit()

        if return_data is None:
            return

        # Delegate to parent widget's complete2D which handles everything properly
        parent_widget = self.parent()
        if parent_widget and hasattr(parent_widget, 'complete2D'):
            parent_widget.complete2D(return_data)

    def _appendPlotsPolyDisp(
        self,
        new_plots: list[Any],
        return_data: dict,
        fitted_data: Data1D | Data2D
    ) -> None:
        """
        Create polydispersity distribution plots.
        
        Args:
            new_plots: List to append plots to
            return_data: Calculation results
            fitted_data: Main fitted data
        """
        for plot in FittingUtilities.plotPolydispersities(
            return_data.get('model', None)
        ):
            if fitted_data.id:
                data_id = fitted_data.id.split()
                plot.id = "{} [{}] {}".format(
                    data_id[0], plot.name, " ".join(data_id[1:])
                )
            if fitted_data.name:
                data_name = fitted_data.name.split()
                plot.name = " ".join([data_name[0], plot.name] + data_name[1:])
            new_plots.append(plot)

    def requestPlots(self, item_name: str, item_model: Any) -> Any | None:
        """
        Request plots for the given item.
        
        Args:
            item_name: Name of the item
            item_model: Model containing plots
            
        Returns:
            Last data item if nothing was plotted, else None
        """
        if not self.get_kernel_module:
            return None

        kernel_module = self.get_kernel_module()
        if kernel_module is None:
            return None

        fitpage_name = kernel_module.name
        plots = GuiUtils.plotsFromDisplayName(item_name, item_model)

        # Check if fitted data has been shown
        data_shown = False
        item = None

        plot_list = []
        for item, plot in plots.items():
            if (plot.plot_role != DataRole.ROLE_DATA and
                fitpage_name in plot.name):
                data_shown = True
                plot_list.append((item, plot))

        # Emit plots if any were found
        if plot_list:
            for item_plot_pair in plot_list:
                self.plotReadySignal.emit([item_plot_pair])

        # Return last data item if nothing was plotted
        return None if data_shown else item

    def showTheoryPlot(self) -> None:
        """Show the current theory plot."""
        if self.theory_item is None or self.model_data is None:
            # Need to recalculate
            return

        # Request plots for theory
        self.requestPlots(
            self.model_data.name,
            self.theory_item.model()
        )

    def calcException(self, exception: Exception) -> None:
        """
        Handle calculation exception.
        
        Args:
            exception: The exception that occurred
        """
        self.calculationFailedSignal.emit(exception)

    def calculateDataFailed(self, reason: Any) -> None:
        """
        Handle calculation failure.
        
        Args:
            reason: Failure reason
        """
        self.calculationFailedSignal.emit(reason)
        print("Calculate Data failed with ", reason)

    def _getModelName(self) -> str:
        """
        Get the model name for plot labeling.
        
        Returns:
            Model name (e.g., "M1", "M2")
        """
        parent_widget = self.parent()
        if parent_widget and hasattr(parent_widget, 'modelName'):
            return parent_widget.modelName()
        return f"M{self.tab_id}"

    def setTheoryItem(self, item: Any) -> None:
        """
        Set the theory item.
        
        Args:
            item: Theory item from data explorer
        """
        self.theory_item = item

    def setCallbacks(
        self,
        get_data: Callable[[], Data1D | Data2D] | None = None,
        get_kernel_module: Callable[[], Any] | None = None,
        get_q_range: Callable[[], tuple[float, float]] | None = None,
        get_weighting: Callable[[], int] | None = None,
        get_smearer: Callable[[], Any] | None = None,
        update_kernel_with_extra_params: Callable[[Any], None] | None = None
    ) -> None:
        """
        Set callback functions.
        
        Args:
            get_data: Get current data
            get_kernel_module: Get kernel module
            get_q_range: Get Q-range (min, max)
            get_weighting: Get weighting flag
            get_smearer: Get smearer object
            update_kernel_with_extra_params: Update kernel with poly/magnetism
        """
        self.get_data = get_data
        self.get_kernel_module = get_kernel_module
        self.get_q_range = get_q_range
        self.get_weighting = get_weighting
        self.get_smearer = get_smearer
        self.update_kernel_with_extra_params = update_kernel_with_extra_params
