import contextlib
import copy
import logging
import re
import traceback
from pathlib import Path
from typing import Any

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets
from twisted.internet import threads

from sasmodels.sasview_model import SasviewModel

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas import config
from sas.qtgui.Perspectives.Fitting import FittingUtilities
from sas.qtgui.Perspectives.Fitting.ConsoleUpdate import ConsoleUpdate
from sas.qtgui.Perspectives.Fitting.Constraint import Constraint
from sas.qtgui.Perspectives.Fitting.controller import FitPageController
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
from sas.qtgui.Perspectives.Fitting.MagnetismWidget import MagnetismWidget
from sas.qtgui.Perspectives.Fitting.model import serializer
from sas.qtgui.Perspectives.Fitting.model.catalog import ModelCatalog
from sas.qtgui.Perspectives.Fitting.model.document import FitPageDocument
from sas.qtgui.Perspectives.Fitting.model.events import Origin
from sas.qtgui.Perspectives.Fitting.model.kernel import KernelBuilder
from sas.qtgui.Perspectives.Fitting.model.parameters import FitOptions, PageIdentity, PageMode, Smearing, Table
from sas.qtgui.Perspectives.Fitting.model.serializer import format_number
from sas.qtgui.Perspectives.Fitting.MultiConstraint import MultiConstraint
from sas.qtgui.Perspectives.Fitting.OptionsWidget import OptionsWidget
from sas.qtgui.Perspectives.Fitting.OrderWidget import OrderWidget
from sas.qtgui.Perspectives.Fitting.PolydispersityWidget import PolydispersityWidget
from sas.qtgui.Perspectives.Fitting.ReportPageLogic import ReportContext, ReportPageLogic
from sas.qtgui.Perspectives.Fitting.services import constraints as constraint_service
from sas.qtgui.Perspectives.Fitting.services.fit import FitService
from sas.qtgui.Perspectives.Fitting.services.theory import TheoryService
from sas.qtgui.Perspectives.Fitting.SmearingWidget import SmearingWidget
from sas.qtgui.Perspectives.Fitting.UI.FittingWidgetUI import Ui_FittingWidgetUI
from sas.qtgui.Perspectives.Fitting.view.ParameterItemModel import ParameterItemModel
from sas.qtgui.Perspectives.Fitting.view.PlotPublisher import PlotPublisher
from sas.qtgui.Perspectives.Fitting.view.SettingsSync import SettingsSync
from sas.qtgui.Perspectives.Fitting.ViewDelegate import ModelViewDelegate
from sas.qtgui.Perspectives.UndoRedo import UndoStack
from sas.qtgui.Plotting.Plotter import PlotterWidget
from sas.qtgui.Plotting.PlotterData import Data1D, Data2D, DataRole
from sas.qtgui.Utilities.BackgroundColor import BG_DEFAULT, BG_ERROR
from sas.sascalc.fit import models
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

# The parameter table of each tab that shows one
_TAB_TABLES = {0: Table.MAIN, TAB_POLY: Table.POLY, TAB_MAGNETISM: Table.MAGNET}


@contextlib.contextmanager
def _blocked(*widgets):
    """The widgets fire no signals: the page sets them up, nothing the user did."""
    for widget in widgets:
        widget.blockSignals(True)
    try:
        yield
    finally:
        for widget in widgets:
            widget.blockSignals(False)


class FittingWidget(QtWidgets.QWidget, Ui_FittingWidgetUI):
    """
    Main widget for selecting form and structure factor models
    """
    newModelSignal = QtCore.Signal()
    fittingFinishedSignal = QtCore.Signal(object, object)        # result, FitRequest
    batchFittingFinishedSignal = QtCore.Signal(object, object)   # result, FitRequest
    keyPressedSignal = QtCore.Signal(QtCore.QEvent)

    def __init__(self, parent: QtWidgets.QWidget | None = None, data: Any | None = None, tab_id: int = 1,
                 catalog: ModelCatalog | None = None) -> None:

        super(FittingWidget, self).__init__()

        # Necessary globals
        self.parent  = parent
        self.process = None    # Default empty value

        # Which tab is this widget displayed in?
        self.tab_id = tab_id

        # The models to choose from: the perspective's, or the page's own
        self._owns_catalog = catalog is None
        self.catalog = ModelCatalog(self.customModels) if catalog is None else catalog

        # Globals
        self.initializeGlobals()

        # The Qt-free page document, the engine instances built from it, and the jobs
        self.document = FitPageDocument(PageIdentity(page_id=tab_id, tab_id=tab_id))
        self.kernel_builder = KernelBuilder(self.catalog.models)
        self.theory_service = TheoryService(self.calcException, self.calculateDataFailed)
        self.fit_service = FitService(self.kernel_builder)
        # The intents; undo and redo replay document commands on the controller
        self.controller = FitPageController(self)
        self.undo_stack = UndoStack(self, target=self.controller, snapshot_fn=self.document.snapshot,
                                    restore_fn=lambda snapshot: self.controller.restore(snapshot, Origin.UNDO))
        self.plot_publisher = PlotPublisher(self)

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

        # New font to display angstrom symbol
        new_font = 'font-family: -apple-system, "Helvetica Neue", "Ubuntu";'
        self.label_17.setStyleSheet(new_font)
        self.label_19.setStyleSheet(new_font)

        # The document drives the settings widgets (the tables read it: initializeModels)
        self.settings_sync = SettingsSync(self)

        if data is not None:
            self.dataFromItems(data)

    @property
    def data(self) -> Data1D | Data2D | None:
        """The active dataset (the theory grid of a page without data)."""
        return self.document.data()

    @property
    def data_index(self) -> int:
        """The position of the active dataset among the page's datasets."""
        doc = self.document
        return doc.dataset_order.index(doc.active_id) if doc.is_loaded() else 0

    @property
    def coordinator(self):
        """The perspective's operations across fit pages (FitPerspectiveCoordinator)."""
        return self.parent.perspective().coordinator

    def kernel(self) -> Any | None:
        """A new engine instance with the document's effective state; None without a model."""
        return self.kernel_builder.build(self.document)

    def dataItem(self, dataset_id: str) -> QtGui.QStandardItem | None:
        """The Data Explorer item of a dataset; None for the theory grid."""
        order = self.document.dataset_order
        return self.all_data[order.index(dataset_id)] if self.all_data and dataset_id in order else None

    def dataFromItems(self, value: QtGui.QStandardItem | list[QtGui.QStandardItem]) -> None:
        """ The data to fit: a list of items for batch fitting, or one item. The layout follows is2D. """
        batch = isinstance(value, list)
        if not batch:
            value = [value]
        assert isinstance(value[0], QtGui.QStandardItem)
        # Keep reference to all datasets for batch
        self.all_data = value
        datasets = [GuiUtils.dataFromItem(item) for item in value]
        data = datasets[0]
        if len(value) > 1:
            # update the ordering tab
            self.order_widget.updateData(self.all_data)
        # The tabs offer what the data allows; setting them up is not the user's doing
        with _blocked(self.smearing_widget, self.options_widget, self.cbFileNames):
            self.smearing_widget.resetSmearer()
            if data.isSesans:
                self.onSesansData()
            self.setEnablementOnDataLoad(data, batch)
        smearing = Smearing(*self.smearing_widget.state())
        self.controller.set_datasets(datasets, batch, smearing)
        if not self.controller.relayout():
            # Same layout: what depends on the data
            self.onLayoutChanged()
            if len(self.document.parameters):
                self.updateData()
        # Reinitialize model list for constrained/simult fitting
        self.newModelSignal.emit()

    def initializeGlobals(self) -> None:
        """
        Initialize global variables used in this class
        """
        # Is the fit job running?
        self.fit_started = False
        # The current fit thread
        self.calc_fit = None
        # Utility variable to enable unselectable option in category combobox
        self._previous_category_index = 0

        self.all_data = []
        # Page id for fitting
        # To keep with previous SasView values, use 200 as the start offset
        self.page_id = 200 + self.tab_id

        self._previous_model_index = 0

        # Enablement of comboboxes
        self.enabled_cbmodel = False
        self.enabled_sfmodel = False

        # list column widths
        self.lstParamHeaderSizes = {}

        # signal communicator
        self.communicator = GuiUtils.communicator

    def initializeWidgets(self) -> None:
        """
        Initialize widgets for tabs
        """
        # Options widget
        layout = QtWidgets.QGridLayout()
        self.options_widget = OptionsWidget(self)
        layout.addWidget(self.options_widget)
        self.tabOptions.setLayout(layout)
        self.options_widget.setLogScale(self.document.options.log_points)

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
        # The three parameter tables read the document (ParameterItemModel)
        self.tables = {table: ParameterItemModel(self, table, view) for table, view in
                       ((Table.MAIN, self.lstParams), (Table.POLY, self.lstPoly), (Table.MAGNET, self.lstMagnetic))}
        self._model_model = self.tables[Table.MAIN]
        self.polydispersity_widget.poly_model = self.tables[Table.POLY]
        self.magnetism_widget._magnet_model = self.tables[Table.MAGNET]

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

        self.lstPoly.customContextMenuRequested.connect(self.showModelContextMenu)
        self.lstMagnetic.customContextMenuRequested.connect(self.showModelContextMenu)

        # Initial status of the ordering tab - invisible
        self.tabFitting.removeTab(TAB_ORDERING)

    def initializeCategoryCombo(self) -> None:
        """
        Model category combo setup
        """
        self.cbCategory.addItem(CATEGORY_DEFAULT)
        self.cbCategory.addItems(self.catalog.category_names())
        self.cbCategory.setCurrentIndex(0)

    def setEnablementOnDataLoad(self, data: Data1D | Data2D, batch: bool = False) -> None:
        """
        Enable/disable various UI elements for the data being loaded
        """
        # Tag along functionality
        self.label.setText("Data loaded from: ")
        self.lblFilename.setText(data.name if data.name else data.filename)
        # Switch off Data2D control
        self.chk2DView.setEnabled(False)
        self.chk2DView.setVisible(False)
        # Combo box or label for file name"
        if batch:
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
        self.options_widget.setEnablementOnDataLoad(data)
        # Smearing tab
        self.smearing_widget.updateData(data)

    def acceptsData(self) -> bool:
        """ Tells the caller this widget can accept new dataset """
        return not self.document.is_loaded()

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
        self.cmdFit.setEnabled(self.document.can_fit())
        self.updateData()

    def toggleMagnetism(self, isChecked: bool) -> None:
        """ The magnetism checkbox: an intent """
        self.controller.set_flag("magnetism", isChecked)

    def applyMagnetism(self, isChecked: bool) -> None:
        """ Enable/disable the magnetism tab (SettingsSync) """
        self.tabFitting.setTabEnabled(TAB_MAGNETISM, isChecked)
        # Check if any parameters are ready for fitting
        self.cmdFit.setEnabled(self.document.can_fit())

    def toggleChainFit(self, isChecked: bool) -> None:
        """ The chain-fit checkbox: an intent """
        self.controller.set_flag("chain_fit", isChecked)

    def applyChainFit(self, isChecked: bool) -> None:
        """ Show or hide the order tab of a chain fit (SettingsSync) """
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
        self.cmdPlot.setEnabled(len(params) > 0)
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
        self.smearing_widget.updateModel(has_model=len(params) > 0)
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
        self.cbModel.addItems(self.catalog.models_in(category))
        self.cbModel.blockSignals(False)
        self.enableModelCombo()
        self.disableStructureCombo()

    def otherSymbols(self) -> set[str]:
        """The constraint symbols of the other fit pages (retention keeps constraints that resolve)."""
        return set() if self.parent is None else set(self.coordinator.symbols(exclude=self))

    def keyAt(self, row: int, table: Table = Table.MAIN) -> str | None:
        """The document key of the parameter in *row* of *table*."""
        return self.tables[table].key_at(row)

    def _currentTable(self) -> ParameterItemModel:
        """The table of the tab shown."""
        return self.tables[_TAB_TABLES[self.tabFitting.currentIndex()]]

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
        options = self.document.options
        self.lblMinRangeDef.setText(GuiUtils.formatNumber(options.qmin, high=True))
        self.lblMaxRangeDef.setText(GuiUtils.formatNumber(options.qmax, high=True))
        self.options_widget.updateQRange(options.qmin, options.qmax, options.npts)

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

        # Signals from separate tabs asking for replot
        self.options_widget.plot_signal.connect(self.onOptionsUpdate)
        self.options_widget.txtMinRange.editingFinished.connect(self.options_widget.updateMinQ)
        self.options_widget.txtMaxRange.editingFinished.connect(self.options_widget.updateMaxQ)

        # Signals from other widgets
        self.communicator.customModelDirectoryChanged.connect(self.onCustomModelChange)
        self.smearing_widget.smearingChangedSignal.connect(self.onSmearingOptionsUpdate)
        self.polydispersity_widget.updateDataSignal.connect(lambda: self.updateData())
        self.polydispersity_widget.deletePlotSignal.connect(self.setPlotDeletable)
        self.magnetism_widget.updateDataSignal.connect(lambda: self.updateData())

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
        if self.document.is2D():
            name += "2d"
        name = f"{self.modelName()} [{name}]"
        return name

    def showModelContextMenu(self, position: QtCore.QPoint) -> None:
        """
        Show context specific menu in the parameter table.
        When clicked on parameter(s): fitting/constraints options
        When clicked on white space: model description
        """
        # See which table we're dealing with by looking at the tab
        model = self._currentTable()
        rows = self.selectedParameters(model.table)

        menu = self.showModelDescription() if not rows else self.modelContextMenu(rows)
        try:
            menu.exec_(model.view.viewport().mapToGlobal(position))
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
        model = self._currentTable()
        # Select for fitting
        param_string = "parameter " if num_rows == 1 else "parameters "
        to_string = "to its current value" if num_rows == 1 else "to their current values"
        constraints = [self.getConstraintForRow(i, model.table) for i in rows]
        has_constraints = any(c is not None for c in constraints)
        has_real_constraints = any(c is not None and c.active for c in constraints)

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
        self.actionMutualMultiConstrain.triggered.connect(lambda: self.showMultiConstraint(current_list=model.view))
        self.actionSelect.triggered.connect(self.selectParameters)
        self.actionDeselect.triggered.connect(self.deselectParameters)
        return menu

    def showMultiConstraint(self, current_list: QtWidgets.QTreeView | None = None) -> None:
        """
        Show the constraint widget for two selected parameters and add the constraint it returns.
        """
        current_list = self.lstParams if current_list is None else current_list
        selected_rows = current_list.selectionModel().selectedRows()
        # There have to be only two rows selected. The caller takes care of that.
        assert len(selected_rows) == 2
        params_list = [s.data() for s in selected_rows]
        mc_widget = MultiConstraint(self, params=params_list)
        if not any(constraint_service.is_polydisperse(self.document, p) for p in params_list):
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
        self.addConstraint(constraint)

    def addConstraint(self, constraint: Constraint) -> bool:
        """
        Put the constraint on its parameter, after the coordinator checked it against every page.
        An inconsistent constraint is reported and not added. Returns whether it was added.
        """
        key = constraint_service.key_for(self.document, constraint.param)
        assert key is not None and self.document.parameters[key].fittable
        if constraint.param.startswith("Distribution of "):
            constraint.param = key
        errors = self.coordinator.add_constraint(self, key, constraint)
        if errors:
            QtWidgets.QMessageBox.critical(self, "Inconsistent constraint", errors, QtWidgets.QMessageBox.Ok)
        return not errors

    def addSimpleConstraint(self) -> None:
        """
        Fix each selected parameter to its current value: an inactive constraint that keeps the
        bounds to restore, and bounds narrowed around the value (bumps needs a range).
        """
        table = self._currentTable().table
        params = self.document.parameters
        for row in self.selectedParameters(table):
            key = self.keyAt(row, table)
            p = params[key]
            constraint = Constraint(param=params.legacy_key(key), value=format_number(p.value),
                                    min=format_number(p.min), max=format_number(p.max))
            constraint.active = False
            self.controller.set_constraint(key, constraint, min=p.value - p.value / 10000.0,
                                           max=p.value + p.value / 10000.0)
        self.communicator.statusBarUpdateSignal.emit('Constraint added')

    def editConstraint(self) -> None:
        """
        Edit the constraint of the selected parameter.
        """
        model = self._currentTable()
        rows = self.selectedParameters(model.table)
        assert len(rows) == 1
        params_list = [model.index(rows[0], 0).data()]
        mc_widget = MultiConstraint(self, params=params_list, constraint=self.getConstraintForRow(rows[0], model.table))
        if not any(constraint_service.is_polydisperse(self.document, p) for p in params_list):
            mc_widget.lblWarning.setText("")
        if mc_widget.exec_() != QtWidgets.QDialog.Accepted:
            return
        param_used = mc_widget.params[1]
        constraint = Constraint(param=mc_widget.params[0], value=param_used, func=mc_widget.txtConstraint.text(),
                                value_ex=f"{self.document.identity.mnemonic}.{param_used}")
        constraint.validate = mc_widget.validate
        self.addConstraint(constraint)

    def deleteConstraint(self) -> None:
        """
        Delete the constraints of the selected parameters.
        """
        table = self._currentTable().table
        for row in self.selectedParameters(table):
            self.controller.remove_constraint(self.keyAt(row, table))

    def getConstraintForRow(self, row: int, table: Table = Table.MAIN) -> Constraint | None:
        """
        The constraint of the parameter in *row*, if any
        """
        key = self.keyAt(row, table)
        if key is None or not self.document.parameters[key].fittable:
            return None
        return self.document.parameters[key].constraint

    def selectParameters(self) -> None:
        """
        The selected parameters are fitted (the context menu)
        """
        self.setFitForSelection(True, self._currentTable().table)

    def deselectParameters(self) -> None:
        """
        The selected parameters are not fitted
        """
        self.setFitForSelection(False, self._currentTable().table)

    def selectedParameters(self, table: Table = Table.MAIN) -> list[int]:
        """ Returns list of selected (highlighted) parameters """
        return [s.row() for s in self.tables[table].view.selectionModel().selectedRows()
                if self.isCheckable(s.row(), table)]

    def setFitForSelection(self, fit: bool, table: Table = Table.MAIN) -> None:
        """
        Every selected parameter of *table* is fitted, or not (checking one of several selected
        rows checks them all, https://github.com/SasView/sasview/issues/1676)
        """
        for row in self.selectedParameters(table):
            self.controller.set_fit_flag(self.keyAt(row, table), fit)

    def getConstraintsForFitting(self) -> list[tuple[str, str]]:
        """
        The constraints of a single-page fit. Constraints that refer to other pages are
        deactivated if the user agrees; otherwise the fit is cancelled (ValueError).
        """
        constraints = constraint_service.complex_constraints(self.document)
        multi_constraints = [cons for cons in constraints if constraint_service.is_multimodel(self.document, cons[1])]
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
        # (the constraint tab follows the documents)
        for key, _ in multi_constraints:
            self.controller.set_constraint_active(key, False)
        return constraint_service.complex_constraints(self.document)

    def showModelDescription(self) -> QtWidgets.QMenu:
        """
        Creates a window with model description, when right-clicked in the treeview
        """
        msg = 'Model description:\n'
        kernel = self.kernel()
        if kernel is not None:
            if str(kernel.description).rstrip().lstrip() == '':
                msg += "Sorry, no information is available for this model."
            else:
                msg += kernel.description + '\n'
        else:
            msg += "You must select a model to get information on this"

        menu = QtWidgets.QMenu()
        label = QtWidgets.QLabel(msg)
        action = QtWidgets.QWidgetAction(self)
        action.setDefaultWidget(label)
        menu.addAction(action)
        return menu

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

    def onSelectBatchFilename(self, data_index: int) -> None:
        """
        Another file of the batch is shown: an intent
        """
        order = self.document.dataset_order
        if 0 <= data_index < len(order):
            self.controller.set_active_dataset(order[data_index])

    def onSelectStructureFactor(self) -> None:
        """
        The structure-factor combo box: an intent
        """
        category = self.cbCategory.currentText()
        model = "" if category == CATEGORY_STRUCTURE else self.cbModel.currentText()
        self.controller.select_model(category, model, self.cbStructureFactor.currentText(), "Select structure factor")

    def onCustomModelChange(self) -> None:
        """
        The plugin directory changed: the catalog reloads (the perspective's does it for its pages)
        """
        if self._owns_catalog:
            self.catalog.reload_plugins()
        self.onCategoriesChanged(refresh=False)
        # See if we need to update the combo in-place
        if self.cbCategory.currentText() != CATEGORY_CUSTOM:
            return
        current_text = self.cbModel.currentText()
        self._populateCategory(CATEGORY_CUSTOM)
        new_index = self.cbModel.findText(current_text)
        if new_index != -1:
            self.cbModel.blockSignals(True)
            self.cbModel.setCurrentIndex(new_index)
            self.cbModel.blockSignals(False)

    def onSelectionChanged(self) -> None:
        """
        React to parameter selection
        """
        rows = self.lstParams.selectionModel().selectedRows()
        # Clean previous messages
        self.communicator.statusBarUpdateSignal.emit("")
        if len(rows) == 1:
            # Show constraint, if present
            constr = self.getConstraintForRow(rows[0].row())
            if constr is None:
                return
            if constr.func is not None:
                # inter-parameter constraint
                update_text = "Active constraint: " + constr.func
            elif constr.param == rows[0].data():
                # current value constraint
                update_text = "Value constrained to: " + str(constr.value)
            else:
                # ill defined constraint
                return
            self.communicator.statusBarUpdateSignal.emit(update_text)

    def onSesansData(self) -> None:
        """
        Updates the fitting widget format when SESANS data is loaded.
        """
        # update the units in the 'Fitting details' box of the Model tab on the Fit Panel
        self.label_17.setText("Å")
        self.label_19.setText("Å")
        # The background is fixed at 0 for SESANS by the document's rules, the Q range is the data's
        # update the units in the 'Fitting details' box of the Fit Options tab on the Fit Panel
        self.options_widget.label_13.setText("Å")
        self.options_widget.label_15.setText("Å")
        # update the smearing drop down box to indicate a Hankel Transform is being used instead of resolution
        self.smearing_widget.onIndexChange(1)
        # update the Weighting box of the Fit Options tab on the Fit Panel
        self.options_widget.rbWeighting2.setText("Use dP Data")
        self.options_widget.rbWeighting3.setText("Use |sqrt(P Data)|")
        self.options_widget.rbWeighting4.setText("Use |P Data|")

    def updateData(self) -> None:
        """
        Helper function for recalculation of data used in plotting
        """
        # Update the chart
        if self.document.is_loaded():
            self.cmdPlot.setText("Compute/Plot")
            self.controller.compute_theory()
        else:
            self.cmdPlot.setText("Calculate")
            # The theory grid, if no data passed
            self.controller.ensure_default_dataset()
            # ensure theory is recalc. before plot, see showTheoryPlot()
            self.plot_publisher.theory_item = None

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
                plugin_names = [name for name, enabled in self.catalog.categories.get(CATEGORY_CUSTOM, {})]
                kernel = self.kernel()
                if (kernel is not None
                        and hasattr(kernel, 'name')
                        and kernel.id not in plugin_names
                        and not re.match("[A-Za-z0-9_-]+[+*@][A-Za-z0-9_-]+", kernel.id)):
                    tree_location = tree_base / "user" / "models"
                    return tree_location / f"{kernel.id}.html"
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

        chain = self.document.flags.chain_fit
        if chain:
            order = self.document.dataset_order
            self.controller.set_chain_order([order[self.all_data.index(item)] for item in self.order_widget.ordering()])

        # Prepare the fitter object
        try:
            request = self.controller.start_fit()
        except ValueError as ex:
            # This should not happen! GUI explicitly forbids this situation
            self.communicator.statusBarUpdateSignal.emit(str(ex))
            return

        # Create the fitting thread, based on the fitter; the completion comes back with its request
        batch = self.document.mode is PageMode.BATCH
        finished = self.batchFittingFinishedSignal if batch else self.fittingFinishedSignal
        def completefn(result):
            finished.emit(tuple() if result is None else result, request)

        self.calc_fit = FitThread(handler=handler,
                                  fn=list(request.fitters),
                                  batch_inputs=batch_inputs,
                                  batch_outputs=batch_outputs,
                                  page_id=[[self.page_id]],
                                  updatefn=updater,
                                  completefn=completefn,
                                  reset_flag=chain)

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

    def fitFailed(self, reason: Any) -> None:
        """
        """
        self.controller.fit_failed()
        self.enableInteractiveElements()
        msg = "Fitting failed with: "+ str(reason)
        self.communicator.statusBarUpdateSignal.emit(msg)

    def batchFitComplete(self, result: tuple, request: Any | None = None) -> None:
        """
        Receive and display batch fitting results; each dataset's theory is computed with its values
        """
        accepted = self.controller.fit_done(request)
        if accepted is None:
            return
        #re-enable the Fit button
        self.enableInteractiveElements()
        if not accepted:
            return

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

        self.controller.apply_batch_fit(result[0])

    def fitComplete(self, result: tuple, request: Any | None = None) -> None:
        """
        Receive and display fitting results
        "result" is a tuple of actual result list and the fit time in seconds; *request* the
        page's fit it completes (None: a fit the constraint tab routed here)
        """
        accepted = self.controller.fit_done(request)
        if accepted is None:
            return
        #re-enable the Fit button
        self.enableInteractiveElements()
        if not accepted:
            return

        if not result or not result[0] or not result[0][0]:
            msg = "Fitting failed."
            self.communicator.statusBarUpdateSignal.emit(msg)
            return

        res = result[0][0][0]
        param_dict = self.controller.outcome(res)

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
        # e.g. param_dic = {"sld":(1.703, 0.0034), "length":(33.455, -0.0983)}: one undoable step.
        # Its chi2 (in res.fitness) is shown until the parameters change.
        self.controller.apply_fit(param_dict, res.fitness)

        # Clean up polydispersity plots if polydispersity has been disabled
        if not self.chkPolydispersity.isChecked():
            self.preparePlotsForDeletion(DataRole.ROLE_POLYDISPERSITY)

        # update charts
        self.onPlot()

        # Read only value - we can get away by just printing it here
        self.lblChi2Value.setText(GuiUtils.formatNumber(res.fitness, high=True))

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

    def onPlot(self) -> None:
        """
        Plot the current set of data
        """
        # Regardless of previous state, this should now be `plot show` functionality only
        self.cmdPlot.setText("Compute/Plot")
        # Force data recalculation so existing charts are updated
        if not self.document.is_loaded():
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
        if not self.document.is_loaded():
            self.controller.ensure_default_dataset()
            self.smearing_widget.updateData(self.data)
        self.controller.compute_theory()

    def showTheoryPlot(self) -> None:
        """
        Show the current theory plot in MPL
        """
        # Show the chart if ready
        publisher = self.plot_publisher
        if publisher.theory_item is None:
            self.recalculatePlotData()
        elif publisher.model_data:
            self._requestPlots(publisher.model_data.name, publisher.theory_item.model())

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
        fitpage_name = self.document.identity.mnemonic
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
        qmin, qmax, npts, log_points, weighting = self.options_widget.state()
        # set Q range labels on the main tab
        self.lblMinRangeDef.setText(GuiUtils.formatNumber(qmin, high=True))
        self.lblMaxRangeDef.setText(GuiUtils.formatNumber(qmax, high=True))
        self.controller.set_options(FitOptions(qmin, qmax, npts, log_points, weighting, self.options_widget.weighting))

    def setDefaultStructureCombo(self) -> None:
        """
        Fill in the structure factors combo box with defaults (only those that can be loaded)
        """
        self.cbStructureFactor.clear()
        self.cbStructureFactor.addItems(sorted([STRUCTURE_DEFAULT] + self.catalog.structure_factors()))

    def isCheckable(self, row: int, table: Table = Table.MAIN) -> bool:
        model = self.tables[table]
        return bool(model.flags(model.index(row, 0)) & QtCore.Qt.ItemIsUserCheckable)

    def setTheoryItem(self, item: Any) -> None:
        """
        Reset the theory item based on the data explorer update
        """
        self.plot_publisher.theory_item = item

    def showTheory(self, result: Any) -> None:
        """
        A theory result the controller accepted: chi² (a fit's, until the parameters change) and the plots
        """
        if self.document.is_loaded():
            chi2 = self.controller.chi2()
            self.lblChi2Value.setText("---" if chi2 is None else GuiUtils.formatNumber(chi2, high=True))
        self.plot_publisher.publish(result)

    def calculateDataFailed(self, reason: Any) -> None:
        """
        Thread returned error
        """
        # Bring the GUI to normal state
        self.enableInteractiveElements()
        print("Calculate Data failed with ", reason)

    def onCategoriesChanged(self, refresh: bool = True) -> None:
            """
            Reload the category/model comboboxes (the catalog re-reads the categories first)
            """
            if refresh and self._owns_catalog:
                self.catalog.refresh()
            # Store the current combo indices
            current_cat = self.cbCategory.currentText()
            current_model = self.cbModel.currentText()

            # repopulate the combo
            self.cbCategory.blockSignals(True)
            self.cbCategory.clear()
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
            x, y = self.kernel().getProfile()
        except (TypeError, AttributeError):
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

    def getReport(self) -> list[str]:
        """
        Create and return HTML report with parameters and charts
        """
        return ReportPageLogic(self.reportContext()).reportList()

    def reportContext(self) -> ReportContext:
        """What the report shows, from the document (§3.6.4)."""
        doc = self.document
        kernel = self.kernel()
        smearing = doc.smearing
        active = doc.datasets.get(doc.active_id) if doc.active_id else None
        return ReportContext(
            model_id=None if kernel is None else kernel.id,
            mnemonic=doc.identity.mnemonic,
            data=self.data,
            params=serializer.report_parameters(doc),
            dispersions={p.key[:-len(".width")]: p.dispersion.type for p in doc.parameters.by_table(Table.POLY)},
            qmin=doc.options.qmin, qmax=doc.options.qmax,
            chi2=self.controller.chi2(),
            smearing=(smearing.mode, smearing.accuracy, smearing.d_down, smearing.d_up),
            resolution=None if active is None else active.resolution,
            is_batch=doc.mode is PageMode.BATCH,
            index=self.all_data[self.data_index] if self.all_data else self.plot_publisher.theory_item,
            results_panel=getattr(self.parent, 'results_panel', None),
            grid_window=getattr(self.parent, 'grid_window', None))

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
        param_list = serializer.fit_parameter_rows(self.document)
        return FittingUtilities.formatParametersExcel(param_list[1:])

    def latex_copy_data(self) -> str:
        """ Latex format data destined for the clipboard"""
        param_list = serializer.fit_parameter_rows(self.document)
        return FittingUtilities.formatParametersLatex(param_list[1:])

    def save_parameters(self) -> None:
        """ Save parameters to a file"""
        param_list = serializer.fit_parameter_rows(self.document)

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
        if self.parent is None or self.coordinator.check_name(self, name) is None:
            return name
        msg = f"Fit page name {name} is already in use, so this page is named {self.modelName()}."
        self.communicator.statusBarUpdateSignal.emit(msg)
        return self.modelName()

    def onMaskedData(self) -> None:
        """
        A mask has been applied to current data: an intent (the Q range follows)
        """
        self.controller.data_masked()

    def getCurrentFitState(self, state: Any | None = None) -> None:
        """
        Store current state for fit_page
        """
        serializer.page_state(self.document, state, self.kernel(), self.controller.chi2())
