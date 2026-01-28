"""
Base class for creating multiple symmetric slicers.
"""

import logging
import warnings
from abc import ABC, abstractmethod

import numpy as np

from sas.qtgui.Plotting.SlicerModel import SlicerModel
from sas.qtgui.Plotting.Slicers.BaseInteractor import BaseInteractor
from sas.qtgui.Plotting.Slicers.SectorSlicer import SectorInteractor
from sas.qtgui.Plotting.Slicers.SlicerUtils import StackableMixin
from sas.qtgui.Plotting.Slicers.WedgeSlicer import WedgeInteractorPhi, WedgeInteractorQ
from sas.qtgui.Utilities.GuiUtils import toDouble

logger = logging.getLogger(__name__)


class MultiSlicerBase(BaseInteractor, SlicerModel, StackableMixin, ABC):
    """
    Base class for creating multiple symmetric slicers that move together as a unit.

    This class handles:
    - Creating multiple slicer instances evenly spaced around the circle
    - Synchronizing movement of all slicers with one master
    - Disabling interaction for non-master slicers
    - Managing model updates and UI parameter changes

    Subclasses must implement:
    - _get_slicer_class() - return the single slicer class to instantiate
    - _get_interactor_names() - return list of interactor attribute names
    - _update_slicer_position(slicer, index, master) - update position for each slicer
    - _on_model_changed(item) - handle UI parameter changes
    """

    def __init__(self, base, axes, count, item=None, color="black", zorder=3):
        BaseInteractor.__init__(self, base, axes, color=color)
        SlicerModel.__init__(self)
        StackableMixin.__init__(self)

        self.markers = []
        self.axes = axes
        self._item = item
        self.base = base

        self.qmax = max(self.data.xmax, np.fabs(self.data.xmin), self.data.ymax, np.fabs(self.data.ymin))
        self.dqmin = min(np.fabs(self.data.qx_data))
        self.connect = self.base.connect

        self.count = count
        self.slicers = []
        self.angle_step = 2 * np.pi / self.count

        self._create_slicers(zorder)

        # Get data from first slicer for compatibility
        if self.slicers:
            self.data = self.slicers[0].data
            self.qmax = self.slicers[0].qmax

            # only wedges have dqmin
            if hasattr(self.slicers[0], "dqmin"):
                self.dqmin = self.slicers[0].dqmin

            self._model = self.slicers[0]._model

            self._connect_master_slicer()

            # Connect model changes to synchronize all slicers
            if self._model is not None:
                self._model.itemChanged.connect(self._on_model_changed)

    @abstractmethod
    def _get_slicer_class(self):
        """
        Return the slicer class to instantiate.
        Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    def _get_interactor_names(self):
        """
        Return the list of interactor attribute names.
        Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    def _update_slicer_position(self, slicer, index, master, moved_interactor_name=None):
        """
        Update the position of the given slicer based on the master slicer.
        Must be implemented by subclasses.

        Parameters:
        - slicer: The slicer to update
        - index: The index of the slicer in the list
        - master: The master slicer to synchronize with
        - moved_interactor_name: The name of the interactor that was moved
        """
        pass

    def _on_model_changed(self, item):
        """Base implementation with batching - subclasses should call this after processing"""
        # After subclass updates geometry, batch-post data for all non-master slicers
        if item is None or not self.slicers:
            return

        xlim, ylim = self.axes.get_xlim(), self.axes.get_ylim()

        # Suspend plot signals during batch update
        manager = getattr(self.base, "manager", None)
        if manager is not None:
            setattr(manager, "_suspend_plot_signals", True)
            if not hasattr(manager, "_pending_plot_updates"):
                manager._pending_plot_updates = []

        # Post data for all secondary slicers
        for i, slicer in enumerate(self.slicers[1:], start=1):
            try:
                slicer._post_data()
            except Exception as e:
                logger.warning(f"Failed to post data for slicer {i + 1}: {e}")

        # Flush pending updates
        if manager is not None:
            setattr(manager, "_suspend_plot_signals", False)
            pending = getattr(manager, "_pending_plot_updates", [])
            if pending:
                unique = []
                seen = set()
                for p in pending:
                    pid = getattr(p, "id", None)
                    if pid not in seen:
                        seen.add(pid)
                        unique.append(p)
                try:
                    manager.communicator.plotUpdateSignal.emit(unique)
                finally:
                    manager._pending_plot_updates = []

        self.axes.set_xlim(xlim)
        self.axes.set_ylim(ylim)
        self.base.draw()

    def _create_slicers(self, zorder):
        """
        Create all slicers and position them evenly around the circle.

        Parameters:
        - zorder: The z-order for drawing the slicers
        """

        # Store the axis limits
        xlim, ylim = self.axes.get_xlim(), self.axes.get_ylim()

        for i in range(self.count):
            slicer_class = self._get_slicer_class()

            color = self.base._get_next_slicer_color()

            slicer = slicer_class(base=self.base, axes=self.axes, item=self._item, color=color, zorder=zorder + 1)

            # Disable model updates for all but the first slicer
            if i > 0:
                slicer.update_model = False

            # Set initial position
            self._update_slicer_position(slicer, i, None)

            # Update interactors
            for interactor_name in self._get_interactor_names():
                if hasattr(slicer, interactor_name):
                    getattr(slicer, interactor_name).update()

            # Disable interaction for non-master slicers
            if i > 0:
                self._disable_slicer_interaction(slicer)

            self.slicers.append(slicer)
            slicer._post_data()

        self.base.draw()

        # Restore axis limits
        self.axes.set_xlim(xlim)
        self.axes.set_ylim(ylim)

    def _disable_slicer_interaction(self, slicer):
        """
        Disable interaction for the given slicer to avoid clutter.
        The slicer lines remain visible for context but are not interactive.

        Parameters:
        - slicer: The slicer to disable interaction for
        """
        marker_attributes = [
            "marker",  # ArcInteractor
            "inner_marker",  # LineInteractor (central line)
            "l_marker",  # RadiusInteractor (left line)
            "r_marker",  # RadiusInteractor (right line)
            "left_marker",  # LineInteractor (side line)
            "right_marker",  # LineInteractor (side line)
        ]
        line_attributes = [
            "line",  # LineInteractor (central_line)
            "arc",  # ArcInteractor (inner_arc, outer_arc)
            "l_line",  # RadiusInteractor (left line)
            "r_line",  # RadiusInteractor (right line)
            "left_line",  # LineInteractor (side_line)
            "right_line",  # LineInteractor (side_line)
        ]

        for interactor in self._get_interactor_names():
            if not hasattr(slicer, interactor):
                continue

            interactor = getattr(slicer, interactor)

            for attr in marker_attributes:
                if hasattr(interactor, attr):
                    marker = getattr(interactor, attr)
                    if marker is not None:
                        marker.set_visible(False)
                        marker.set_picker(False)
                        marker.set_pickradius(0)

            # Additionally, remove line pickers to disable interactivity
            for line_attr in line_attributes:
                if hasattr(interactor, line_attr):
                    line = getattr(interactor, line_attr)
                    if line is not None:
                        line.set_picker(False)
                        line.set_pickradius(0)

            # Disable interaction flags
            interactor.has_move = False

    def _connect_master_slicer(self):
        """
        Connect the moveend signal of the first slicer to update all slicers.
        """
        master = self.slicers[0]

        # Store original methods
        self.original_moveends = {}
        self.original_moves = {}

        for interactor_name in self._get_interactor_names():
            if not hasattr(master, interactor_name):
                continue

            interactor = getattr(master, interactor_name)

            self.original_moveends[interactor_name] = interactor.moveend
            self.original_moves[interactor_name] = interactor.move

            # Replace with the synchronized moveend
            interactor.moveend = lambda ev, name=interactor_name: self._synchronized_moveend(ev, name)
            interactor.move = lambda x, y, ev, name=interactor_name: self._synchronized_move(x, y, ev, name)

    def _synchronized_move(self, x, y, ev, interactor_name):
        """
        Called during dragging to update all slicers.

        Parameters:
        - x: The x-coordinate
        - y: The y-coordinate
        - ev: The mouse event
        - interactor_name: The name of the interactor being moved
        """

        master = self.slicers[0]
        original_move = self.original_moves[interactor_name]
        original_move(x, y, ev)

        xlim, ylim = self.axes.get_xlim(), self.axes.get_ylim()

        master.update()

        # Update other slicers
        for i, slicer in enumerate(self.slicers[1:], start=1):
            self._update_slicer_position(slicer, i, master, moved_interactor_name=interactor_name)

            for name in self._get_interactor_names():
                if hasattr(slicer, name):
                    getattr(slicer, name).update()

        self.axes.set_xlim(xlim)
        self.axes.set_ylim(ylim)
        self.base.canvas.draw_idle()

    def _synchronized_moveend(self, ev, interactor_name):
        """
        Called after dragging to finalize all slicers.
        """
        # Store axis limits to prevent auto-scaling
        xlim, ylim = self.axes.get_xlim(), self.axes.get_ylim()

        master = self.slicers[0]

        # Block model signals during batch geometry update to prevent premature recomputation
        if self._model is not None:
            self._model.blockSignals(True)

        # Update master geometry
        master.update()

        # Synchronize geometry for all secondary slicers
        for i, slicer in enumerate(self.slicers[1:], start=1):
            self._update_slicer_position(slicer, i, master, moved_interactor_name=interactor_name)

            # Update visual representation only (lines, markers)
            for name in self._get_interactor_names():
                if hasattr(slicer, name):
                    getattr(slicer, name).update()

        # Restore axis limits before posting data
        self.axes.set_xlim(xlim)
        self.axes.set_ylim(ylim)

        # Unblock model signals
        if self._model is not None:
            self._model.blockSignals(False)

        # Post master data first
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                master._post_data()
        except (ValueError, RuntimeError) as e:
            logger.warning(f"Failed to post data for master slicer: {e}")

        # Now post data for all secondary slicers (with update_model temporarily enabled)
        for i, slicer in enumerate(self.slicers[1:], start=1):
            try:
                # Temporarily enable model updates for this slicer
                old_update_model = slicer.update_model
                slicer.update_model = True
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    slicer._post_data()

                # Restore original state
                slicer.update_model = old_update_model
            except (ValueError, RuntimeError) as e:
                logger.warning(f"Failed to post data for slicer {i + 1}: {e}")

        # Update slicer plots list once
        if hasattr(self.base, 'slicer_widget') and self.base.slicer_widget is not None:
            try:
                self.base.slicer_widget.updateSlicerPlotList()
            except Exception:
                # Best-effort UI update; ignore failures so they do not prevent drawing.
                pass

        self.base.draw()

    def clear(self):
        """
        Clear all slicers from the axes.
        """
        for slicer in self.slicers:
            slicer.clear()
        self.slicers = []

    def getParams(self):
        """
        Get parameters from the master slicer.
        """
        if self.slicers:
            return self.slicers[0].getParams()
        return {}

    def setParams(self, params):
        """
        Set parameters for all slicers based on the master slicer.

        Parameters:
        - params: Dictionary of parameters to set
        """
        if not self.slicers:
            return

        master = self.slicers[0]
        master.setParams(params)

        # Update other slicers
        for i, slicer in enumerate(self.slicers[1:], start=1):
            self._update_slicer_position(slicer, i, master)

            for name in self._get_interactor_names():
                if hasattr(slicer, name):
                    getattr(slicer, name).update()

            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    slicer._post_data()
            except (ValueError, RuntimeError) as e:
                logger.warning(f"Failed to post data for slicer {i + 1}: {e}")

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                master._post_data()
        except (ValueError, RuntimeError) as e:
            logger.warning(f"Failed to post data for master slicer: {e}")

        self.base.draw()

    def draw(self):
        """
        Draw the canvas.
        """
        self.base.draw()

    def validate(self, param_name, param_value):
        """Validate parameters using master slicer"""
        if self.slicers:
            return self.slicers[0].validate(param_name, param_value)
        return True


class WedgeInteractorMulti(MultiSlicerBase):
    """
    Creates multiple symmetric wedge slicers that move together as a unit.
    Works with both WedgeInteractorPhi (phi mode) and WedgeInteractorQ (Q mode).
    The plotting mode is determined by the slicer_class passed to __init__.
    """

    def __init__(self, base, axes, count, slicer_class, item=None, color="black", zorder=3):
        """
        Initialize multiple wedge slicers.
        
        Parameters:
        - base: The base plotter
        - axes: The matplotlib axes
        - count: Number of slicers to create
        - slicer_class: Either WedgeInteractorPhi or WedgeInteractorQ
        - item: Optional data item
        - color: Color for the slicers
        - zorder: Z-order for drawing
        """
        self.slicer_class = slicer_class
        super().__init__(base, axes, count, item, color, zorder)

    def _get_slicer_class(self):
        """Return the wedge slicer class (Phi or Q mode)"""
        return self.slicer_class

    def _get_interactor_names(self):
        """Return list of interactor names for wedge slicers"""
        return ["inner_arc", "outer_arc", "radial_lines", "central_line"]

    def _update_slicer_position(self, slicer, index, master, moved_interactor_name=None):
        """Update wedge position with angular offset"""
        if master is None:
            # Initial positioning - spread evenly around full circle
            theta = index * self.angle_step
            slicer.theta = theta
            slicer.central_line.theta = theta
            slicer.inner_arc.theta = theta
            slicer.outer_arc.theta = theta
            slicer.radial_lines.theta = theta
        else:
            # Sync with master - detect which interactor moved
            if moved_interactor_name == "central_line":
                master_theta = master.central_line.theta
            elif moved_interactor_name == "radial_lines":
                master_theta = master.radial_lines.theta
            elif moved_interactor_name == "inner_arc":
                master_theta = master.inner_arc.theta
            elif moved_interactor_name == "outer_arc":
                master_theta = master.outer_arc.theta
            else:
                logger.warning(f"Unexpected interactor name: {moved_interactor_name}")
                master_theta = master.central_line.theta

            # Sync radii and phi
            slicer.r1 = master.r1
            slicer.r2 = master.r2
            slicer.phi = master.phi

            # Calculate offset and apply
            offset_theta = index * self.angle_step
            slicer.theta = (master_theta + offset_theta) % (2 * np.pi)

            # Update all interactors
            slicer.inner_arc.radius = slicer.r1
            slicer.inner_arc.theta = slicer.theta
            slicer.inner_arc.phi = slicer.phi

            slicer.outer_arc.radius = slicer.r2
            slicer.outer_arc.theta = slicer.theta
            slicer.outer_arc.phi = slicer.phi

            slicer.radial_lines.r1 = slicer.r1
            slicer.radial_lines.r2 = slicer.r2
            slicer.radial_lines.theta = slicer.theta
            slicer.radial_lines.phi = slicer.phi

            slicer.central_line.theta = slicer.theta

    def _on_model_changed(self, item):
        """Handle parameter changes from UI"""
        if item is None:
            return

        param_name = self._model.item(item.row(), 0).text()
        param_value_str = self._model.item(item.row(), 1).text()

        xlim, ylim = self.axes.get_xlim(), self.axes.get_ylim()

        try:
            if param_name == "phi [deg]":
                master_theta = toDouble(param_value_str) * np.pi / 180.0
                for i, slicer in enumerate(self.slicers):
                    new_theta = (master_theta + i * self.angle_step) % (2 * np.pi)
                    slicer.theta = new_theta
                    slicer.central_line.theta = new_theta
                    slicer.inner_arc.theta = new_theta
                    slicer.outer_arc.theta = new_theta
                    slicer.radial_lines.theta = new_theta

                    for name in self._get_interactor_names():
                        getattr(slicer, name).update()

            elif param_name == "delta_phi [deg]":
                delta_phi = toDouble(param_value_str) * np.pi / 180.0
                if delta_phi <= 0 or delta_phi >= np.pi:
                    return

                for i, slicer in enumerate(self.slicers):
                    slicer.phi = delta_phi
                    slicer.radial_lines.phi = delta_phi
                    slicer.inner_arc.phi = delta_phi
                    slicer.outer_arc.phi = delta_phi

                    slicer.radial_lines.update()
                    slicer.inner_arc.update()
                    slicer.outer_arc.update()

            elif param_name == "r_min":
                r_min = toDouble(param_value_str)
                if r_min <= 0:
                    return

                for i, slicer in enumerate(self.slicers):
                    slicer.r1 = r_min
                    slicer.inner_arc.radius = r_min
                    slicer.radial_lines.r1 = r_min

                    slicer.inner_arc.update()
                    slicer.radial_lines.update()

            elif param_name == "r_max":
                r_max = toDouble(param_value_str)
                if r_max <= 0:
                    return

                for i, slicer in enumerate(self.slicers):
                    slicer.r2 = r_max
                    slicer.outer_arc.radius = r_max
                    slicer.radial_lines.r2 = r_max

                    slicer.outer_arc.update()
                    slicer.radial_lines.update()

            elif param_name == "nbins":
                nbins = int(toDouble(param_value_str))
                if nbins < 1:
                    return

                for i, slicer in enumerate(self.slicers):
                    slicer.nbins = nbins

        except Exception as e:
            logger.error(f"Error in _on_model_changed: {e}")

        self.axes.set_xlim(xlim)
        self.axes.set_ylim(ylim)

        # call base class to handle batching
        super()._on_model_changed(item)


class WedgeInteractorPhiMulti(WedgeInteractorMulti):
    """Multiple wedge slicers in Phi mode (plots vs phi)"""
    def __init__(self, base, axes, count, item=None, color="black", zorder=3):
        super().__init__(base, axes, count, WedgeInteractorPhi, item, color, zorder)


class WedgeInteractorQMulti(WedgeInteractorMulti):
    """Multiple wedge slicers in Q mode (plots vs Q)"""
    def __init__(self, base, axes, count, item=None, color="black", zorder=3):
        super().__init__(base, axes, count, WedgeInteractorQ, item, color, zorder)


class SectorInteractorMulti(MultiSlicerBase):
    """
    Creates multiple symmetric sector slicers that move together as a unit.
    """

    def _get_slicer_class(self):
        """Return the SectorInteractor class"""
        return SectorInteractor

    def _get_interactor_names(self):
        """Return list of interactor names for sector slicers"""
        return ["main_line", "left_line", "right_line"]

    def _update_slicer_position(self, slicer, index, master, moved_interactor_name=None):
        """Update sector position with angular offset"""
        if master is None:
            # Initial positioning - half circle as it spans both sides
            theta = index * self.angle_step / 2
            slicer.theta2 = theta

            # Default phi offset
            slicer.phi = np.pi / 12

            slicer.main_line.theta = theta

            slicer.left_line.theta2 = theta
            slicer.left_line.phi = slicer.phi
            slicer.left_line.theta = theta + slicer.phi

            slicer.right_line.theta2 = theta
            slicer.right_line.phi = -slicer.phi
            slicer.right_line.theta = theta - slicer.phi

        else:
            # Determine which interactor moved and get master_theta
            master_theta = None

            if moved_interactor_name == "main_line":
                # Preserve each slicer's existing side-line separation (phi)
                # Only align the central/main line angle to the master's.
                master_theta = master.main_line.theta
            elif moved_interactor_name == "left_line":
                # left_line.theta2 is the shared anchor for sectors
                master_theta = master.left_line.theta2
                slicer.phi = master.left_line.phi
            elif moved_interactor_name == "right_line":
                master_theta = master.right_line.theta2
                slicer.phi = -master.right_line.phi
            else:
                # Should never reach here, but provide safe fallback
                logger.warning(f"Unexpected interactor name: {moved_interactor_name}")
                master_theta = master.main_line.theta

            # Guard: ensure master_theta is valid
            if master_theta is None:
                master_theta = master.main_line.theta if hasattr(master, "main_line") else getattr(master, "theta2", 0)

            # Calculate offset and apply (half circle spacing for sectors)
            offset_theta = index * self.angle_step / 2
            slicer.theta2 = (master_theta + offset_theta) % np.pi

            # Update all interactors
            slicer.main_line.theta = slicer.theta2

            slicer.left_line.theta2 = slicer.theta2
            slicer.left_line.phi = slicer.phi
            slicer.left_line.theta = slicer.theta2 + slicer.phi

            slicer.right_line.theta2 = slicer.theta2
            slicer.right_line.phi = -slicer.phi
            slicer.right_line.theta = slicer.theta2 - slicer.phi

    def _on_model_changed(self, item):
        """Handle parameter changes from UI"""
        if item is None or not self.slicers:
            return

        param_name = self._model.item(item.row(), 0).text()
        param_value_str = self._model.item(item.row(), 1).text()

        xlim, ylim = self.axes.get_xlim(), self.axes.get_ylim()

        try:
            if param_name == "Phi [deg]":
                # Central angle
                master_theta = toDouble(param_value_str) * np.pi / 180.0

                # Update master's theta2 to keep consistency
                self.slicers[0].theta2 = master_theta
                self.slicers[0].main_line.theta = master_theta

                for i, slicer in enumerate(self.slicers):
                    new_theta = (master_theta + i * self.angle_step / 2) % np.pi
                    slicer.theta2 = new_theta

                    slicer.main_line.theta = new_theta
                    slicer.main_line.update()

                    slicer.left_line.theta2 = new_theta
                    slicer.left_line.theta = new_theta + slicer.left_line.phi
                    slicer.left_line.update()

                    slicer.right_line.theta2 = new_theta
                    slicer.right_line.theta = new_theta + slicer.right_line.phi
                    slicer.right_line.update()

            elif param_name == "Delta_Phi [deg]":
                # Angular width
                delta_phi = toDouble(param_value_str) * np.pi / 180.0
                if delta_phi <= 0:
                    return

                for i, slicer in enumerate(self.slicers):
                    slicer.phi = delta_phi

                    slicer.left_line.phi = delta_phi
                    slicer.left_line.theta = slicer.left_line.theta2 + delta_phi
                    slicer.left_line.update()

                    slicer.right_line.phi = -delta_phi
                    slicer.right_line.theta = slicer.right_line.theta2 - delta_phi
                    slicer.right_line.update()

            elif param_name == "nbins":
                nbins = int(toDouble(param_value_str))
                if nbins < 1:
                    return

        except Exception as e:
            logger.error(f"Error in _on_model_changed: {e}")

        self.axes.set_xlim(xlim)
        self.axes.set_ylim(ylim)

        # call base class to handle batching
        super()._on_model_changed(item)
