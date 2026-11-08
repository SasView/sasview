import copy
import json
import logging
import os
import re
import traceback
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets
from twisted.internet import threads

from sasmodels.sasview_model import MODELS, SasviewModel, load_standard_models

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas import config
from sas.qtgui.Perspectives.Fitting import FittingUtilities
from sas.qtgui.Perspectives.Fitting.ConsoleUpdate import ConsoleUpdate
from sas.qtgui.Perspectives.Fitting.Constraint import Constraint
from sas.qtgui.Perspectives.Fitting.controller import FitPageController
from sas.qtgui.Perspectives.Fitting.DocumentShadow import DocumentShadow, mirrors
from sas.qtgui.Perspectives.Fitting.FitPage import FitPage
from sas.qtgui.Perspectives.Fitting.FitThread import FitThread
from sas.qtgui.Perspectives.Fitting.FittingConstants import (  # noqa: F401 (re-exported)
    CATEGORY_CUSTOM,
    CATEGORY_DEFAULT,
    CATEGORY_STRUCTURE,
    DEFAULT_POLYDISP_FUNCTION,
    LAYERED_MODELS,
    MODEL_DEFAULT,
    STRUCTURE_DEFAULT,
    SUPPRESSED_MODELS,
    TAB_MAGNETISM,
    TAB_ORDERING,
    TAB_POLY,
    polydispersity_plot_name,
)
from sas.qtgui.Perspectives.Fitting.FittingController import FittingController
from sas.qtgui.Perspectives.Fitting.FittingLogic import FittingLogic
from sas.qtgui.Perspectives.Fitting.FittingState import FittingState
from sas.qtgui.Perspectives.Fitting.LegacyKernelSync import LegacyKernelSync
from sas.qtgui.Perspectives.Fitting.MagnetismWidget import MagnetismWidget
from sas.qtgui.Perspectives.Fitting.model import serializer
from sas.qtgui.Perspectives.Fitting.model.document import FitPageDocument
from sas.qtgui.Perspectives.Fitting.model.events import Origin
from sas.qtgui.Perspectives.Fitting.model.kernel import KernelBuilder
from sas.qtgui.Perspectives.Fitting.model.parameters import FitOptions, PageIdentity, Smearing, Table
from sas.qtgui.Perspectives.Fitting.model.serializer import format_number
from sas.qtgui.Perspectives.Fitting.ModelThread import Calc1D, Calc2D
from sas.qtgui.Perspectives.Fitting.MultiConstraint import MultiConstraint
from sas.qtgui.Perspectives.Fitting.OptionsWidget import OptionsWidget
from sas.qtgui.Perspectives.Fitting.OrderWidget import OrderWidget
from sas.qtgui.Perspectives.Fitting.PolydispersityWidget import PolydispersityWidget
from sas.qtgui.Perspectives.Fitting.ReportPageLogic import ReportPageLogic
from sas.qtgui.Perspectives.Fitting.services import constraints as constraint_service
from sas.qtgui.Perspectives.Fitting.SmearingWidget import SmearingWidget
from sas.qtgui.Perspectives.Fitting.UI.FittingWidgetUI import Ui_FittingWidgetUI
from sas.qtgui.Perspectives.Fitting.view.ParameterTableAdapter import ParameterTableAdapter
from sas.qtgui.Perspectives.Fitting.view.SettingsSync import SettingsSync
from sas.qtgui.Perspectives.Fitting.ViewDelegate import ModelViewDelegate
from sas.qtgui.Perspectives.UndoRedo import UndoStack
from sas.qtgui.Plotting.Plotter import PlotterWidget
from sas.qtgui.Plotting.PlotterData import Data1D, Data2D, DataRole
from sas.qtgui.Utilities.BackgroundColor import BG_DEFAULT, BG_ERROR
from sas.qtgui.Utilities.CategoryInstaller import CategoryInstaller
from sas.sascalc.fit import models
from sas.sascalc.fit.BumpsFitting import BumpsFit as Fit
from sas.system import HELP_SYSTEM

# CRUFT: remove when new release of sasmodels is available
# https://github.com/SasView/sasview/pull/181#discussion_r218135162
if not hasattr(SasviewModel, 'get_weights'):
    def get_weights(self: Any, name: str) -> tuple[np.ndarray, np.ndarray]:
        """
        Returns the polydispersity distribution for parameter *name* as *value* and *weight* arrays.
        """
        _, x, w = self._get_weights(self._model_info.parameters[name])
        return x, w

    SasviewModel.get_weights = get_weights

logger = logging.getLogger(__name__)

class FittingWidget(QtWidgets.QWidget, Ui_FittingWidgetUI):
    """
    Main widget for selecting form and structure factor models
    """
    constraintAddedSignal = QtCore.Signal(list, str)
    newModelSignal = QtCore.Signal()
    fittingFinishedSignal = QtCore.Signal(tuple)
    batchFittingFinishedSignal = QtCore.Signal(tuple)
    Calc1DFinishedSignal = QtCore.Signal(dict)
    Calc2DFinishedSignal = QtCore.Signal(dict)
    keyPressedSignal = QtCore.Signal(QtCore.QEvent)

    def __init__(self, parent: QtWidgets.QWidget | None = None, data: Any | None = None, tab_id: int = 1) -> None:

        super(FittingWidget, self).__init__()

        # Necessary globals
        self.parent  = parent
        self.process = None    # Default empty value

        # Which tab is this widget displayed in?
        self.tab_id = tab_id

        # Globals
        self.initializeGlobals()

        # The Qt-free page document. In Phase 2 it shadows the legacy stores (DocumentShadow).
        self.document = FitPageDocument(PageIdentity(page_id=tab_id, tab_id=tab_id))
        self.kernel_builder = KernelBuilder(self.models)
        self.shadow = DocumentShadow(self)
        # The intents (Phase 5); undo and redo replay document commands on the controller
        self.controller = FitPageController(self)
        self.undo_stack = UndoStack(self, target=self.controller, snapshot_fn=self.document.snapshot,
                                    restore_fn=lambda snapshot: self.controller.restore(snapshot, Origin.UNDO))

        # data index for the batch set
        self.data_index = 0
        # Main Data[12]D holders
        # Logics.data contains a single Data1D/Data2D object
        self._logic = [FittingLogic()]

        # Fitting controller for business logic
        self.fitting_controller = FittingController(self)

        # Shared state object for tab widgets
        self.fitting_state = FittingState(
            on_fit_ready_changed=lambda can_fit: self.cmdFit.setEnabled(can_fit)
        )

        # Main GUI setup up
        self.setupUi(self)
        self.setWindowTitle("Fitting")

        # Set up tabs widgets
        self.initializeWidgets()

        # Set up models and views
        self.initializeModels()

        # Defaults for the structure factors
        self.setDefaultStructureCombo()

        # Make structure factor and model CBs disabled
        self.disableModelCombo()
        self.disableStructureCombo()

        # Generate the category list for display
        self.initializeCategoryCombo()

        # Initial control state
        self.initializeControls()

        QtWidgets.QApplication.processEvents()

        # Connect signals to controls
        self.initializeSignals()

        if data is not None:
            self.dataFromItems(data)

        # New font to display angstrom symbol
        new_font = 'font-family: -apple-system, "Helvetica Neue", "Ubuntu";'
        self.label_17.setStyleSheet(new_font)
        self.label_19.setStyleSheet(new_font)

        # The document drives the kernel, then the tables, then the settings widgets
        self.kernel_sync = LegacyKernelSync(self)
        self.table_adapters = [ParameterTableAdapter(self, table) for table in Table]
        self.settings_sync = SettingsSync(self)
        # Every legacy writer from here on is mirrored into the document
        self.shadow.start()

    @property
    def logic(self) -> FittingLogic:
        # make sure the logic contains at least one element
        assert self._logic
        # logic connected to the currently shown data
        return self._logic[self.data_index]

    @property
    def data(self) -> Data1D | Data2D:
        return self.logic.data

    def dataFromItems(self, value: QtGui.QStandardItem | list[QtGui.QStandardItem]) -> None:
        """ data setter: the data is read back into the document, and the layout follows is2D """
        self._loadData(value)
        if not self.controller.relayout():
            # Same layout: the derived rules (e.g. SESANS: no background) reach the tables
            self.shadow.resync(set(self.document.parameters.keys()))
            self.onLayoutChanged()
            if len(self.document.parameters):
                self.updateData()
        # Reinitialize model list for constrained/simult fitting
        self.newModelSignal.emit()

    @mirrors('data', 'options', 'smearing', 'flags', 'parameters')
    def _loadData(self, value: QtGui.QStandardItem | list[QtGui.QStandardItem]) -> None:
        # Value is either a list of indices for batch fitting or a simple index
        # for standard fitting. Assure we have a list, regardless.
        if isinstance(value, list):
            self.is_batch_fitting = True
        else:
            value = [value]

        assert isinstance(value[0], QtGui.QStandardItem)

        if hasattr(self, "undo_stack"):
            self.undo_stack.clear()

        # Keep reference to all datasets for batch
        self.all_data = value

        # Create logics with data items
        # Logics.data contains only a single Data1D/Data2D object
        if len(value) == 1:
            # single data logic is already defined, update data on it
            self._logic[0].data = GuiUtils.dataFromItem(value[0])
        else:
            # batch datasets
            self._logic = []
            for data_item in value:
                logic = FittingLogic(data=GuiUtils.dataFromItem(data_item))
                self._logic.append(logic)
            # Option widget logic was destroyed - reestablish
            self.options_widget.logic = self._logic[0]
            # Ensure auxiliary widgets point at the new logic instance
            self.polydispersity_widget.logic = self._logic[0]
            self.magnetism_widget.logic = self._logic[0]
            # update the ordering tab
            self.order_widget.updateData(self.all_data)

        # Overwrite data type descriptor
        self.is2D = True if isinstance(self.logic.data, Data2D) else False

        # Let others know we're full of data now
        self.data_is_loaded = True

        # Update FittingState
        self.fitting_state.is2D = self.is2D
        self.fitting_state.is_batch_fitting = self.is_batch_fitting
        self.fitting_state.data_is_loaded = True

        # Reset the smearer
        self.smearing_widget.resetSmearer()
        if self.data.isSesans:
            self.onSesansData()

        # Enable/disable UI components
        self.setEnablementOnDataLoad()

    def initializeGlobals(self) -> None:
        """
        Initialize global variables used in this class
        """
        # SasModel is loaded
        self.model_is_loaded = False
        # Data[12]D passed and set
        self.data_is_loaded = False
        # Batch/single fitting
        self.is_batch_fitting = False
        self.is_chain_fitting = False
        # Is the fit job running?
        self.fit_started = False
        # The current fit thread
        self.calc_fit = None
        # Current SasModel view dimension
        self.is2D = False
        # Utility variable to enable unselectable option in category combobox
        self._previous_category_index = 0
        # The row of the shell-count combo box (the table adapter sets it)
        self._n_shells_row = -1
        # Dictionary of {model name: model class} for the current category
        self.models = {}
        # Dictionary of QModels
        self.model_dict = {}
        self.lst_dict = {}
        self.tabToList = {} # tab_id -> list widget
        self.tabToKey = {} # tab_id -> model key

        # Fit options
        self.q_range_min = OptionsWidget.QMIN_DEFAULT
        self.q_range_max = OptionsWidget.QMAX_DEFAULT
        self.npts = OptionsWidget.NPTS_DEFAULT
        self.log_points = True
        self.weighting = 0
        self.chi2 = None

        self.all_data = []
        # custom plugin models
        # {model.name:model}
        self.custom_models = self.customModels()
        # Page id for fitting
        # To keep with previous SasView values, use 200 as the start offset
        self.page_id = 200 + self.tab_id

        # Data for chosen model
        self.model_data = None
        self._previous_model_index = 0

        # Error column presence in parameter display
        self.has_error_column = False
        self.has_magnet_error_column = False

        # Enablement of comboboxes
        self.enabled_cbmodel = False
        self.enabled_sfmodel = False

        # If the widget generated theory item, save it
        self.theory_item = None

        # list column widths
        self.lstParamHeaderSizes = {}

        # Fitting just ran - don't recalculate chi2
        self.fitResults = False

        # Current parameters

        # signal communicator
        self.communicator = GuiUtils.communicator

    def initializeWidgets(self) -> None:
        """
        Initialize widgets for tabs
        """
        # Options widget
        layout = QtWidgets.QGridLayout()
        self.options_widget = OptionsWidget(self, self.logic)
        layout.addWidget(self.options_widget)
        self.tabOptions.setLayout(layout)
        self.options_widget.setLogScale(self.log_points)

        # Smearing widget
        layout = QtWidgets.QGridLayout()
        self.smearing_widget = SmearingWidget(self)
        layout.addWidget(self.smearing_widget)
        self.tabResolution.setLayout(layout)

        # Polydispersity widget
        layout = QtWidgets.QGridLayout()
        self.polydispersity_widget = PolydispersityWidget(parent=self)
        layout.addWidget(self.polydispersity_widget)
        self.tabPolydispersity.setLayout(layout)
        self.lstPoly = self.polydispersity_widget.lstPoly

        # magnetism widget
        layout = QtWidgets.QGridLayout()
        self.magnetism_widget = MagnetismWidget(parent=self)
        layout.addWidget(self.magnetism_widget)
        self.tabMagnetism.setLayout(layout)
        self.lstMagnetic = self.magnetism_widget.lstMagnetic

        # Order widget
        layout = QtWidgets.QGridLayout()
        # pass all data items to access multiple datasets
        self.order_widget = OrderWidget(self, self.all_data)
        layout.addWidget(self.order_widget)
        self.tabOrder.setLayout(layout)

        # Define bold font for use in various controls
        self.boldFont = QtGui.QFont()
        self.boldFont.setBold(True)

        # Set data label
        self.label.setFont(self.boldFont)
        self.label.setText("No data loaded")
        self.lblFilename.setText("")

    def initializeModels(self) -> None:
        """
        Set up models and views
        """
        # Set the main models
        # We can't use a single model here, due to restrictions on flattening
        # the model tree with subclassed QAbstractProxyModel...
        self._model_model = FittingUtilities.ToolTippedItemModel()

        self.model_dict["standard"] = self._model_model
        self.model_dict["poly"] = self.polydispersity_widget.poly_model
        self.model_dict["magnet"] = self.magnetism_widget._magnet_model

        self.lst_dict["standard"] = self.lstParams
        self.lst_dict["poly"] = self.lstPoly
        self.lst_dict["magnet"] = self.lstMagnetic

        self.tabToList[0] = self.lstParams
        self.tabToList[3] = self.polydispersity_widget.lstPoly
        self.tabToList[4] = self.magnetism_widget.lstMagnetic

        self.tabToKey[0] = "standard"
        self.tabToKey[3] = "poly"
        self.tabToKey[4] = "magnet"

        # Param model displayed in param list
        self.lstParams.setModel(self._model_model)
        self.readCategoryInfo()

        # Delegates for custom editing and display
        self.lstParams.setItemDelegate(ModelViewDelegate(self))

        self.lstParams.setAlternatingRowColors(True)
        stylesheet = """

            QTreeView {
                paint-alternating-row-colors-for-empty-area:0;
            }

            QTreeView::item {
                border: 1px;
                padding: 2px 1px;
            }

            QTreeView::item:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #e7effd, stop: 1 #cbdaf1);
                border: 1px solid #bfcde4;
            }

            QTreeView::item:selected {
                border: 1px solid #567dbc;
            }

            QTreeView::item:selected:active{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #6ea1f1, stop: 1 #567dbc);
            }

            QTreeView::item:selected:!active {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #6b9be8, stop: 1 #577fbf);
            }
           """
        self.lstParams.setStyleSheet(stylesheet)
        self.lstParams.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.lstParams.customContextMenuRequested.connect(self.showModelContextMenu)
        self.lstParams.setAttribute(QtCore.Qt.WA_MacShowFocusRect, False)
        # Column resize signals
        self.lstParams.header().sectionResized.connect(self.onColumnWidthUpdate)

        # The poly and magnet tables are built from the document (ParameterTableAdapter)
        self.lstPoly.customContextMenuRequested.connect(self.showModelContextMenu)
        self.lstMagnetic.customContextMenuRequested.connect(self.showModelContextMenu)

        # Initial status of the ordering tab - invisible
        self.tabFitting.removeTab(TAB_ORDERING)

    def initializeCategoryCombo(self) -> None:
        """
        Model category combo setup
        """
        category_list = sorted(self.master_category_dict)
        self.cbCategory.addItem(CATEGORY_DEFAULT)
        self.cbCategory.addItems(category_list)
        if CATEGORY_STRUCTURE not in category_list:
            self.cbCategory.addItem(CATEGORY_STRUCTURE)
        self.cbCategory.setCurrentIndex(0)

    def setEnablementOnDataLoad(self) -> None:
        """
        Enable/disable various UI elements based on data loaded
        """
        # Suppress undo capture: data loading is a programmatic operation,
        # not a user-initiated parameter change.  Without this, updateQRange
        # and onWeightingChoice push spurious FitOptionsCommand entries.
        with self.undo_stack.suppressed():
            # Tag along functionality
            self.label.setText("Data loaded from: ")
            if self.logic.data.name:
                self.lblFilename.setText(self.logic.data.name)
            else:
                self.lblFilename.setText(self.logic.data.filename)
            self.updateQRange()
            # Switch off Data2D control
            self.chk2DView.setEnabled(False)
            self.chk2DView.setVisible(False)
            self.chkMagnetism.setEnabled(self.canHaveMagnetism())
            self.tabFitting.setTabEnabled(TAB_MAGNETISM, self.chkMagnetism.isChecked())
            # Combo box or label for file name"
            if self.is_batch_fitting:
                self.lblFilename.setVisible(False)
                for dataitem in self.all_data:
                    name = GuiUtils.dataFromItem(dataitem).name
                    self.cbFileNames.addItem(name)
                self.cbFileNames.setVisible(True)
                self.chkChainFit.setEnabled(True)
                self.chkChainFit.setVisible(True)
                # This panel is not designed to view individual fits, so disable plotting
                self.cmdPlot.setVisible(False)
            # Similarly on other tabs
            self.options_widget.setEnablementOnDataLoad()
            # Smearing tab
            self.smearing_widget.updateData(self.data)
            # Check if a model was already loaded when data is sent to the tab
            self.cmdFit.setEnabled(self.haveParamsToFit())

    def acceptsData(self) -> bool:
        """ Tells the caller this widget can accept new dataset """
        return not self.data_is_loaded

    def disableModelCombo(self) -> None:
        """ Disable the combobox """
        self.cbModel.setEnabled(False)
        self.lblModel.setEnabled(False)
        self.enabled_cbmodel = False

    def enableModelCombo(self) -> None:
        """ Enable the combobox """
        self.cbModel.setEnabled(True)
        self.lblModel.setEnabled(True)
        self.enabled_cbmodel = True

    def disableStructureCombo(self) -> None:
        """ Disable the combobox """
        self.cbStructureFactor.setEnabled(False)
        self.lblStructure.setEnabled(False)
        self.enabled_sfmodel = False

    def enableStructureCombo(self) -> None:
        """ Enable the combobox """
        self.cbStructureFactor.setEnabled(True)
        self.lblStructure.setEnabled(True)
        self.enabled_sfmodel = True

    def togglePoly(self, isChecked: bool) -> None:
        """ The polydispersity checkbox: an intent """
        self.controller.set_flag("polydispersity", isChecked)

    def applyPolydispersity(self, isChecked: bool) -> None:
        """ Enable/disable the polydispersity tab (SettingsSync) """
        self.tabFitting.setTabEnabled(TAB_POLY, isChecked)
        # Check if any parameters are ready for fitting
        self.cmdFit.setEnabled(self.haveParamsToFit())
        self.polydispersity_widget.togglePoly(isChecked)
        self.updateData()

    def onPolyToggled(self, isChecked: bool) -> None:
        """
        Handle polydispersity toggle signal from PolydispersityWidget.

        Updates FittingState and tab enablement.
        """
        self.fitting_state.poly_enabled = isChecked
        self.tabFitting.setTabEnabled(TAB_POLY, isChecked)
        self.cmdFit.setEnabled(self.haveParamsToFit())

    def toggleMagnetism(self, isChecked: bool) -> None:
        """ The magnetism checkbox: an intent """
        self.controller.set_flag("magnetism", isChecked)

    def applyMagnetism(self, isChecked: bool) -> None:
        """ Enable/disable the magnetism tab (SettingsSync) """
        self.tabFitting.setTabEnabled(TAB_MAGNETISM, isChecked)
        # Check if any parameters are ready for fitting
        self.cmdFit.setEnabled(self.haveParamsToFit())
        self.magnetism_widget.isActive = isChecked

    def onMagnetismToggled(self, isChecked: bool) -> None:
        """
        Handle magnetism toggle signal from MagnetismWidget.

        Updates FittingState and tab enablement.
        """
        self.fitting_state.magnetism_enabled = isChecked
        self.tabFitting.setTabEnabled(TAB_MAGNETISM, isChecked)
        self.cmdFit.setEnabled(self.haveParamsToFit())

    def toggleChainFit(self, isChecked: bool) -> None:
        """ The chain-fit checkbox: an intent """
        self.controller.set_flag("chain_fit", isChecked)

    def applyChainFit(self, isChecked: bool) -> None:
        """ Enable/disable chain fitting (SettingsSync) """
        self.is_chain_fitting = isChecked
        # show/hide the ordering tab
        if isChecked:
            self.tabFitting.insertTab(TAB_ORDERING, self.tabOrder, "Order")
        else:
            self.tabFitting.removeTab(TAB_ORDERING)

    def toggle2D(self, isChecked: bool) -> None:
        """ The 2D-view checkbox (no data loaded): a layout change """
        self.controller.set_view_2d(isChecked)

    def showSelection(self, selection, view_2d: bool) -> None:
        """The combo boxes and the 2D checkbox show the document's selection (SettingsSync)."""
        widgets = (self.cbCategory, self.cbModel, self.cbStructureFactor, self.chk2DView)
        for widget in widgets:
            widget.blockSignals(True)
        try:
            if selection.category and self.cbCategory.currentText() != selection.category:
                self.cbCategory.setCurrentIndex(self.cbCategory.findText(selection.category))
                self._previous_category_index = self.cbCategory.currentIndex()
                self._populateCategory(selection.category)
            if selection.category != CATEGORY_STRUCTURE:
                index = self.cbModel.findText(selection.model or MODEL_DEFAULT)
                if index >= 0:
                    self.cbModel.setCurrentIndex(index)
                    self._previous_model_index = index
            self.cbStructureFactor.setCurrentIndex(
                max(self.cbStructureFactor.findText(selection.structure or STRUCTURE_DEFAULT), 0))
            self.chk2DView.setChecked(view_2d)
        finally:
            for widget in widgets:
                widget.blockSignals(False)

    def onLayoutChanged(self) -> None:
        """What depends on the layout, after it changed (SettingsSync) or after a data load."""
        doc = self.document
        params = doc.parameters
        self.is2D = doc.is2D()
        self.polydispersity_widget.is2D = self.is2D
        self.model_is_loaded = len(params) > 0
        self.cmdPlot.setEnabled(self.model_is_loaded)
        self.chkMagnetism.setEnabled(doc.can_have_magnetism())
        self.tabFitting.setTabEnabled(TAB_MAGNETISM, self.chkMagnetism.isChecked() and doc.can_have_magnetism())
        self.chkPolydispersity.setEnabled(bool(params.by_table(Table.POLY)))
        if doc.selection.category != CATEGORY_STRUCTURE and doc.selection.model not in ("", MODEL_DEFAULT):
            # The structure factor goes with form factors; a combo showing "None" stays as it is
            # (enableStructureFactorControl)
            if params.capabilities.structure_factor:
                self.enableStructureCombo()
            elif doc.selection.structure or not self.cbStructureFactor.isEnabled():
                self.disableStructureCombo()
        for column, width in self.lstParamHeaderSizes.items():
            self.lstParams.setColumnWidth(column, width)
        self.lstParams.header().setFont(self.boldFont)
        self.smearing_widget.updateKernelModel(kernel_model=self.logic.kernel_module)
        self.newModelSignal.emit()

    def _populateCategory(self, category: str) -> None:
        """The model combo box (or the structure-factor one) for *category*."""
        if category == CATEGORY_STRUCTURE:
            self.disableModelCombo()
            self.enableStructureCombo()
            return
        self.cbModel.blockSignals(True)
        self.cbModel.clear()
        self.cbModel.addItem(MODEL_DEFAULT)
        model_list = self.master_category_dict[category]
        self.cbModel.addItems(sorted(m[0] for m in model_list if m[0] not in SUPPRESSED_MODELS and m[1]))
        self.cbModel.blockSignals(False)
        self.enableModelCombo()
        self.disableStructureCombo()

    def otherSymbols(self) -> set[str]:
        """The constraint symbols of the other fit pages (retention keeps constraints that resolve)."""
        if self.parent is None:
            return set()
        return {symbol for tab in self.parent.perspective().getFitTabs() if tab is not self
                for symbol in tab.document.symbol_table()}

    def keyAt(self, row: int, model_key: str = "standard") -> str | None:
        """The document key of the parameter in *row* of the table *model_key*."""
        return self.table_adapters[list(self.model_dict).index(model_key)].key_at(row)

    @classmethod
    def customModels(cls) -> dict[str, Any]:
        """ Reads in file names in the custom plugin directory """
        manager = models.ModelManager()
        # TODO: Cache plugin models instead of scanning the directory each time.
        manager.update()
        # TODO: Define plugin_models property in ModelManager.
        return manager.base.plugin_models

    def initializeControls(self) -> None:
        """
        Set initial control enablement
        """
        self.cbFileNames.setVisible(False)
        self.cmdFit.setEnabled(False)
        self.cmdPlot.setEnabled(False)
        self.chkPolydispersity.setEnabled(False)
        self.chkPolydispersity.setChecked(False)
        self.chk2DView.setEnabled(True)
        self.chk2DView.setChecked(False)
        self.chkMagnetism.setEnabled(False)
        self.chkMagnetism.setChecked(False)
        self.chkChainFit.setEnabled(False)
        self.chkChainFit.setVisible(False)
        # Tabs
        self.tabFitting.setTabEnabled(TAB_POLY, False)
        self.tabFitting.setTabEnabled(TAB_MAGNETISM, False)
        self.lblChi2Value.setText("---")
        # Smearing tab
        self.smearing_widget.updateData(self.data)
        # Line edits in the option tab
        self.updateQRange()

    def initializeSignals(self) -> None:
        """
        Connect GUI element signals
        """
        # Comboboxes
        self.cbStructureFactor.currentIndexChanged.connect(self.onSelectStructureFactor)
        self.cbCategory.currentIndexChanged.connect(self.onSelectCategory)
        self.cbModel.currentIndexChanged.connect(self.onSelectModel)
        self.cbFileNames.currentIndexChanged.connect(self.onSelectBatchFilename)
        # Checkboxes
        self.chk2DView.toggled.connect(self.toggle2D)
        self.chkPolydispersity.toggled.connect(self.togglePoly)
        self.chkMagnetism.toggled.connect(self.toggleMagnetism)
        self.chkChainFit.toggled.connect(self.toggleChainFit)
        # Buttons
        self.cmdFit.clicked.connect(self.onFit)
        self.cmdPlot.clicked.connect(self.onPlot)
        self.cmdHelp.clicked.connect(self.onHelp)

        # Respond to change in parameters from the UI (the table adapters forward the edits)
        self.lstParams.selectionModel().selectionChanged.connect(self.onSelectionChanged)
        self.lstParams.installEventFilter(self)

        # Local signals
        self.batchFittingFinishedSignal.connect(self.batchFitComplete)
        self.fittingFinishedSignal.connect(self.fitComplete)
        self.Calc1DFinishedSignal.connect(self.complete1D)
        self.Calc2DFinishedSignal.connect(self.complete2D)

        # Signals from separate tabs asking for replot
        self.options_widget.plot_signal.connect(self.onOptionsUpdate)
        self.options_widget.txtMinRange.editingFinished.connect(self.options_widget.updateMinQ)
        self.options_widget.txtMaxRange.editingFinished.connect(self.options_widget.updateMaxQ)

        # Signals from other widgets
        self.communicator.customModelDirectoryChanged.connect(self.onCustomModelChange)
        self.smearing_widget.smearingChangedSignal.connect(self.onSmearingOptionsUpdate)
        self.polydispersity_widget.updateDataSignal.connect(lambda: self.updateData())
        self.polydispersity_widget.deletePlotSignal.connect(self.setPlotDeletable)
        self.polydispersity_widget.toggledSignal.connect(self.onPolyToggled)
        self.magnetism_widget.updateDataSignal.connect(lambda: self.updateData())
        self.magnetism_widget.toggledSignal.connect(self.onMagnetismToggled)

        # Communicator signal
        self.communicator.updateModelCategoriesSignal.connect(self.onCategoriesChanged)
        self.communicator.updateMaskedDataSignal.connect(self.onMaskedData)

        # Catch all key press events
        self.keyPressedSignal.connect(self.onKey)

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        super(FittingWidget, self).keyPressEvent(event)
        self.keyPressedSignal.emit(event)

    def eventFilter(self, obj: QtCore.QObject, event: QtCore.QEvent) -> bool:
        # Catch enter key presses when editing model params
        if obj in [self.lstParams, self.polydispersity_widget.lstPoly, self.magnetism_widget.lstMagnetic]:
            if event.type() == QtCore.QEvent.KeyPress and event.key() in [QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter]:
                self.onKey(event)
                return True
        return False

    def modelName(self) -> str:
        """
        Returns model name, by default M<tab#>, e.g. M1, M2
        """
        return f"M{self.tab_id}"

    def nameForFittedData(self, name: str) -> str:
        """
        Generate name for the current fit
        """
        if self.is2D:
            name += "2d"
        name = f"{self.modelName()} [{name}]"
        return name

    def showModelContextMenu(self, position: QtCore.QPoint) -> None:
        """
        Show context specific menu in the parameter table.
        When clicked on parameter(s): fitting/constraints options
        When clicked on white space: model description
        """
        # See which model we're dealing with by looking at the tab id
        current_list = self.tabToList[self.tabFitting.currentIndex()]
        model_key = self.tabToKey[self.tabFitting.currentIndex()]
        rows = [s.row() for s in current_list.selectionModel().selectedRows()
                if self.isCheckable(s.row(), model_key=model_key)]

        menu = self.showModelDescription() if not rows else self.modelContextMenu(rows)
        try:
            menu.exec_(current_list.viewport().mapToGlobal(position))
        except AttributeError as ex:
            logger.error("Error generating context menu: %s" % ex)
        return

    def modelContextMenu(self, rows: list[int]) -> QtWidgets.QMenu:
        """
        Create context menu for the parameter selection
        """
        menu = QtWidgets.QMenu()
        num_rows = len(rows)
        if num_rows < 1:
            return menu
        current_list = self.tabToList[self.tabFitting.currentIndex()]
        model_key = self.tabToKey[self.tabFitting.currentIndex()]
        # Select for fitting
        param_string = "parameter " if num_rows == 1 else "parameters "
        to_string = "to its current value" if num_rows == 1 else "to their current values"
        has_constraints = any([self.rowHasConstraint(i, model_key=model_key) for i in rows])
        has_real_constraints = any([self.rowHasActiveConstraint(i, model_key=model_key) for i in rows])

        self.actionSelect = QtGui.QAction(self)
        self.actionSelect.setObjectName("actionSelect")
        self.actionSelect.setText(QtCore.QCoreApplication.translate("self", "Select "+param_string+" for fitting"))
        # Unselect from fitting
        self.actionDeselect = QtGui.QAction(self)
        self.actionDeselect.setObjectName("actionDeselect")
        self.actionDeselect.setText(QtCore.QCoreApplication.translate("self", "De-select "+param_string+" from fitting"))

        self.actionConstrain = QtGui.QAction(self)
        self.actionConstrain.setObjectName("actionConstrain")
        self.actionConstrain.setText(QtCore.QCoreApplication.translate("self", "Constrain "+param_string + to_string))

        self.actionRemoveConstraint = QtGui.QAction(self)
        self.actionRemoveConstraint.setObjectName("actionRemoveConstrain")
        self.actionRemoveConstraint.setText(QtCore.QCoreApplication.translate("self", "Remove constraint"))

        self.actionEditConstraint = QtGui.QAction(self)
        self.actionEditConstraint.setObjectName("actionEditConstrain")
        self.actionEditConstraint.setText(QtCore.QCoreApplication.translate("self", "Edit constraint"))

        self.actionMultiConstrain = QtGui.QAction(self)
        self.actionMultiConstrain.setObjectName("actionMultiConstrain")
        self.actionMultiConstrain.setText(QtCore.QCoreApplication.translate("self", "Constrain selected parameters to their current values"))

        self.actionMutualMultiConstrain = QtGui.QAction(self)
        self.actionMutualMultiConstrain.setObjectName("actionMutualMultiConstrain")
        self.actionMutualMultiConstrain.setText(QtCore.QCoreApplication.translate("self", "Mutual constrain of selected parameters..."))

        menu.addAction(self.actionSelect)
        menu.addAction(self.actionDeselect)
        menu.addSeparator()

        if has_constraints:
            menu.addAction(self.actionRemoveConstraint)
            if num_rows == 1 and has_real_constraints:
                menu.addAction(self.actionEditConstraint)
        else:
            if num_rows == 2:
                menu.addAction(self.actionMutualMultiConstrain)
            else:
                menu.addAction(self.actionConstrain)

        # Define the callbacks
        self.actionConstrain.triggered.connect(self.addSimpleConstraint)
        self.actionRemoveConstraint.triggered.connect(self.deleteConstraint)
        self.actionEditConstraint.triggered.connect(self.editConstraint)
        self.actionMutualMultiConstrain.triggered.connect(lambda: self.showMultiConstraint(current_list=current_list))
        self.actionSelect.triggered.connect(self.selectParameters)
        self.actionDeselect.triggered.connect(self.deselectParameters)
        return menu

    def showMultiConstraint(self, current_list: QtWidgets.QTreeView | None = None) -> None:
        """
        Show the constraint widget for two selected parameters and add the constraint it returns.
        """
        current_list = self.lstParams if current_list is None else current_list
        model_key = next((key for key, view in self.lst_dict.items() if view is current_list), "standard")
        selected_rows = current_list.selectionModel().selectedRows()
        # There have to be only two rows selected. The caller takes care of that.
        assert len(selected_rows) == 2
        params_list = [s.data() for s in selected_rows]
        mc_widget = MultiConstraint(self, params=params_list)
        if not np.any([FittingUtilities.isParamPolydisperse(p, self.logic.model_parameters, is2D=self.is2D)
                       for p in params_list]):
            # no parameters are pd - do not show the warning
            mc_widget.lblWarning.setText("")
        if mc_widget.exec_() != QtWidgets.QDialog.Accepted:
            return
        mnemonic = self.document.identity.mnemonic
        param_used = mc_widget.params[1]
        constraint = Constraint(param=mc_widget.params[0], value=param_used,
                                func=mc_widget.txtConstraint.text().replace(param_used, f"{mnemonic}.{param_used}"),
                                value_ex=f"{mnemonic}.{param_used}")
        constraint.validate = mc_widget.validate
        self.addConstraintToRow(constraint=constraint, row=self.getRowFromName(constraint.param), model_key=model_key)

    def getModelKeyFromName(self, name: str) -> str:
        """
        The table ('standard', 'poly' or 'magnet') of the parameter shown as *name*
        """
        key = constraint_service.key_for(self.document, name)
        if key is None:
            return "standard"
        table = self.document.parameters[key].table
        return next(model_key for model_key, t in constraint_service.TABLES.items() if t is table)

    def getRowFromName(self, name: str) -> int | None:
        """
        The row of the parameter shown as *name*, in its table
        """
        key = constraint_service.key_for(self.document, name)
        if key is None:
            return None
        return (self._adapter(self.getModelKeyFromName(name)).rows() or {}).get(key)

    def _adapter(self, model_key: str):
        return self.table_adapters[list(constraint_service.TABLES).index(model_key)]

    def getParamNames(self) -> list[str]:
        """
        The fittable main parameters, and the poly widths while polydispersity is on
        """
        return self.getParamNamesMain() + self.getParamNamesPoly()

    def getParamNamesPoly(self) -> list[str]:
        if not self.document.flags.polydispersity:
            return []
        return [p.key for p in self.document.parameters.by_table(Table.POLY)]

    def paramsToFit(self) -> list[str]:
        """The main (by label) and poly parameters selected for fitting (the constraint dialogs)."""
        params = self.document.parameters
        return [params.legacy_key(p.key) for t in (Table.MAIN, Table.POLY) for p in params.by_table(t)
                if p.fit and p.fittable]

    def getParamNamesMain(self) -> list[str]:
        """
        The labels of the fittable main parameters
        """
        return [p.label for p in self.document.parameters.by_table(Table.MAIN) if p.fittable]

    def getParamNamesMagnet(self) -> list[str]:
        """
        The magnetic parameters, while magnetism is on
        """
        if not self.chkMagnetism.isChecked():
            return []
        return [p.key for p in self.document.parameters.by_table(Table.MAGNET) if p.fittable]

    def getModelKey(self, constraint: Constraint) -> str | None:
        """
        The table of the parameter a constraint is on, or None if this page has no such parameter
        """
        if constraint_service.key_for(self.document, constraint.param) is None:
            return None
        return self.getModelKeyFromName(constraint.param)

    def addConstraintToRow(self, constraint: Constraint | None = None, row: int = 0, model_key: str = "standard") -> None:
        """
        Add the constraint object to the requested row, after checking it against every page's symbols.
        An inconsistent constraint is reported and not added.
        """
        assert isinstance(constraint, Constraint)
        key = self.keyAt(row, model_key)
        assert key is not None and self.document.parameters[key].fittable
        if model_key == 'poly' and 'Distribution' in constraint.param:
            constraint.param = self.polydispersity_widget.polyNameToParam(constraint.param)
        perspective = self.parent.perspective()
        constraint_list = perspective.getActiveConstraintList()
        constraint_list.append((f"{self.document.identity.mnemonic}.{constraint.param}", constraint.func))
        errors = FittingUtilities.checkConstraints(perspective.getSymbolDictForConstraints(), constraint_list)
        constraint_tab = perspective.getConstraintTab()
        if errors:
            QtWidgets.QMessageBox.critical(self, "Inconsistent constraint", errors, QtWidgets.QMessageBox.Ok)
            if constraint_tab:
                # inform the constraint tab that the constraint was not accepted
                constraint_tab.constraint_accepted = False
            return
        # The constrained parameter is fitted (it is computed from the others while fitting)
        self.controller.set_constraint(key, constraint, fit=True)
        self.constraintAddedSignal.emit([row], model_key)
        self.communicator.statusBarUpdateSignal.emit('Constraint added')
        if constraint_tab:
            constraint_tab.constraint_accepted = True

    def addSimpleConstraint(self) -> None:
        """
        Fix each selected parameter to its current value: an inactive constraint that keeps the
        bounds to restore, and bounds narrowed around the value (bumps needs a range).
        """
        model_key = self.tabToKey[self.tabFitting.currentIndex()]
        params = self.document.parameters
        for row in self.selectedParameters(model_key=model_key):
            key = self.keyAt(row, model_key)
            p = params[key]
            constraint = Constraint(param=params.legacy_key(key), value=format_number(p.value),
                                    min=format_number(p.min), max=format_number(p.max))
            constraint.active = False
            self.controller.set_constraint(key, constraint, min=p.value - p.value / 10000.0,
                                           max=p.value + p.value / 10000.0)
            self.constraintAddedSignal.emit([row], model_key)
        self.communicator.statusBarUpdateSignal.emit('Constraint added')

    def editConstraint(self) -> None:
        """
        Edit the constraint of the selected parameter.
        """
        current_list = self.tabToList[self.tabFitting.currentIndex()]
        model_key = self.tabToKey[self.tabFitting.currentIndex()]
        params_list = [s.data() for s in current_list.selectionModel().selectedRows()
                       if self.isCheckable(s.row(), model_key=model_key)]
        assert len(params_list) == 1
        row = current_list.selectionModel().selectedRows()[0].row()
        mc_widget = MultiConstraint(self, params=params_list, constraint=self.getConstraintForRow(row, model_key))
        if not np.any([FittingUtilities.isParamPolydisperse(p, self.logic.model_parameters, is2D=self.is2D)
                       for p in params_list]):
            mc_widget.lblWarning.setText("")
        if mc_widget.exec_() != QtWidgets.QDialog.Accepted:
            return
        param_used = mc_widget.params[1]
        constraint = Constraint(param=mc_widget.params[0], value=param_used, func=mc_widget.txtConstraint.text(),
                                value_ex=f"{self.document.identity.mnemonic}.{param_used}")
        constraint.validate = mc_widget.validate
        if model_key == 'poly' and 'Distribution' in constraint.param:
            constraint.param = self.polydispersity_widget.polyNameToParam(constraint.param)
        self.addConstraintToRow(constraint=constraint, row=self.getRowFromName(constraint.param), model_key=model_key)

    def deleteConstraint(self) -> None:
        """
        Delete the constraints of the selected parameters.
        """
        current_list = self.tabToList[self.tabFitting.currentIndex()]
        model_key = self.tabToKey[self.tabFitting.currentIndex()]
        for index in current_list.selectionModel().selectedRows():
            if self.isCheckable(index.row(), model_key=model_key):
                param = index.data()
                if model_key == 'poly':
                    param = self.polydispersity_widget.polyNameToParam(param)
                self.deleteConstraintOnParameter(param=param, model_key=model_key)

    def deleteConstraintOnParameter(self, param: str | None = None, model_key: str = "standard") -> None:
        """
        Delete the constraint on *param* (every constraint of the table if None), restoring
        the bounds a simple constraint kept.
        """
        rows = self._adapter(model_key).rows() or {}
        for key, row in rows.items():
            constraint = self.document.parameters[key].constraint
            if constraint is None or (param and constraint.param != param):
                continue
            bounds = {b: FittingUtilities.parse_number(getattr(constraint, b)) for b in ("min", "max")}
            self.controller.set_constraint(key, None, **{b: v for b, v in bounds.items() if v is not None})
            self.constraintAddedSignal.emit([row], model_key)
        self.communicator.statusBarUpdateSignal.emit('Constraint removed')

    def setConstraintActive(self, param: str, active: bool) -> None:
        """Activate or deactivate the constraint on *param* (the constraint tab)."""
        key = constraint_service.key_for(self.document, param)
        if key is not None:
            self.controller.set_constraint_active(key, active)

    def getConstraintForRow(self, row: int, model_key: str = "standard") -> Constraint | None:
        """
        The constraint of the parameter in *row*, if any
        """
        key = self.keyAt(row, model_key)
        if key is None or not self.document.parameters[key].fittable:
            return None
        return self.document.parameters[key].constraint

    def allParamNames(self) -> list[str]:
        """
        Returns a list of all parameter names defined on the current model
        """
        all_params = self.logic.kernel_module._model_info.parameters.kernel_parameters
        all_params = list(self.logic.kernel_module.details)

        # all_param_names = [param.name for param in all_params]
        # Assure scale and background are always included
        # if 'scale' not in all_param_names:
        #    all_param_names.append('scale')
        # if 'background' not in all_param_names:
        #    all_param_names.append('background')
        return all_params

    def paramHasConstraint(self, param: str | None = None) -> bool:
        """
        Whether the parameter *param* has a constraint
        """
        key = None if param is None else constraint_service.key_for(self.document, param)
        return key is not None and self.document.parameters[key].constraint is not None

    def rowHasConstraint(self, row: int, model_key: str = "standard") -> bool:
        return self.getConstraintForRow(row, model_key) is not None

    def rowHasActiveConstraint(self, row: int, model_key: str = "standard") -> bool:
        constraint = self.getConstraintForRow(row, model_key)
        return constraint is not None and constraint.active

    def rowHasActiveComplexConstraint(self, row: int, model_key: str = "standard") -> bool:
        constraint = self.getConstraintForRow(row, model_key)
        return constraint is not None and constraint.active and bool(constraint.func)

    def selectParameters(self) -> None:
        """
        Selected parameter is chosen for fitting
        """
        status = QtCore.Qt.Checked
        model_key = self.tabToKey[self.tabFitting.currentIndex()]
        model = self.model_dict[model_key]
        current_list = self.lst_dict[model_key]
        item = model.itemFromIndex(current_list.currentIndex())
        self.setParameterSelection(status, item=item, model_key=model_key)

    def deselectParameters(self) -> None:
        """
        Selected parameters are removed for fitting
        """
        status = QtCore.Qt.Unchecked
        model_key = self.tabToKey[self.tabFitting.currentIndex()]
        model = self.model_dict[model_key]
        current_list = self.lst_dict[model_key]
        item = model.itemFromIndex(current_list.currentIndex())
        self.setParameterSelection(status, item=item, model_key=model_key)

    def selectedParameters(self, model_key: str = "standard") -> list[int]:
        """ Returns list of selected (highlighted) parameters """
        return [s.row() for s in self.lst_dict[model_key].selectionModel().selectedRows()
                if self.isCheckable(s.row(), model_key=model_key)]

    def setParameterSelection(self, status: QtCore.Qt.CheckState = QtCore.Qt.Unchecked, item: QtGui.QStandardItem | None = None, model_key: str = "standard") -> None:
        """
        Selected parameters are chosen for fitting
        """
        # Convert to proper indices and set requested enablement
        if item is None:
            return
        # We only want to select/deselect all items if
        # `item` is also selected!
        # Otherwise things get confusing.
        # https://github.com/SasView/sasview/issues/1676
        if item.row() not in self.selectedParameters(model_key=model_key):
            return
        for row in self.selectedParameters(model_key=model_key):
            self.model_dict[model_key].item(row, 0).setCheckState(status)

    def getConstraintsForAllModels(self) -> list[tuple[str, str]]:
        """
        (constrained parameter, expression) of the active constraints, e.g. [('sld','5*sld_solvent')]
        """
        return constraint_service.active(self.document)

    def getComplexConstraintsForAllModels(self) -> list[tuple[str, str]]:
        """
        (key, expression) of the active constraints that have an expression
        """
        return constraint_service.complex_constraints(self.document)

    def getComplexConstraintsForModel(self, model_key: str) -> list[tuple[str, str]]:
        """
        (key, expression) of the active constraints with an expression of one table, e.g. [('sld','5*M2.sld_solvent')]
        """
        return constraint_service.complex_constraints(self.document, constraint_service.TABLES[model_key])

    def getFullConstraintNameListForModel(self, model_key: str) -> list[tuple[str, str]]:
        """
        (constrained parameter, expression) of every constraint of one table, active or not
        """
        return constraint_service.full_names(self.document, constraint_service.TABLES[model_key])

    def getConstraintObjectsForAllModels(self) -> list[Constraint]:
        """
        Copies of the page's constraints (the constraint tab changes them through the page)
        """
        return [copy.deepcopy(p.constraint) for p in self.document.constrained()]

    def getConstraintObjectsForModel(self, model_key: str) -> list[Constraint]:
        """
        Copies of the constraints of one table
        """
        return [copy.deepcopy(p.constraint) for p in self.document.constrained(constraint_service.TABLES[model_key])]

    def getConstraintsForFitting(self) -> list[tuple[str, str]]:
        """
        The constraints of a single-page fit. Constraints that refer to other pages are
        deactivated if the user agrees; otherwise the fit is cancelled (ValueError).
        """
        constraints = self.getComplexConstraintsForAllModels()
        multi_constraints = [cons for cons in constraints if self.isConstraintMultimodel(cons[1])]
        if not multi_constraints:
            return constraints
        msg = "The current fit contains constraints relying on other fit pages.\n"
        msg += "Parameters with those constraints are:\n" + '\n'.join([cons[0] for cons in multi_constraints])
        msg += "\n\nWould you like to deactivate these constraints or cancel fitting?"
        msgbox = QtWidgets.QMessageBox(self)
        msgbox.setIcon(QtWidgets.QMessageBox.Warning)
        msgbox.setText(msg)
        msgbox.setWindowTitle("Existing Constraints")
        msgbox.addButton(QtWidgets.QPushButton("Deactivate"), QtWidgets.QMessageBox.YesRole)
        msgbox.addButton(QtWidgets.QPushButton("Cancel"), QtWidgets.QMessageBox.RejectRole)
        if msgbox.exec_() == QtWidgets.QMessageBox.RejectRole:
            raise ValueError("Fitting cancelled")
        constraint_tab = self.parent.perspective().getConstraintTab()
        for key, _ in multi_constraints:
            self.controller.set_constraint_active(key, False)
            if constraint_tab:
                legacy_key = self.document.parameters.legacy_key(key)
                constraint_tab.uncheckConstraint(f"{self.document.identity.mnemonic}:{legacy_key}")
        return self.getComplexConstraintsForAllModels()

    def showModelDescription(self) -> QtWidgets.QMenu:
        """
        Creates a window with model description, when right-clicked in the treeview
        """
        msg = 'Model description:\n'
        if self.logic.kernel_module is not None:
            if str(self.logic.kernel_module.description).rstrip().lstrip() == '':
                msg += "Sorry, no information is available for this model."
            else:
                msg += self.logic.kernel_module.description + '\n'
        else:
            msg += "You must select a model to get information on this"

        menu = QtWidgets.QMenu()
        label = QtWidgets.QLabel(msg)
        action = QtWidgets.QWidgetAction(self)
        action.setDefaultWidget(label)
        menu.addAction(action)
        return menu

    def canHaveMagnetism(self) -> bool:
        """
        Checks if the current model has magnetic scattering implemented
        """
        return self.document.can_have_magnetism()

    def onSelectModel(self) -> None:
        """
        The model combo box: an intent (the controller lays the tables out)
        """
        model = self.cbModel.currentText()
        if model == MODEL_DEFAULT:
            # Keep the previous model, if there was one
            if self._previous_model_index != 0:
                self.cbModel.blockSignals(True)
                self.cbModel.setCurrentIndex(self._previous_model_index)
                self.cbModel.blockSignals(False)
            return
        if not self.cbModel.isEnabled() or not model:
            return
        self._previous_model_index = self.cbModel.currentIndex()
        structure = self.cbStructureFactor.currentText() if self.cbStructureFactor.isEnabled() else ""
        self.controller.select_model(self.cbCategory.currentText(), model, structure)
        # set focus so it doesn't move up
        self.cbModel.setFocus()

    @mirrors('data', 'options')
    def onSelectBatchFilename(self, data_index: int) -> None:
        """
        Update the logic based on the selected file in batch fitting
        """
        if data_index != self.data_index:
            self.undo_stack.clear()
        self.data_index = data_index
        self.updateQRange()

    def onSelectStructureFactor(self) -> None:
        """
        The structure-factor combo box: an intent
        """
        category = self.cbCategory.currentText()
        model = "" if category == CATEGORY_STRUCTURE else self.cbModel.currentText()
        self.controller.select_model(category, model, self.cbStructureFactor.currentText(), "Select structure factor")

    def onCustomModelChange(self) -> None:
        """
        Reload the custom model combobox
        """
        ## If caching plugins, then force cache reset to reload plugins
        #ModelManager().plugins_reset()
        self.custom_models = self.customModels()
        self.readCustomCategoryInfo()
        self.onCategoriesChanged()

        # See if we need to update the combo in-place
        if self.cbCategory.currentText() != CATEGORY_CUSTOM:
            return

        current_text = self.cbModel.currentText()
        self.cbModel.clear()
        self.enableModelCombo()
        self.disableStructureCombo()
        # Retrieve the list of models
        model_list = self.master_category_dict[CATEGORY_CUSTOM]
        # Populate the models combobox
        self.cbModel.addItems(sorted([model for (model, _) in model_list]))
        new_index = self.cbModel.findText(current_text)
        if new_index != -1:
            self.cbModel.setCurrentIndex(self.cbModel.findText(current_text))

    def onSelectionChanged(self) -> None:
        """
        React to parameter selection
        """
        current_list = self.tabToList[self.tabFitting.currentIndex()]
        model_key = self.tabToKey[self.tabFitting.currentIndex()]

        rows = current_list.selectionModel().selectedRows()
        # Clean previous messages
        self.communicator.statusBarUpdateSignal.emit("")
        if len(rows) == 1:
            # Show constraint, if present
            row = rows[0].row()
            if not self.rowHasConstraint(row, model_key=model_key):
                return
            constr = self.getConstraintForRow(row, model_key=model_key)
            func = self.getConstraintForRow(row, model_key=model_key).func
            if constr.func is not None:
                # inter-parameter constraint
                update_text = "Active constraint: "+func
            elif constr.param == rows[0].data():
                # current value constraint
                update_text = "Value constrained to: " + str(constr.value)
            else:
                # ill defined constraint
                return
            self.communicator.statusBarUpdateSignal.emit(update_text)

    @mirrors('options', 'smearing', 'parameters')
    def onSesansData(self) -> None:
        """
        Updates the fitting widget format when SESANS data is loaded.
        """
        # update the units in the 'Fitting details' box of the Model tab on the Fit Panel
        self.label_17.setText("Å")
        self.label_19.setText("Å")
        # the background is fixed at 0 for SESANS by the document's rules
        # update options defaults and settings for SESANS data
        self.options_widget.updateQRange(1, 100000, self.options_widget.NPTS_DEFAULT)
        # update the units in the 'Fitting details' box of the Fit Options tab on the Fit Panel
        self.options_widget.label_13.setText("Å")
        self.options_widget.label_15.setText("Å")
        # update the smearing drop down box to indicate a Hankel Transform is being used instead of resolution
        self.smearing_widget.onIndexChange(1)
        # update the Weighting box of the Fit Options tab on the Fit Panel
        self.options_widget.rbWeighting2.setText("Use dP Data")
        self.options_widget.rbWeighting3.setText("Use |sqrt(P Data)|")
        self.options_widget.rbWeighting4.setText("Use |P Data|")

    def replaceConstraintName(self, old_name: str, new_name: str = "") -> None:
        """
        A page was renamed: the constraint expressions of this page follow
        """
        self.controller.replace_page_name(old_name, new_name)

    def isConstraintMultimodel(self, constraint: str) -> bool:
        """
        Whether the constraint expression refers to another page
        """
        return constraint_service.is_multimodel(self.document, constraint)

    def updateData(self) -> None:
        """
        Helper function for recalculation of data used in plotting
        """
        # Update the chart
        if self.data_is_loaded:
            self.cmdPlot.setText("Compute/Plot")
            self.calculateQGridForModel()
        else:
            self.cmdPlot.setText("Calculate")
            # Create default datasets if no data passed
            self.createDefaultDataset()
            self.theory_item = None # ensure theory is recalc. before plot, see showTheoryPlot()

    def onSelectCategory(self) -> None:
        """
        The category combo box: lists its models and empties the tables until one is chosen (an intent)
        """
        category = self.cbCategory.currentText()
        if category == CATEGORY_DEFAULT:
            # Keep the previous category, if there was one
            if self._previous_category_index != 0:
                self.cbCategory.blockSignals(True)
                self.cbCategory.setCurrentIndex(self._previous_category_index)
                self.cbCategory.blockSignals(False)
            return
        self._previous_category_index = self.cbCategory.currentIndex()
        self._populateCategory(category)
        if category == CATEGORY_STRUCTURE:
            self.cbStructureFactor.blockSignals(True)
            self.cbStructureFactor.setCurrentIndex(0)
            self.cbStructureFactor.blockSignals(False)
        self.controller.select_model(category)

    def onHelp(self):
        """
        Show the "Fitting" section of help
        """
        if not HELP_SYSTEM.path:
            logger.error("Help documentation was not found.")
            return
        help_location = self.getHelpLocation(HELP_SYSTEM.path)
        self.parent.showHelp(help_location)

    def getHelpLocation(self, tree_base: Path) -> Path:
        # Actual file will depend on the current tab
        tab_id = self.tabFitting.currentIndex()
        tree_location = tree_base / "user" / "qtgui" / "Perspectives" / "Fitting"

        match tab_id:
            case 0:
                # Look at the model and if set, pull out its help page
                # TODO: Disable plugin model documentation generation until issues can be resolved
                plugin_names = [name for name, enabled in self.master_category_dict.get(CATEGORY_CUSTOM, {})]
                if (self.logic.kernel_module is not None
                        and hasattr(self.logic.kernel_module, 'name')
                        and self.logic.kernel_module.id not in plugin_names
                        and not re.match("[A-Za-z0-9_-]+[+*@][A-Za-z0-9_-]+", self.logic.kernel_module.id)):
                    tree_location = tree_base / "user" / "models"
                    return tree_location / f"{self.logic.kernel_module.id}.html"
                else:
                    return tree_location / "fitting_help.html"
            case 1:
                return tree_location / "residuals_help.html"
            case 2:
                return tree_location / "resolution.html"
            case 3:
                return tree_location / "pd/polydispersity.html"
            case 4:
                return tree_location / "magnetism/magnetism.html"
            case _:
                return tree_location / "fitting.html"

    def onFit(self) -> None:
        """
        Perform fitting on the current data
        """
        if self.fit_started:
            self.stopFit()
            return

        # If this page takes part in a running constrained/simultaneous fit,
        # the button reads 'Stop fit', so stop that fit instead of starting a new one
        if self.stopConstrainedFit():
            return

        # initialize fitter constants
        handler = None
        batch_inputs = {}
        batch_outputs = {}
        #---------------------------------
        if config.USING_TWISTED:
            handler = None
            updater = None
        else:
            handler = ConsoleUpdate(parent=self.parent,
                                    manager=self,
                                    improvement_delta=0.1)
            updater = handler.update_fit

        # Prepare the fitter object
        try:
            fitters, _ = self.fitting_controller.prepareFitters()
        except ValueError as ex:
            # This should not happen! GUI explicitly forbids this situation
            self.communicator.statusBarUpdateSignal.emit(str(ex))
            return

        # Create the fitting thread, based on the fitter
        completefn = self.batchFittingCompleted if self.is_batch_fitting else self.fittingCompleted

        self.calc_fit = FitThread(handler=handler,
                                  fn=fitters,
                                  batch_inputs=batch_inputs,
                                  batch_outputs=batch_outputs,
                                  page_id=[[self.page_id]],
                                  updatefn=updater,
                                  completefn=completefn,
                                  reset_flag=self.is_chain_fitting)

        if config.USING_TWISTED:
            # start the trhrhread with twisted
            calc_thread = threads.deferToThread(self.calc_fit.compute)
            calc_thread.addCallback(completefn)
            calc_thread.addErrback(self.fitFailed)
        else:
            # Use the old python threads + Queue
            self.calc_fit.queue()
            self.calc_fit.ready(2.5)

        self.communicator.statusBarUpdateSignal.emit('Fitting started...')
        self.fit_started = True

        # Disable some elements
        self.disableInteractiveElements()
        # The undo stack stays enabled during the fit; intermediate parameter
        # updates are blocked via the suppressed() context manager instead.

    def stopConstrainedFit(self) -> bool:
        """
        Stop the constrained/simultaneous fit this page takes part in, if any.
        Returns True if a running constrained fit was stopped.
        """
        if self.parent is None:
            return False
        constraint_tab = self.parent.perspective().getConstraintTab()
        if constraint_tab is None or not constraint_tab.is_running:
            return False
        page_name = "Page%s" % self.tab_id
        if not any(page_name in tab for tab in constraint_tab.getTabsForFit()):
            return False
        constraint_tab.stopFit()
        return True

    def stopFit(self) -> None:
        """
        Attempt to stop the fitting thread
        """
        if self.calc_fit is None or not self.calc_fit.isrunning():
            return
        self.calc_fit.stop()
        #re-enable the Fit button
        self.enableInteractiveElements()

        msg = "Fitting cancelled."
        self.communicator.statusBarUpdateSignal.emit(msg)
        self.communicator.undoRedoUpdateSignal.emit()

    def updateFit(self) -> None:
        """
        """
        print("UPDATE FIT")
        pass

    def fitFailed(self, reason: Any) -> None:
        """
        """
        self.enableInteractiveElements()
        msg = "Fitting failed with: "+ str(reason)
        self.communicator.statusBarUpdateSignal.emit(msg)

    def batchFittingCompleted(self, result: tuple | None) -> None:
        """
        Send the finish message from calculate threads to main thread
        """
        if result is None:
            result = tuple()
        self.batchFittingFinishedSignal.emit(result)

    @mirrors('data')
    def batchFitComplete(self, result: tuple) -> None:
        """
        Receive and display batch fitting results
        """
        #re-enable the Fit button
        self.enableInteractiveElements()

        if len(result) == 0:
            msg = "Fitting failed."
            self.communicator.statusBarUpdateSignal.emit(msg)
            return

        # Show the grid panel
        page_name = "BatchPage" + str(self.tab_id)
        results = copy.deepcopy(result[0])
        results.append(page_name)
        self.communicator.sendDataToGridSignal.emit(results)

        elapsed = result[1]
        msg = "Fitting completed successfully in: %s s.\n" % GuiUtils.formatNumber(elapsed)
        self.communicator.statusBarUpdateSignal.emit(msg)

        # Run over the list of results and update the items
        for res_index, res_list in enumerate(result[0]):
            # results
            res = res_list[0]
            param_dict = self.fitting_controller.paramDictFromResults(res)

            # create local kernel_module
            kernel_module = FittingUtilities.updateKernelWithResults(self.logic.kernel_module, param_dict)
            if kernel_module is None:
                continue
            # pull out current data
            data = self._logic[res_index].data

            # Switch indexes
            self.data_index = res_index

            # Recalculate theories
            method = self.complete1D if isinstance(self.data, Data1D) else self.complete2D
            self.calculateQGridForModelExt(data=data, model=kernel_module, completefn=method, use_threads=False)

    def paramDictFromResults(self, results: Any) -> dict[str, tuple[float, float]] | None:
        """
        Given the fit results structure, pull out optimized parameters.

        Delegated to FittingController.
        """
        return self.fitting_controller.paramDictFromResults(results)

    def fittingCompleted(self, result: tuple | None) -> None:
        """
        Send the finish message from calculate threads to main thread
        """
        if result is None:
            result = tuple()
        self.fittingFinishedSignal.emit(result)

    def fitComplete(self, result: tuple) -> None:
        """
        Receive and display fitting results
        "result" is a tuple of actual result list and the fit time in seconds
        """
        #re-enable the Fit button
        self.enableInteractiveElements()

        if not result or not result[0] or not result[0][0]:
            msg = "Fitting failed."
            self.communicator.statusBarUpdateSignal.emit(msg)
            return

        # Don't recalculate chi2 - it's in res.fitness already
        self.fitResults = True
        if result is None or len(result) == 0 or len(result[0]) == 0:
            msg = "Fitting failed."
            self.communicator.statusBarUpdateSignal.emit(msg)
            return
        res_list = result[0][0]
        res = res_list[0]
        self.chi2 = res.fitness
        param_dict = self.fitting_controller.paramDictFromResults(res)

        if param_dict is None:
            return

        # Show bumps convergence plots
        self.communicator.resultPlotUpdateSignal.emit(result[0])

        elapsed = result[1]
        if self.calc_fit is not None and self.calc_fit._interrupting:
            msg = "Fitting cancelled by user after: %s s." % GuiUtils.formatNumber(elapsed)
            logger.warning("\n"+msg+"\n")
        else:
            msg = "Fitting completed successfully in: %s s." % GuiUtils.formatNumber(elapsed)
        self.communicator.statusBarUpdateSignal.emit(msg)

        # Dictionary of fitted parameter: value, error
        # e.g. param_dic = {"sld":(1.703, 0.0034), "length":(33.455, -0.0983)}: one undoable step
        self.controller.apply_fit(param_dict)

        # Clean up polydispersity plots if polydispersity has been disabled
        if not self.chkPolydispersity.isChecked():
            self.preparePlotsForDeletion(DataRole.ROLE_POLYDISPERSITY)

        # update charts
        self.onPlot()

        # Read only value - we can get away by just printing it here
        chi2_repr = GuiUtils.formatNumber(self.chi2, high=True)
        self.lblChi2Value.setText(chi2_repr)

        # Ensure undo/redo action state is refreshed in the GUI manager.
        # The push above emits stackChanged, but if the per-stack signal
        # connection was disrupted (e.g. tab change during processEvents
        # in onPlot), this communicator signal provides a reliable fallback.
        self.communicator.undoRedoUpdateSignal.emit()

    def preparePlotsForDeletion(self, redundant_role: DataRole):
        """If plots with a particular role are no longer required, change their role to ROLE_DELETABLE."""
        if not self.all_data:
            return
        item_model = self.all_data[self.data_index].model()
        plots = GuiUtils.plotsFromDisplayName(self.data.name, item_model).values()
        for plot in plots:
            if plot.plot_role == redundant_role:
                plot.plot_role = DataRole.ROLE_DELETABLE

    def setPlotDeletable(self, parameter_name: str) -> None:
        """Set the plot role to ROLE_DELETABLE for the polydispersity plot with the given parameter name."""
        item_model = self.all_data[self.data_index].model()
        plots = GuiUtils.plotsFromDisplayName(self.data.name, item_model).values()
        data_name = self.nameForFittedData(self.data.name).split()
        poly_plot_name = polydispersity_plot_name.format(data_name[0], parameter_name, " ".join(data_name[1:]))
        poly_plots = [plot for plot in plots if plot.name == poly_plot_name]
        for plot in poly_plots:
            plot.plot_role = DataRole.ROLE_DELETABLE

    def prepareFitters(self, fitter: Fit | None = None, fit_id: int = 0, weight_increase: int = 1) -> tuple[list[Fit], int]:
        """
        Prepare the Fitter object for use in fitting.

        Delegated to FittingController.
        """
        return self.fitting_controller.prepareFitters(fitter, fit_id, weight_increase)

    def onPlot(self) -> None:
        """
        Plot the current set of data
        """
        # Regardless of previous state, this should now be `plot show` functionality only
        self.cmdPlot.setText("Compute/Plot")
        # Force data recalculation so existing charts are updated
        if not self.data_is_loaded:
            self.showTheoryPlot()
        else:
            self.showPlot()
        # This is an important processEvent.
        # This allows charts to be properly updated in order
        # of plots being applied.
        QtWidgets.QApplication.processEvents()
        self.recalculatePlotData()  # recalc+plot theory again (2nd)

    def onSmearingOptionsUpdate(self) -> None:
        """
        React to changes in the smearing widget: an intent
        """
        if self.controller.muted:
            return
        smearing, accuracy, d_down, d_up = self.smearing_widget.state()
        self.lblCurrentSmearing.setText(smearing)
        self.controller.set_smearing(Smearing(smearing, accuracy, d_down, d_up))

    def onKey(self, event: QtGui.QKeyEvent) -> None:
        if event.key() in [QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return] and self.cmdPlot.isEnabled():
            self.onPlot()

    def recalculatePlotData(self) -> None:
        """
        Generate a new dataset for model
        """
        if not self.data_is_loaded:
            self.createDefaultDataset()
            self.smearing_widget.updateData(self.data)
        self.calculateQGridForModel()

    def showTheoryPlot(self) -> None:
        """
        Show the current theory plot in MPL
        """
        # Show the chart if ready
        if self.theory_item is None:
            self.recalculatePlotData()
        elif self.model_data:
            self._requestPlots(self.model_data.name, self.theory_item.model())

    def showPlot(self) -> None:
        """
        Show the current plot in MPL
        """
        # Show the chart if ready
        data_to_show = self.data
        # Any models for this page
        current_index = self.all_data[self.data_index]
        item = self._requestPlots(self.data.name, current_index.model())
        if item:
            # fit+data has not been shown - show just data
            self.communicator.plotRequestedSignal.emit([item, data_to_show])

    def _requestPlots(self, item_name: str, item_model: Any) -> Any | None:
        """
        Emits plotRequestedSignal for all plots found in the given model under the provided item name.
        """
        fitpage_name = self.logic.kernel_module.name
        plots = GuiUtils.plotsFromDisplayName(item_name, item_model)
        # Has the fitted data been shown?
        data_shown = False
        item = None
        for item, plot in plots.items():
            if plot.plot_role != DataRole.ROLE_DATA and fitpage_name in plot.name:
                data_shown = True
                self.communicator.plotRequestedSignal.emit([item, plot])
        # return the last data item seen, if nothing was plotted; supposed to be just data)
        return None if data_shown else item

    def onOptionsUpdate(self) -> None:
        """
        A change in the options tab: an intent
        """
        if self.controller.muted:
            return
        self.q_range_min, self.q_range_max, self.npts, self.log_points, self.weighting =             self.options_widget.state()
        # set Q range labels on the main tab
        self.lblMinRangeDef.setText(GuiUtils.formatNumber(self.q_range_min, high=True))
        self.lblMaxRangeDef.setText(GuiUtils.formatNumber(self.q_range_max, high=True))
        self.controller.set_options(FitOptions(self.q_range_min, self.q_range_max, self.npts, self.log_points,
                                               self.weighting, self.options_widget.weighting))

    def setDefaultStructureCombo(self) -> None:
        """
        Fill in the structure factors combo box with defaults
        """
        structure_factor_list = self.master_category_dict.pop(CATEGORY_STRUCTURE)
        # Only offer structure factors that are actually loadable. The
        # categorization file (which may be a stale user file) can list models
        # that are not present in the installed sasmodels, and selecting one of
        # those would raise a KeyError in self.models[...] and leave the page
        # in a broken state.
        factors = [factor[0] for factor in structure_factor_list if factor[0] in self.models]
        factors.insert(0, STRUCTURE_DEFAULT)
        self.cbStructureFactor.clear()
        self.cbStructureFactor.addItems(sorted(factors))

    @mirrors('data')
    def createDefaultDataset(self) -> None:
        """
        Generate default Dataset 1D/2D for the given model
        """
        # Create default datasets if no data passed
        if self.is2D:
            qmax = self.q_range_max/np.sqrt(2)
            qstep = self.npts
            self.logic.createDefault2dData(qmax, qstep, self.tab_id)
            return
        elif self.log_points:
            qmin = -10.0 if self.q_range_min < 1.e-10 else np.log10(self.q_range_min)
            qmax = 10.0 if self.q_range_max > 1.e10 else np.log10(self.q_range_max)
            interval = np.logspace(start=qmin, stop=qmax, num=self.npts, endpoint=True, base=10.0)
        else:
            interval = np.linspace(start=self.q_range_min, stop=self.q_range_max,
                                   num=int(self.npts), endpoint=True)
        self.logic.createDefault1dData(interval, self.tab_id)

    def readCategoryInfo(self) -> None:
        """
        Reads the categories in from file
        """
        self.master_category_dict = defaultdict(list)
        self.by_model_dict = defaultdict(list)
        self.model_enabled_dict = defaultdict(bool)

        categorization_file = CategoryInstaller.get_user_file()
        if not os.path.isfile(categorization_file):
            categorization_file = CategoryInstaller.get_default_file()
        with open(categorization_file, 'rb') as cat_file:
            self.master_category_dict = json.load(cat_file)
            self.regenerateModelDict()

        # Load the model dict
        models = load_standard_models()
        for model in models:
            self.models[model.name] = model

        self.readCustomCategoryInfo()

    def readCustomCategoryInfo(self) -> None:
        """
        Reads the custom model category
        """
        #Looking for plugins
        self.plugins = list(self.custom_models.values())
        plugin_list = []
        for name, plug in self.custom_models.items():
            self.models[name] = plug
            plugin_list.append([name, True])
        if plugin_list:
            self.master_category_dict[CATEGORY_CUSTOM] = plugin_list
        # Adding plugins classified as structure factor to 'CATEGORY_STRUCTURE' list
        if CATEGORY_STRUCTURE in self.master_category_dict:
            plugin_structure_list = [
                [name, True] for name, plug in self.custom_models.items()
                if plug.is_structure_factor
                and [name, True] not in self.master_category_dict[CATEGORY_STRUCTURE]
            ]
            if plugin_structure_list:
                self.master_category_dict[CATEGORY_STRUCTURE].extend(plugin_structure_list)

    def regenerateModelDict(self) -> None:
        """
        Regenerates self.by_model_dict which has each model name as the
        key and the list of categories belonging to that model
        along with the enabled mapping
        """
        self.by_model_dict = defaultdict(list)
        master_category_list_iterator = self.master_category_dict.copy()
        for category in master_category_list_iterator:
            for (model, enabled) in master_category_list_iterator[category]:
                if model not in MODELS:
                    logging.warning(f"The model {model} is no longer available in sasmodels. It will be ignored.")
                    self.master_category_dict[category].remove([model, enabled])
                    continue
                self.by_model_dict[model].append(category)
                self.model_enabled_dict[model] = enabled

    def addWeightingToData(self, data: Data1D | Data2D) -> Data1D | Data2D:
        """
        Adds weighting contribution to fitting data
        """
        if not self.data_is_loaded:
            # no weighting for theories (dy = 0)
            return data
        new_data = copy.deepcopy(data)
        # Send original data for weighting
        weight = FittingUtilities.getWeight(data=data, is2d=self.is2D, flag=self.weighting)
        if self.is2D:
            new_data.err_data = weight
        else:
            new_data.dy = weight

        return new_data

    @mirrors('options')
    def updateQRange(self) -> None:
        """
        Updates Q Range display
        """
        if self.data_is_loaded:
            self.q_range_min, self.q_range_max, self.npts = self.logic.computeDataRange()
        # set Q range labels on the main tab
        self.lblMinRangeDef.setText(GuiUtils.formatNumber(self.q_range_min, high=True))
        self.lblMaxRangeDef.setText(GuiUtils.formatNumber(self.q_range_max, high=True))

        # set Q range labels on the options tab
        self.options_widget.updateQRange(self.q_range_min, self.q_range_max, self.npts)

    def haveParamsToFit(self) -> bool:
        """
        Finds out if there are any parameters ready to be fitted
        """
        return self.document.can_fit()

    def isCheckable(self, row: int, model_key: str = "standard") -> bool:
        model = self.model_dict[model_key]
        if model.item(row,0) is None:
            return False
        return model.item(row, 0).isCheckable()

    def createNewIndex(self, fitted_data: Data1D | Data2D) -> None:
        """
        Create a model or theory index with passed Data1D/Data2D
        """
        if self.data_is_loaded:
            if not fitted_data.name:
                name = self.nameForFittedData(self.data.name)
                fitted_data.title = name
                fitted_data.name = name
                fitted_data.filename = name
                fitted_data.symbol = "Line"
            self.updateModelIndex(fitted_data)
        else:
            if not fitted_data.name:
                name = self.nameForFittedData(self.logic.kernel_module.id)
            else:
                name = fitted_data.name
            fitted_data.title = name
            fitted_data.filename = name
            fitted_data.symbol = "Line"
            self.createTheoryIndex(fitted_data)
            # Switch to the theory tab for user's glee
            self.communicator.changeDataExplorerTabSignal.emit(1)

    def updateModelIndex(self, fitted_data: Data1D | Data2D) -> None:
        """
        Update a QStandardModelIndex containing model data
        """
        name = self.nameFromData(fitted_data)
        # Make this a line if no other defined
        if hasattr(fitted_data, 'symbol') and fitted_data.symbol is None:
            fitted_data.symbol = 'Line'
        # Notify the GUI manager so it can update the main model in DataExplorer
        GuiUtils.updateModelItemWithPlot(self.all_data[self.data_index], fitted_data, name)

    def createTheoryIndex(self, fitted_data: Data1D | Data2D) -> None:
        """
        Create a QStandardModelIndex containing model data
        """
        name = self.nameFromData(fitted_data)
        # TODO: Temporary Hack to fix NaNs in generated theory data
        #  This is usually from GSC models that are calculated outside the Q range they were created for
        #  The 'remove_nans_in_data' should become its own function in a data utility class, post-6.0.0 release.
        from sasdata.dataloader.filereader import FileReader
        temp_reader = FileReader()
        fitted_data = temp_reader._remove_nans_in_data(fitted_data)
        # Modify the item or add it if new
        theory_item = GuiUtils.createModelItemWithPlot(fitted_data, name=name)
        self.communicator.updateTheoryFromPerspectiveSignal.emit(theory_item)

    def setTheoryItem(self, item: Any) -> None:
        """
        Reset the theory item based on the data explorer update
        """
        self.theory_item = item

    def nameFromData(self, fitted_data: Data1D | Data2D) -> str:
        """
        Return name for the dataset. Terribly impure function.
        """
        if fitted_data.name is None:
            name = self.nameForFittedData(self.logic.data.name)
            fitted_data.title = name
            fitted_data.name = name
            fitted_data.filename = name
        else:
            name = fitted_data.name
        return name

    def methodCalculateForData(self) -> Any:
        '''return the method for data calculation'''
        return Calc1D if isinstance(self.data, Data1D) else Calc2D

    def methodCompleteForData(self) -> Any:
        '''return the method for result parsin on calc complete '''
        return self.completed1D if isinstance(self.data, Data1D) else self.completed2D

    def calculateQGridForModelExt(self, data: Data1D | Data2D | None = None, model: Any | None = None, completefn: Any | None = None, use_threads: bool = True) -> None:
        """
        Wrapper for Calc1D/2D calls
        """
        if data is None:
            data = self.data
        if model is None:
            # The kernel holds the document's effective state (KernelBuilder.build)
            model = copy.deepcopy(self.logic.kernel_module)

        if completefn is None:
            completefn = self.methodCompleteForData()
        smearer = self.smearing_widget.smearer()
        weight = FittingUtilities.getWeight(data=data, is2d=self.is2D, flag=self.weighting)

        # Disable buttons/table
        self.disableInteractiveElementsOnCalculate()
        # Awful API to a backend method.
        calc_thread = self.methodCalculateForData()(data=data,
                                               model=model,
                                               page_id=0,
                                               qmin=self.q_range_min,
                                               qmax=self.q_range_max,
                                               smearer=smearer,
                                               state=None,
                                               weight=weight,
                                               fid=None,
                                               toggle_mode_on=False,
                                               completefn=completefn,
                                               update_chisqr=True,
                                               exception_handler=self.calcException,
                                               source=None)
        if use_threads:
            if config.USING_TWISTED:
                # start the thread with twisted
                thread = threads.deferToThread(calc_thread.compute)
                thread.addCallback(completefn)
                thread.addErrback(self.calculateDataFailed)
            else:
                # Use the old python threads + Queue
                calc_thread.queue()
                calc_thread.ready(2.5)
        else:
            results = calc_thread.compute()
            completefn(results)

    def calculateQGridForModel(self) -> None:
        """
        Prepare the fitting data object, based on current ModelModel
        """
        if self.logic.kernel_module is None:
            return
        self.calculateQGridForModelExt()

    def calculateDataFailed(self, reason: Any) -> None:
        """
        Thread returned error
        """
        # Bring the GUI to normal state
        self.enableInteractiveElements()
        print("Calculate Data failed with ", reason)

    def completed1D(self, return_data: dict) -> None:
        self.Calc1DFinishedSignal.emit(return_data)

    def completed2D(self, return_data: dict) -> None:
        self.Calc2DFinishedSignal.emit(return_data)

    def _appendPlotsPolyDisp(self, new_plots: list[Any], return_data: dict, fitted_data: Data1D | Data2D) -> None:
        """
        Internal helper for 1D and 2D for creating plots of the polydispersity distribution for
        parameters which have a polydispersity enabled
        """
        for plot in FittingUtilities.plotPolydispersities(return_data.get('model', None)):
            data_id = fitted_data.id.split()
            plot.id = f"{data_id[0]} [{plot.name} polydispersity] {' '.join(data_id[1:])}"
            data_name = fitted_data.name.split()
            plot.name = polydispersity_plot_name.format(data_name[0], plot.name, " ".join(data_name[1:]))
            self.createNewIndex(plot)
            new_plots.append(plot)

    def complete1D(self, return_data: dict) -> None:
        """
        Plot the current 1D data
        """
        # Bring the GUI to normal state
        self.enableInteractiveElements()
        if return_data is None:
            return
        fitted_data = self.logic.new1DPlot(return_data, self.tab_id)

        # Fits of Sesans data are in real space
        if return_data["data"].isSesans:
            fitted_data.isSesans = True
            fitted_data.xtransform="x"
            fitted_data.ytransform="y"

        # assure the current index is set properly for batch
        if len(self._logic) > 1:
            for i, logic in enumerate(self._logic):
                if logic.data.name in fitted_data.name:
                    self.data_index = i

        residuals = self.calculateResiduals(fitted_data)

        # SESANS residuals should be on lin-lin scale
        if return_data["data"].isSesans:
            residuals.plot_role = DataRole.ROLE_RESIDUAL_SESANS

        fitted_data.show_q_range_sliders = True
        # Suppress the GUI update until the move is finished to limit model calculations
        fitted_data.slider_update_on_move = False
        fitted_data.slider_tab_name = self.modelName()
        fitted_data.slider_perspective_name = 'Fitting'
        fitted_data.slider_high_q_input = ['options_widget', 'txtMaxRange']
        fitted_data.slider_high_q_setter = ['options_widget', 'updateMaxQ']
        fitted_data.slider_low_q_input = ['options_widget', 'txtMinRange']
        fitted_data.slider_low_q_setter = ['options_widget', 'updateMinQ']

        self.model_data = fitted_data
        new_plots = [fitted_data]
        if residuals is not None:
            new_plots.append(residuals)

        if self.data_is_loaded:
            # delete any plots associated with the data that were not updated
            # (e.g. to remove beta(Q), S_eff(Q))
            GuiUtils.deleteRedundantPlots(self.all_data[self.data_index], new_plots)
            pass
        else:
            # delete theory items for the model, in order to get rid of any
            # redundant items, e.g. beta(Q), S_eff(Q)
            self.communicator.deleteIntermediateTheoryPlotsSignal.emit(str(self.tab_id))

        self._appendPlotsPolyDisp(new_plots, return_data, fitted_data)

        # Create plots for intermediate product data
        plots = self.logic.new1DProductPlots(return_data, self.tab_id)
        for plot in plots:
            plot.symbol = "Line"
            self.createNewIndex(plot)
            new_plots.append(plot)

        for plot in new_plots:
            self.communicator.plotUpdateSignal.emit([plot])
            QtWidgets.QApplication.processEvents()

        # Update radius_effective if relevant
        self.updateEffectiveRadius(return_data)

    def complete2D(self, return_data: dict) -> None:
        """
        Plot the current 2D data
        """
        # Bring the GUI to normal state
        self.enableInteractiveElements()

        if return_data is None:
            return

        fitted_data = self.logic.new2DPlot(return_data)
        # assure the current index is set properly for batch
        if len(self._logic) > 1:
            for i, logic in enumerate(self._logic):
                if logic.data.name in fitted_data.name:
                    self.data_index = i

        residuals = self.calculateResiduals(fitted_data)
        self.model_data = fitted_data
        new_plots = [fitted_data]
        if residuals is not None:
            new_plots.append(residuals)

        self._appendPlotsPolyDisp(new_plots, return_data, fitted_data)

        # Update/generate plots
        for plot in new_plots:
            self.communicator.plotUpdateSignal.emit([plot])

    def updateEffectiveRadius(self, return_data: dict) -> None:
        """
        The effective radius sasmodels computed (radius_effective_mode > 0): shown in the table,
        written to the document as a derived value (never recorded, never recalculating).
        """
        params = self.document.parameters
        if "radius_effective" not in params or "radius_effective_mode" not in params:
            return
        if int(params["radius_effective_mode"].value) < 1:
            return
        value = self.logic.getScalarIntermediateResults(return_data).get("radius_effective")
        if value is None or value == params["radius_effective"].value:
            return
        with self.controller.transaction(Origin.DERIVED) as tx:
            tx.set_parameter("radius_effective", value=float(value))

    def calculateResiduals(self, fitted_data: Data1D | Data2D) -> Data1D | Data2D | None:
        """
        Calculate and print Chi2 and display chart of residuals. Returns residuals plot object.
        """
        # Create a new index for holding data
        fitted_data.symbol = "Line"

        # Modify fitted_data with weighting
        weighted_data = self.addWeightingToData(fitted_data)

        self.createNewIndex(weighted_data)

        # Plot residuals if actual data
        if not self.data_is_loaded:
            return

        # Calculate difference between return_data and logic.data
        weights = FittingUtilities.getWeight(self.data, self.is2D, flag = self.weighting)
        # Recalculate chi2 only for manual parameter change, not after fitting
        if not self.fitResults:
            self.chi2 = FittingUtilities.calculateChi2(weighted_data, self.data, weights)
            # Update the control
            chi2_repr = "---" if self.chi2 is None else GuiUtils.formatNumber(self.chi2, high=True)
            self.lblChi2Value.setText(chi2_repr)
        self.fitResults = False

        residuals_plot = FittingUtilities.plotResiduals(self.data, fitted_data, weights)
        if residuals_plot is None:
            return
        residuals_plot.id = "Residual " + residuals_plot.id
        residuals_plot.plot_role = DataRole.ROLE_RESIDUAL
        self.createNewIndex(residuals_plot)
        return residuals_plot

    def onCategoriesChanged(self) -> None:
            """
            Reload the category/model comboboxes
            """
            # Store the current combo indices
            current_cat = self.cbCategory.currentText()
            current_model = self.cbModel.currentText()

            # reread the category file and repopulate the combo
            self.cbCategory.blockSignals(True)
            self.cbCategory.clear()
            self.readCategoryInfo()
            self.initializeCategoryCombo()

            # Scroll back to the original index in Categories
            new_index = self.cbCategory.findText(current_cat)
            if new_index != -1:
                self.cbCategory.setCurrentIndex(new_index)
            self.cbCategory.blockSignals(False)
            # ...and in the Models
            self.cbModel.blockSignals(True)
            new_index = self.cbModel.findText(current_model)
            if new_index != -1:
                self.cbModel.setCurrentIndex(new_index)
            self.cbModel.blockSignals(False)

            return

    def calcException(self, etype: Any, value: Any, tb: Any) -> None:
        """
        Thread threw an exception.
        """
        # Bring the GUI to normal state
        self.enableInteractiveElements()
        # TODO: remimplement thread cancellation
        logger.error("".join(traceback.format_exception(etype, value, tb)))

    def onColumnWidthUpdate(self, index: int, old_size: int, new_size: int) -> None:
        """
        Simple state update of the current column widths in the  param list
        """
        self.lstParamHeaderSizes[index] = new_size

    def modifyShellsInList(self, text: str) -> None:
        """
        The shell-count combo box: an intent
        """
        try:
            shells = int(text)
        except ValueError:
            logger.error("Multiplicity incorrect!")
            return
        self.controller.set_multiplicity(shells)

    def onShowSLDProfile(self) -> None:
        """
        Show a quick plot of SLD profile
        """
        # get profile data
        try:
            x, y = self.logic.kernel_module.getProfile()
        except TypeError:
            msg = "SLD profile calculation failed."
            logger.error(msg)
            return

        y *= 1.0e6
        profile_data = Data1D(x=x, y=y)
        profile_data.name = "SLD"
        profile_data.scale = 'linear'
        profile_data.symbol = 'Line'
        profile_data.hide_error = True
        profile_data._xaxis = "R"
        profile_data._xunit = r"\AA"
        profile_data._yaxis = "SLD"
        profile_data._yunit = r"10^{-6}\AA^{-2}"
        profile_data.ytransform='y'
        profile_data.xtransform='x'

        profile_data.id = "sld"

        plotter = PlotterWidget(self, quickplot=True)
        plotter.showLegend = False
        plotter.plot(data=profile_data, hide_error=True, marker='-')

        self.plot_widget = QtWidgets.QWidget()
        self.plot_widget.setWindowTitle("Scattering Length Density Profile")
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(plotter)
        self.plot_widget.setLayout(layout)
        self.plot_widget.show()

    def setInteractiveElements(self, enabled: bool = True) -> None:
        """
        Switch interactive GUI elements on/off
        """
        assert isinstance(enabled, bool)

        self.lstParams.setEnabled(enabled)
        self.lstPoly.setEnabled(enabled)
        self.lstMagnetic.setEnabled(enabled)

        self.cbCategory.setEnabled(enabled)

        if enabled:
            # worry about original enablement of model and SF
            self.cbModel.setEnabled(self.enabled_cbmodel)
            self.cbStructureFactor.setEnabled(self.enabled_sfmodel)
        else:
            self.cbModel.setEnabled(enabled)
            self.cbStructureFactor.setEnabled(enabled)

        self.cmdPlot.setEnabled(enabled)

    def enableInteractiveElements(self) -> None:
        """
        Set button caption on fitting/calculate finish
        Enable the param table(s)
        """
        # Notify the user that fitting is available
        self.cmdFit.setStyleSheet(BG_DEFAULT)
        self.cmdFit.setText("Fit")
        self.fit_started = False
        self.setInteractiveElements(True)

    def disableInteractiveElements(self) -> None:
        """
        Set button caption on fitting/calculate start
        Disable the param table(s)
        """
        # Notify the user that fitting is being run
        # Allow for stopping the job
        self.cmdFit.setStyleSheet(BG_ERROR)
        self.cmdFit.setText('Stop fit')
        self.setInteractiveElements(False)

    def disableInteractiveElementsOnCalculate(self) -> None:
        """
        Set button caption on fitting/calculate start
        Disable the param table(s)
        """
        # Notify the user that fitting is being run
        # Allow for stopping the job
        self.cmdFit.setStyleSheet(BG_ERROR)
        self.cmdFit.setText('Running...')
        self.setInteractiveElements(False)

    def readFitPage(self, fp: FitPage) -> None:
        """
        Read in state from a fitpage object and update GUI
        """
        assert isinstance(fp, FitPage)
        # Main tab info
        self.logic.data.name = fp.name
        self.data_is_loaded = fp.data_is_loaded
        self.chkPolydispersity.setChecked(fp.is_polydisperse)
        self.chkMagnetism.setChecked(fp.is_magnetic)
        self.chk2DView.setChecked(fp.is2D)

        # Update the comboboxes
        self.cbCategory.setCurrentIndex(self.cbCategory.findText(fp.current_category))
        self.cbModel.setCurrentIndex(self.cbModel.findText(fp.current_model))
        if fp.current_factor:
            self.cbStructureFactor.setCurrentIndex(self.cbStructureFactor.findText(fp.current_factor))

        self.chi2 = fp.chi2

        # Options tab
        self.q_range_min = fp.fit_options[fp.MIN_RANGE]
        self.q_range_max = fp.fit_options[fp.MAX_RANGE]
        self.npts = fp.fit_options[fp.NPTS]
        self.log_points = fp.fit_options[fp.LOG_POINTS]
        self.weighting = fp.fit_options[fp.WEIGHTING]

        # Models
        self._model_model = fp.model_model
        self.polydispersity_widget.poly_model = fp.poly_model
        self.magnetism_widget._magnet_model = fp.magnetism_model

        # Resolution tab
        smearing = fp.smearing_options[fp.SMEARING_OPTION]
        accuracy = fp.smearing_options[fp.SMEARING_ACCURACY]
        smearing_min = fp.smearing_options[fp.SMEARING_MIN]
        smearing_max = fp.smearing_options[fp.SMEARING_MAX]
        self.smearing_widget.setState(smearing, accuracy, smearing_min, smearing_max)

        # TODO: add polidyspersity and magnetism

    def saveToFitPage(self, fp: FitPage) -> None:
        """
        Write current state to the given fitpage
        """
        assert isinstance(fp, FitPage)

        # Main tab info
        fp.name = self.logic.data.name
        fp.data_is_loaded = self.data_is_loaded
        fp.is_polydisperse = self.chkPolydispersity.isChecked()
        fp.is_magnetic = self.chkMagnetism.isChecked()
        fp.is2D = self.chk2DView.isChecked()
        fp.data = self.data

        # Use current models - they contain all the required parameters
        fp.model_model = self._model_model
        fp.poly_model = self.polydispersity_widget.poly_model
        fp.magnetism_model = self.magnetism_widget._magnet_model

        if self.cbCategory.currentIndex() != 0:
            fp.current_category = str(self.cbCategory.currentText())
            fp.current_model = str(self.cbModel.currentText())

        if self.cbStructureFactor.isEnabled() and self.cbStructureFactor.currentIndex() != 0:
            fp.current_factor = str(self.cbStructureFactor.currentText())
        else:
            fp.current_factor = ''

        fp.chi2 = self.chi2
        params = self.document.parameters
        fitted = lambda table: [p.key for p in params.by_table(table) if p.fit and p.fittable]  # noqa: E731
        fp.main_params_to_fit = [params.legacy_key(k) for k in fitted(Table.MAIN)]
        fp.poly_params_to_fit = fitted(Table.POLY)
        fp.magnet_params_to_fit = fitted(Table.MAGNET)
        fp.kernel_module = self.logic.kernel_module

        # Algorithm options
        # fp.algorithm = self.parent.fit_options.selected_id

        # Options tab
        fp.fit_options[fp.MIN_RANGE] = self.q_range_min
        fp.fit_options[fp.MAX_RANGE] = self.q_range_max
        fp.fit_options[fp.NPTS] = self.npts
        #fp.fit_options[fp.NPTS_FIT] = self.npts_fit
        fp.fit_options[fp.LOG_POINTS] = self.log_points
        fp.fit_options[fp.WEIGHTING] = self.weighting

        # Resolution tab
        smearing, accuracy, smearing_min, smearing_max = self.smearing_widget.state()
        fp.smearing_options[fp.SMEARING_OPTION] = smearing
        fp.smearing_options[fp.SMEARING_ACCURACY] = accuracy
        fp.smearing_options[fp.SMEARING_MIN] = smearing_min
        fp.smearing_options[fp.SMEARING_MAX] = smearing_max

        # TODO: add polydispersity and magnetism

    # ------------------------------------------------------------------
    # Undo/redo helper methods (called by UndoCommand subclasses)
    # ------------------------------------------------------------------

    def getReport(self) -> list[str]:
        """
        Create and return HTML report with parameters and charts
        """
        index = None
        if self.all_data:
            index = self.all_data[self.data_index]
        else:
            index = self.theory_item
        report_logic = ReportPageLogic(self,
                                       kernel_module=self.logic.kernel_module,
                                       data=self.data,
                                       index=index,
                                       params=self._report_parameters())

        return report_logic.reportList()

    def _report_parameters(self) -> list[list]:
        """The report's parameter rows (serializer.report_parameters)."""
        return serializer.report_parameters(self.document)

    def loadPageStateCallback(self, state: Any | None = None, datainfo: Any | None = None, format: Any | None = None) -> None:
        """
        This is a callback method called from the CANSAS reader.
        We need the instance of this reader only for writing out a file,
        so there's nothing here.
        Until Load Analysis is implemented, that is.
        """
        pass

    def loadPageState(self, pagestate: Any | None = None) -> None:
        """
        Load the PageState object and update the current widget
        """
        _ = self.loadAnalysisFile()
        pass

    def loadAnalysisFile(self) -> str:
        """
        Called when the "Open Project" menu item chosen.
        """
        default_name = "FitPage"+str(self.tab_id)+".fitv"
        wildcard = "fitv files (*.fitv)"
        kwargs = {
            'caption'   : 'Open Analysis',
            'directory' : default_name,
            'filter'    : wildcard,
            'parent'    : self,
        }
        filename = QtWidgets.QFileDialog.getOpenFileName(**kwargs)[0]
        return filename

    def getParameterDict(self) -> dict[str, list[str]]:
        """
        Gather current fitting parameters as dict
        """

        param_list = self.getFitPage()
        param_list += self.getFitModel()

        params = FittingUtilities.formatParameters(param_list)
        lines = params.split(':')
        # put the text into dictionary
        line_dict = {}
        for line in lines[1:]:
            content = line.split(',')
            if len(content) > 1:
                line_dict[content[0]] = content[1:]
        return line_dict

    def clipboard_copy(self) -> None:
        copy_data = self.full_copy_data()
        self.set_clipboard(copy_data)

    def clipboard_paste(self) -> None:
        """
        Use the clipboard to update fit state
        """
        # Check if the clipboard contains right stuff
        cb = QtWidgets.QApplication.clipboard()
        line_dict = serializer.parse_clipboard(cb.text())
        if line_dict is None:
            msg = "Clipboard content is incompatible with the Fit Page."
            msgbox = QtWidgets.QMessageBox(self)
            msgbox.setIcon(QtWidgets.QMessageBox.Warning)
            msgbox.setText(msg)
            msgbox.setWindowTitle("Clipboard")
            msgbox.exec_()
            return
        if self._confirmModelMismatch(line_dict):
            self.controller.paste(line_dict)

    def _confirmModelMismatch(self, line_dict: dict[str, list[str]]) -> bool:
        """Before anything changes: ask whether to apply parameters of another model (§2.3)."""
        if 'model_name' not in line_dict:
            return False
        if str(self.cbModel.currentText()) == str(line_dict['model_name'][0]):
            return True
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.setText("The model in the clipboard is not the same as the currently loaded model. \
                     Not all parameters saved may paste correctly.")
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
        return msg.exec_() == QtWidgets.QMessageBox.Ok

    def clipboard_copy_excel(self) -> None:
        self.set_clipboard(self.excel_copy_data())

    def clipboard_copy_latex(self) -> None:
        self.set_clipboard(self.latex_copy_data())

    def full_copy_data(self) -> str:
        """ Data destined for the clipboard when copy clicked"""
        param_list = self.getFitPage()
        param_list += self.getFitModel()
        return FittingUtilities.formatParameters(param_list)

    def excel_copy_data(self) -> str:
        """ Excel format data destined for the clipboard"""
        param_list = self.getFitParameters()
        return FittingUtilities.formatParametersExcel(param_list[1:])

    def latex_copy_data(self) -> str:
        """ Latex format data destined for the clipboard"""
        param_list = self.getFitParameters()
        return FittingUtilities.formatParametersLatex(param_list[1:])

    def save_parameters(self) -> None:
        """ Save parameters to a file"""
        param_list = self.getFitParameters()

        save_dialog = QtWidgets.QFileDialog()
        save_dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        parent = self
        caption = 'Save Project'
        filter = 'Text (*.txt);;Excel (*.xls);;Latex (*.log)'
        file_path = save_dialog.getSaveFileName(parent, caption, "", filter, "")
        filename = file_path[0]

        if not filename:
            return
        if file_path[1] == 'Text (*.txt)':
            save_data = FittingUtilities.formatParameters(param_list, line_sep="\n")
            filename = '.'.join((filename, 'txt'))
        elif file_path[1] == 'Excel (*.xls)':
            save_data = FittingUtilities.formatParametersExcel(param_list[1:])
            filename = '.'.join((filename, 'xls'))
        elif file_path[1] == 'Latex (*.log)':
            save_data = FittingUtilities.formatParametersLatex(param_list[1:])
            filename = '.'.join((filename, 'log'))
        else:
            raise ValueError(f"Unknown File Format {file_path[1]}")

        with open(filename, 'w') as file:
            file.write(save_data)

    def set_clipboard(self, data: str) -> None:
        """ Set the data in the clipboard """
        cb = QtWidgets.QApplication.clipboard()
        cb.setText(data)


    def getFitModel(self) -> list[list[str]]:
        """
        The legacy rows of the model selection
        """
        return serializer.fit_model_rows(self.document)

    def getFitPage(self) -> list[list[str]]:
        """
        serializes full state of this fit page
        """
        return serializer.fit_page_rows(self.document)

    def getFitParameters(self) -> list[list[str | tuple]]:
        """
        The legacy rows of the parameters
        """
        return serializer.fit_parameter_rows(self.document)

    def createPageForParameters(self, line_dict: dict[str, list[str]]) -> None:
        """
        Sets up page with requested model/str factor
        and fills it up with sent parameters (a project load: the history is cleared)
        """
        self.controller.load_selection(line_dict)
        if not self._confirmModelMismatch(line_dict):
            return
        mnemonic = self._loadedMnemonic(line_dict['tab_name'][0]) if 'tab_name' in line_dict else None
        self.controller.load_page(line_dict, mnemonic)
        if mnemonic is not None:
            # The constraint tab lists the pages by mnemonic
            self.newModelSignal.emit()

    def _loadedMnemonic(self, name: str) -> str:
        """The saved page name, or M<tab#> if another open page already uses it (R-3)."""
        others = [] if self.parent is None else self.parent.perspective().getFitTabs()
        if all(tab is self or tab.document.identity.mnemonic != name for tab in others):
            return name
        msg = f"Fit page name {name} is already in use, so this page is named {self.modelName()}."
        self.communicator.statusBarUpdateSignal.emit(msg)
        return self.modelName()

    @mirrors('data', 'options')
    def onMaskedData(self) -> None:
        """
        A mask has been applied to current data.
        Update the Q ranges.
        """
        self.updateQRange()
        self.updateData()

    def getCurrentFitState(self, state: Any | None = None) -> None:
        """
        Store current state for fit_page
        """
        serializer.page_state(self.document, state, self.logic.kernel_module, self.chi2)

    def getSymbolDict(self) -> dict[str, float]:
        """
        Return a dict containing a list of all the symbols used for fitting
        and their values, e.g. {'M1.scale':1, 'M1.background': 0.001}
        """
        return self.document.symbol_table()

