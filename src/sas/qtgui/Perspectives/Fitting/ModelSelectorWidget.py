"""
ModelSelectorWidget - Encapsulates model/category/structure selection UI and logic.

This widget handles the combo boxes for category, model, and structure factor selection,
reducing complexity in FittingWidget.
"""
import logging
from collections import defaultdict
from collections.abc import Callable
from typing import Any

from PySide6 import QtCore, QtWidgets

logger = logging.getLogger(__name__)

# Constants
CATEGORY_DEFAULT = "Choose category..."
CATEGORY_STRUCTURE = "Structure Factor"
CATEGORY_CUSTOM = "Plugin Models"
MODEL_DEFAULT = "Choose model..."
STRUCTURE_DEFAULT = "None"


class ModelSelectorWidget(QtWidgets.QWidget):
    """
    Widget for managing category, model, and structure factor selection.

    Encapsulates the combo box logic and category management from FittingWidget.
    """

    # Signals
    categoryChangedSignal = QtCore.Signal(str)  # New category selected
    modelChangedSignal = QtCore.Signal(str)  # New model selected
    structureChangedSignal = QtCore.Signal(str)  # New structure factor selected

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        category_combo: QtWidgets.QComboBox | None = None,
        model_combo: QtWidgets.QComboBox | None = None,
        structure_combo: QtWidgets.QComboBox | None = None
    ) -> None:
        """
        Initialize the ModelSelectorWidget.

        Args:
            parent: Parent widget
            category_combo: Combo box for category selection
            model_combo: Combo box for model selection
            structure_combo: Combo box for structure factor selection
        """
        super().__init__(parent)

        self.category_combo = category_combo
        self.model_combo = model_combo
        self.structure_combo = structure_combo

        # Data
        self.master_category_dict: dict[str, Any] = defaultdict(list)
        self.models: dict[str, Any] = {}

        # State tracking
        self._previous_category_index: int = 0
        self._previous_model_index: int = 0

        # Callbacks (set by parent)
        self.onCategoryChanged: Callable[[str], None] | None = None
        self.onModelChanged: Callable[[str], None] | None = None
        self.onStructureChanged: Callable[[str], None] | None = None

        if category_combo:
            category_combo.currentIndexChanged.connect(self._handleCategoryChange)
        if model_combo:
            model_combo.currentIndexChanged.connect(self._handleModelChange)
        if structure_combo:
            structure_combo.currentIndexChanged.connect(self._handleStructureChange)

    def setMasterCategoryDict(self, category_dict: dict[str, Any]) -> None:
        """
        Set the master category dictionary.

        Args:
            category_dict: Dictionary mapping category names to model lists
        """
        self.master_category_dict = category_dict

    def setModels(self, models: dict[str, Any]) -> None:
        """
        Set the models dictionary.

        Args:
            models: Dictionary mapping model names to model objects
        """
        self.models = models

    def initializeCategoryCombo(self) -> None:
        """
        Initialize the category combo box with available categories.
        """
        if not self.category_combo:
            return

        category_list = sorted(self.master_category_dict.keys())

        self.category_combo.blockSignals(True)
        self.category_combo.clear()
        self.category_combo.addItem(CATEGORY_DEFAULT)
        self.category_combo.addItems(category_list)

        if CATEGORY_STRUCTURE not in category_list:
            self.category_combo.setItemData(
                self.category_combo.findText(CATEGORY_STRUCTURE),
                QtCore.Qt.NoItemFlags
            )

        self.category_combo.setCurrentIndex(0)
        self.category_combo.blockSignals(False)

    def initializeStructureCombo(self) -> None:
        """
        Initialize the structure factor combo box.
        """
        if not self.structure_combo or not self.master_category_dict:
            return

        structure_list = self.master_category_dict.get(CATEGORY_STRUCTURE, [])
        factors = [factor[0] for factor in structure_list]
        factors.insert(0, STRUCTURE_DEFAULT)

        self.structure_combo.blockSignals(True)
        self.structure_combo.clear()
        self.structure_combo.addItems(sorted(factors))
        self.structure_combo.blockSignals(False)

    def _handleCategoryChange(self, index: int) -> None:
        """
        Handle category combo box changes.

        Args:
            index: New selected index
        """
        if not self.category_combo:
            return

        category = self.category_combo.currentText()

        # Check if the user chose "Choose category entry"
        if category == CATEGORY_DEFAULT:
            # If the previous category was not the default, keep it
            if self._previous_category_index != 0:
                self.category_combo.blockSignals(True)
                self.category_combo.setCurrentIndex(self._previous_category_index)
                self.category_combo.blockSignals(False)
            return

        self._previous_category_index = index

        # Update model combo for this category
        self._updateModelCombo(category)

        # Emit signal and call callback
        self.categoryChangedSignal.emit(category)
        if self.onCategoryChanged:
            self.onCategoryChanged(category)

    def _handleModelChange(self, index: int) -> None:
        """
        Handle model combo box changes.

        Args:
            index: New selected index
        """
        if not self.model_combo:
            return

        model = self.model_combo.currentText()

        if model == MODEL_DEFAULT:
            # If the previous model was not the default, keep it
            if self._previous_model_index != 0:
                self.model_combo.blockSignals(True)
                self.model_combo.setCurrentIndex(self._previous_model_index)
                self.model_combo.blockSignals(False)
            return

        self._previous_model_index = index

        # Emit signal and call callback
        self.modelChangedSignal.emit(model)
        if self.onModelChanged:
            self.onModelChanged(model)

    def _handleStructureChange(self, index: int) -> None:
        """
        Handle structure factor combo box changes.

        Args:
            index: New selected index
        """
        if not self.structure_combo:
            return

        structure = self.structure_combo.currentText()

        # Emit signal and call callback
        self.structureChangedSignal.emit(structure)
        if self.onStructureChanged:
            self.onStructureChanged(structure)

    def _updateModelCombo(self, category: str) -> None:
        """
        Update the model combo box based on the selected category.

        Args:
            category: Selected category name
        """
        if not self.model_combo:
            return

        self.model_combo.blockSignals(True)
        self.model_combo.clear()

        if category == CATEGORY_STRUCTURE:
            # Structure factor category - disable model combo
            self.enableModelCombo(False)
            self.enableStructureCombo(True)
            if self.structure_combo:
                self.structure_combo.setCurrentIndex(0)
        else:
            # Regular category - enable model combo
            self.enableModelCombo(True)
            self.enableStructureCombo(False)

            # Populate models for this category
            model_list = self.master_category_dict.get(category, [])
            models_to_show = [m[0] for m in model_list if m[1]]  # Only enabled models

            self.model_combo.addItem(MODEL_DEFAULT)
            self.model_combo.addItems(sorted(models_to_show))

        self.model_combo.blockSignals(False)

    def enableModelCombo(self, enable: bool = True) -> None:
        """
        Enable or disable the model combo box.

        Args:
            enable: Whether to enable the combo
        """
        if self.model_combo:
            self.model_combo.setEnabled(enable)

    def enableStructureCombo(self, enable: bool = True) -> None:
        """
        Enable or disable the structure factor combo box.

        Args:
            enable: Whether to enable the combo
        """
        if self.structure_combo:
            self.structure_combo.setEnabled(enable)

    def getCurrentCategory(self) -> str:
        """
        Get the currently selected category.

        Returns:
            Current category name
        """
        if self.category_combo:
            return self.category_combo.currentText()
        return ""

    def getCurrentModel(self) -> str:
        """
        Get the currently selected model.

        Returns:
            Current model name
        """
        if self.model_combo:
            return self.model_combo.currentText()
        return ""

    def getCurrentStructure(self) -> str:
        """
        Get the currently selected structure factor.

        Returns:
            Current structure factor name
        """
        if self.structure_combo:
            return self.structure_combo.currentText()
        return ""

    def setCallbacks(
        self,
        onCategoryChanged: Callable[[str], None] | None = None,
        onModelChanged: Callable[[str], None] | None = None,
        onStructureChanged: Callable[[str], None] | None = None
    ) -> None:
        """
        Set callback functions for selection changes.

        Args:
            onCategoryChanged: Callback for category selection
            onModelChanged: Callback for model selection
            onStructureChanged: Callback for structure selection
        """
        if onCategoryChanged:
            self.onCategoryChanged = onCategoryChanged
        if onModelChanged:
            self.onModelChanged = onModelChanged
        if onStructureChanged:
            self.onStructureChanged = onStructureChanged
