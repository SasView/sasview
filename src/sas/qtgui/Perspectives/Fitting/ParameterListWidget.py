"""
ParameterListWidget - Encapsulates parameter list UI and logic.

This widget handles parameter selection, constraints, and editing for a parameter table,
reducing the complexity in FittingWidget.
"""
import logging
from collections.abc import Callable

from PySide6 import QtCore, QtGui, QtWidgets

logger = logging.getLogger(__name__)


class ParameterListWidget(QtWidgets.QWidget):
    """
    Widget for managing a parameter list with selection, constraints, and editing capabilities.

    This encapsulates the lstParams, lstPoly, and lstMagnetic functionality from FittingWidget.
    """

    # Signals
    selectionChangedSignal = QtCore.Signal(list)  # list of selected row indices
    parameterSelectedSignal = QtCore.Signal(bool)  # parameter selected/deselected for fitting
    constraintRequestedSignal = QtCore.Signal(str, list)  # action type, selected rows

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        tree_view: QtWidgets.QTreeView | None = None,
        model: QtGui.QStandardItemModel | None = None,
        model_key: str = "standard"
    ) -> None:
        """
        Initialize the ParameterListWidget.

        Args:
            parent: Parent widget
            tree_view: The QTreeView for displaying parameters
            model: The QStandardItemModel containing parameter data
            model_key: Key identifying this model ("standard", "poly", "magnet")
        """
        super().__init__(parent)

        self.tree_view = tree_view
        self.model = model
        self.model_key = model_key

        # Callbacks for constraint checking (set by parent)
        self.rowHasConstraint: Callable[[int, str], bool] | None = None
        self.rowHasActiveConstraint: Callable[[int, str], bool] | None = None
        self.isCheckable: Callable[[int, str], bool] | None = None

        # Callbacks for actions (set by parent)
        self.onAddSimpleConstraint: Callable[[], None] | None = None
        self.onDeleteConstraint: Callable[[], None] | None = None
        self.onEditConstraint: Callable[[], None] | None = None
        self.onShowMultiConstraint: Callable[[QtWidgets.QTreeView], None] | None = None
        self.onSelectParameters: Callable[[], None] | None = None
        self.onDeselectParameters: Callable[[], None] | None = None
        self.onShowModelDescription: Callable[[], QtWidgets.QMenu] | None = None

        if tree_view:
            self._setupTreeView()

    def _setupTreeView(self) -> None:
        """Configure the tree view with context menu."""
        if not self.tree_view:
            return

        self.tree_view.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.showContextMenu)
        self.tree_view.selectionModel().selectionChanged.connect(self._onSelectionChanged)

    def _onSelectionChanged(self) -> None:
        """Handle selection changes in the tree view."""
        if not self.tree_view:
            return
        selected_rows = self.getSelectedRows()
        self.selectionChangedSignal.emit(selected_rows)

    def getSelectedRows(self) -> list[int]:
        """
        Get list of selected row indices.

        Returns:
            List of selected row indices that are checkable
        """
        if not self.tree_view or not self.isCheckable:
            return []

        return [
            s.row() for s in self.tree_view.selectionModel().selectedRows()
            if self.isCheckable(s.row(), self.model_key)
        ]

    def showContextMenu(self, position: QtCore.QPoint) -> None:
        """
        Show context specific menu in the parameter table.

        When clicked on parameter(s): fitting/constraints options
        When clicked on white space: model description

        Args:
            position: Position where context menu was requested
        """
        if not self.tree_view:
            return

        rows = self.getSelectedRows()

        if not rows and self.onShowModelDescription:
            # Show model description
            menu = self.onShowModelDescription()
        else:
            # Show parameter context menu
            menu = self.createParameterContextMenu(rows)

        if menu:
            try:
                menu.exec_(self.tree_view.viewport().mapToGlobal(position))
            except AttributeError as ex:
                logger.error("Error generating context menu: %s" % ex)

    def createParameterContextMenu(self, rows: list[int]) -> QtWidgets.QMenu | None:
        """
        Create context menu for the parameter selection.

        Args:
            rows: List of selected row indices

        Returns:
            QMenu with context-appropriate actions
        """
        menu = QtWidgets.QMenu()
        num_rows = len(rows)

        if num_rows < 1:
            return menu

        # Build menu text
        param_string = "parameter " if num_rows == 1 else "parameters "
        to_string = "to its current value" if num_rows == 1 else "to their current values"

        # Check constraint status
        has_constraints = False
        has_real_constraints = False

        if self.rowHasConstraint and self.rowHasActiveConstraint:
            has_constraints = any([self.rowHasConstraint(i, self.model_key) for i in rows])
            has_real_constraints = any([self.rowHasActiveConstraint(i, self.model_key) for i in rows])

        # Create actions
        actionSelect = QtGui.QAction(self)
        actionSelect.setText("Select " + param_string + " for fitting")

        actionDeselect = QtGui.QAction(self)
        actionDeselect.setText("De-select " + param_string + " from fitting")

        actionConstrain = QtGui.QAction(self)
        actionConstrain.setText("Constrain " + param_string + to_string)

        actionRemoveConstraint = QtGui.QAction(self)
        actionRemoveConstraint.setText("Remove constraint")

        actionEditConstraint = QtGui.QAction(self)
        actionEditConstraint.setText("Edit constraint")

        actionMutualMultiConstrain = QtGui.QAction(self)
        actionMutualMultiConstrain.setText("Mutual constrain of selected parameters...")

        # Build menu
        menu.addAction(actionSelect)
        menu.addAction(actionDeselect)
        menu.addSeparator()

        if has_constraints:
            menu.addAction(actionRemoveConstraint)
            if num_rows == 1 and has_real_constraints:
                menu.addAction(actionEditConstraint)
        else:
            if num_rows == 2:
                menu.addAction(actionMutualMultiConstrain)
            else:
                menu.addAction(actionConstrain)

        # Connect actions to callbacks
        if self.onSelectParameters:
            actionSelect.triggered.connect(self.onSelectParameters)
        if self.onDeselectParameters:
            actionDeselect.triggered.connect(self.onDeselectParameters)
        if self.onAddSimpleConstraint:
            actionConstrain.triggered.connect(self.onAddSimpleConstraint)
        if self.onDeleteConstraint:
            actionRemoveConstraint.triggered.connect(self.onDeleteConstraint)
        if self.onEditConstraint:
            actionEditConstraint.triggered.connect(self.onEditConstraint)
        if self.onShowMultiConstraint and self.tree_view:
            actionMutualMultiConstrain.triggered.connect(
                lambda: self.onShowMultiConstraint(self.tree_view)
            )

        return menu

    def setCallbacks(
        self,
        rowHasConstraint: Callable[[int, str], bool] | None = None,
        rowHasActiveConstraint: Callable[[int, str], bool] | None = None,
        isCheckable: Callable[[int, str], bool] | None = None,
        onAddSimpleConstraint: Callable[[], None] | None = None,
        onDeleteConstraint: Callable[[], None] | None = None,
        onEditConstraint: Callable[[], None] | None = None,
        onShowMultiConstraint: Callable[[QtWidgets.QTreeView], None] | None = None,
        onSelectParameters: Callable[[], None] | None = None,
        onDeselectParameters: Callable[[], None] | None = None,
        onShowModelDescription: Callable[[], QtWidgets.QMenu] | None = None
    ) -> None:
        """
        Set callback functions for various operations.

        This allows the parent widget to provide implementations without tight coupling.
        """
        if rowHasConstraint:
            self.rowHasConstraint = rowHasConstraint
        if rowHasActiveConstraint:
            self.rowHasActiveConstraint = rowHasActiveConstraint
        if isCheckable:
            self.isCheckable = isCheckable
        if onAddSimpleConstraint:
            self.onAddSimpleConstraint = onAddSimpleConstraint
        if onDeleteConstraint:
            self.onDeleteConstraint = onDeleteConstraint
        if onEditConstraint:
            self.onEditConstraint = onEditConstraint
        if onShowMultiConstraint:
            self.onShowMultiConstraint = onShowMultiConstraint
        if onSelectParameters:
            self.onSelectParameters = onSelectParameters
        if onDeselectParameters:
            self.onDeselectParameters = onDeselectParameters
        if onShowModelDescription:
            self.onShowModelDescription = onShowModelDescription
