"""
Utility functions for slicers in the 2D plotter, including unique ID generation and stacking mixin.
"""

import logging

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Plotting.PlotterData import Data1D

logger = logging.getLogger(__name__)


def _count_matching_ids(item, base_id: str) -> int:
    """
    Recursively count items with IDs starting with base_id.

    :param item: Tree item to search
    :param base_id: The base identifier to match
    :return: Count of matching items in this subtree
    """
    count = 0

    # Check current item
    d = item.data()
    if hasattr(d, "id") and isinstance(d.id, str) and d.id.startswith(base_id):
        count += 1

    # Recursively check all children
    for i in range(item.rowCount()):
        count += _count_matching_ids(item.child(i), base_id)

    return count


def generate_unique_plot_id(base_id: str, item) -> str:
    """
    Generate a unique plot ID by checking existing plots in the data tree.

    :param base_id: The base identifier string (e.g., "SectorQ" + data.name)
    :param item: The current item in the data explorer tree
    :return: A unique ID string, either base_id or base_id_N where N is a number
    """
    parent_item = item if item.parent() is None else item.parent()
    existing = _count_matching_ids(parent_item, base_id)

    return f"{base_id}_{existing}"


class StackableMixin:
    """
    Mixin class that provides stacking functionality for slicer plots.
    Any slicer that inherits from this mixin can stack multiple plots on the same window.

    Required attributes in the slicer class:
    - self.base: Reference to the 2D plot
    - self.data: The 2D data being sliced
    - self._item: The data explorer item
    - self.color: Color for this slicer
    - self._plot_id: The base plot ID (set before calling _create_or_update_plot)

    Required methods in the slicer class:
    - self._get_slicer_type_id(): Should return a string identifying the slicer type
    """

    def __init__(self):
        """Initialize stacking-related attributes"""
        self._plot_window = None  # Track the plot window this slicer uses
        self._actual_plot_id = None  # The actual ID used (may differ when stacking)

    @staticmethod
    def as_list(data: object) -> list:
        """
        Ensure data is returned as a list.
        Returns an empty list if data is None, a single-item list if data is a single item/
        
        :param data: Data which may be None, a single item, or a list
        :return: List of data items
        """
        if data is None:
            return []
        return data if isinstance(data, list) else [data]

    def _get_slicer_type_id(self) -> str:
        """
        Get the type identifier for this slicer.
        Should be overridden by subclasses to return something like "AnnulusPhi" + data.name

        :return: String identifying the slicer type and source data
        """
        raise NotImplementedError("Subclass must implement _get_slicer_type_id()")

    def _create_or_update_plot(self, new_plot: Data1D, item) -> None:
        """
        Create a new plot or update/stack onto an existing one based on state.

        :param new_plot: The Data1D object to plot
        :param item: The data explorer item
        """

        # Set the type_id for stacking identification
        new_plot.type_id = self._get_slicer_type_id()
        new_plot.custom_color = self.color

        # Check if this is an update to an existing plot
        if self._plot_window is not None and self._actual_plot_id is not None:
            # Update existing plot
            new_plot.id = self._actual_plot_id
            new_plot.name = self._actual_plot_id
            new_plot.title = self._actual_plot_id
            self._update_existing_plot(new_plot, item)
        else:
            # First time: check if we should stack
            should_stack = getattr(self.base, 'stackplots', False)

            if should_stack and (existing_plot_window := self._find_stackable_plot_window()):
                # Stack onto existing plot
                actual_id = self._append_to_plot_window(existing_plot_window, new_plot, item)
                self._plot_window = existing_plot_window
                self._actual_plot_id = actual_id
            else:
                # No existing window or not stacking, create new plot
                self._create_new_plot(new_plot, item)

    def _find_stackable_plot_window(self) -> object:
        """
        Find an existing plot window that can accept this slicer's data.
        Returns the latest matching plot window if found, None otherwise.

        :return: Plot window if found, None otherwise
        """

        # Search through active plots
        manager = getattr(self.base, 'manager', None)
        active_plots = getattr(manager, 'active_plots', {})
        match_type_id = self._get_slicer_type_id()  # ID of the slicer being created

        # Loop backwards to find the most recent matching plot
        for plot_window in reversed(list(active_plots.values())):
            data = getattr(plot_window, 'data', None)
            data_list = self.as_list(data)
            if data_list and hasattr(data_list[0], 'type_id') and data_list[0].type_id == match_type_id:
                return plot_window
        return None

    def _append_to_plot_window(self, plot_window: object, new_plot: Data1D, item) -> str:
        """
        Append new data to an existing plot window.

        :param plot_window: The existing plot window to append to
        :param new_plot: The new Data1D object to add
        :param item: The item for the data model
        :return: The actual ID assigned to the plot
        """
        new_plot.custom_color = self.color

        # Add to model
        GuiUtils.updateModelItemWithPlot(item, new_plot, new_plot.id)

        # Add to existing window
        plot_window.plot(data=new_plot, color=self.color, hide_error=False)

        # Notify manager
        self.base.manager.communicator.plotUpdateSignal.emit([new_plot])

        # Update slicer plots list if the slicer widget exists
        if (slicer_widget := getattr(self.base, 'slicer_widget', None)):
            slicer_widget.updateSlicerPlotList()

        return new_plot.id

    def _create_new_plot(self, new_plot: Data1D, item) -> None:
        """
        Create a new plot window.

        :param new_plot: The Data1D object to plot
        :param item: The data explorer item
        """
        # Add to model
        GuiUtils.updateModelItemWithPlot(item, new_plot, new_plot.id)

        # Signal to create plot
        self.base.manager.communicator.plotUpdateSignal.emit([new_plot])
        self.base.manager.communicator.forcePlotDisplaySignal.emit([item, new_plot])

        # Store references
        self._actual_plot_id = new_plot.id

        # Find the plot window that was created
        manager = getattr(self.base, 'manager', None)
        if manager and hasattr(manager, 'active_plots'):
            for plot_id, plot_window in manager.active_plots.items():
                data_list = self.as_list(getattr(plot_window, 'data', None))
                if plot_id == new_plot.id or any(getattr(d, 'id', None) == new_plot.id for d in data_list):
                    self._plot_window = plot_window
                    break

        # Update slicer plots list if the slicer widget exists
        if (slicer_widget := getattr(self.base, 'slicer_widget', None)):
            slicer_widget.updateSlicerPlotList()

    def _update_existing_plot(self, new_plot, item):
        """
        Update data in existing plot window.

        :param new_plot: The updated Data1D object
        :param item: The data explorer item
        """
        if self._plot_window is None:
            logger.warning(f"No plot window found for {new_plot.id}")
            return

        # Preserve color
        new_plot.custom_color = self.color

        # Replace plot data
        self._plot_window.replacePlot(new_plot.id, new_plot)

        # Update model
        GuiUtils.updateModelItemWithPlot(item, new_plot, new_plot.name)

        # Notify manager
        self.base.manager.communicator.plotUpdateSignal.emit([new_plot])

        # Update slicer plots list if the slicer widget exists
        if (slicer_widget := getattr(self.base, 'slicer_widget', None)):
            slicer_widget.updateSlicerPlotList()
