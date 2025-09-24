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

from sasmodels import generate, modelinfo
from sasmodels.sasview_model import MultiplicationModel, SasviewModel, load_standard_models

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas import config
from sas.qtgui.Perspectives.Fitting import FittingUtilities
from sas.qtgui.Perspectives.Fitting.ConsoleUpdate import ConsoleUpdate
from sas.qtgui.Perspectives.Fitting.Constraint import Constraint
from sas.qtgui.Perspectives.Fitting.FitPage import FitPage
from sas.qtgui.Perspectives.Fitting.FitThread import FitThread
from sas.qtgui.Perspectives.Fitting.FittingLogic import FittingLogic
from sas.qtgui.Perspectives.Fitting.MagnetismWidget import MagnetismWidget
from sas.qtgui.Perspectives.Fitting.ModelThread import Calc1D, Calc2D
from sas.qtgui.Perspectives.Fitting.MultiConstraint import MultiConstraint
from sas.qtgui.Perspectives.Fitting.OptionsWidget import OptionsWidget
from sas.qtgui.Perspectives.Fitting.OrderWidget import OrderWidget
from sas.qtgui.Perspectives.Fitting.PolydispersityWidget import PolydispersityWidget
from sas.qtgui.Perspectives.Fitting.ReportPageLogic import ReportPageLogic
from sas.qtgui.Perspectives.Fitting.SmearingWidget import SmearingWidget
from sas.qtgui.Perspectives.Fitting.UI.FittingWidgetUI import Ui_FittingWidgetUI
from sas.qtgui.Perspectives.Fitting.ViewDelegate import ModelViewDelegate
from sas.qtgui.Plotting.Plotter import PlotterWidget
from sas.qtgui.Plotting.PlotterData import Data1D, Data2D, DataRole
from sas.qtgui.Utilities.CategoryInstaller import CategoryInstaller
from sas.sascalc.fit import models
from sas.sascalc.fit.BumpsFitting import BumpsFit as Fit
from sas.system.user import HELP_DIRECTORY_LOCATION

TAB_MAGNETISM = 4
TAB_POLY = 3
TAB_ORDERING = 5
CATEGORY_DEFAULT = "Choose category..."
MODEL_DEFAULT = "Choose model..."
CATEGORY_STRUCTURE = "Structure Factor"
CATEGORY_CUSTOM = "Plugin Models"
STRUCTURE_DEFAULT = "None"

DEFAULT_POLYDISP_FUNCTION = 'gaussian'

# A list of models that are known to not work with how the GUI handles models from sasmodels
#   NOTE: These models are correct when used directly through the sasmodels package, but how qtgui handles them is wrong
SUPPRESSED_MODELS = ['rpa']
# Layered models that have integer parameters are often treated differently. Maintain a list of these models.
LAYERED_MODELS = ['unified_power_Rg', 'core_multi_shell', 'onion', 'spherical_sld']

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

    MAGNETIC_MODELS = ['sphere', 'core_shell_sphere', 'core_multi_shell', 'cylinder', 'parallelepiped']

    def __init__(self, parent: QtWidgets.QWidget | None = None, data: Any | None = None, tab_id: int = 1) -> None:

        super(FittingWidget, self).__init__()

        # Necessary globals
        self.parent  = parent
        self.process = None    # Default empty value

        # Which tab is this widget displayed in?
        self.tab_id = tab_id

        import sys
        sys.excepthook = self.info

        # Globals
        self.initializeGlobals()

        # data index for the batch set
        self.data_index = 0
        # Main Data[12]D holders
        # Logics.data contains a single Data1D/Data2D object
        self._logic = [FittingLogic()]

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

    def info(self, type: Any, value: Any, tb: Any) -> None:
        logger.error("".join(traceback.format_exception(type, value, tb)))

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
        """ data setter """
        # Value is either a list of indices for batch fitting or a simple index
        # for standard fitting. Assure we have a list, regardless.
        if isinstance(value, list):
            self.is_batch_fitting = True
        else:
            value = [value]

        assert isinstance(value[0], QtGui.QStandardItem)

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
            # update the ordering tab
            self.order_widget.updateData(self.all_data)

        # Overwrite data type descriptor
        self.is2D = True if isinstance(self.logic.data, Data2D) else False

        # Let others know we're full of data now
        self.data_is_loaded = True
        # Reset the smearer
        self.smearing_widget.resetSmearer()
        if self.data.isSesans:
            self.onSesansData()

        # Enable/disable UI components
        self.setEnablementOnDataLoad()
        # Reinitialize model list for constrained/simult fitting
        self.newModelSignal.emit()

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
        # Current SasModel is multishell
        self.model_has_shells = False
        # Utility variable to enable unselectable option in category combobox
        self._previous_category_index = 0
        # Utility variables for multishell display
        self._n_shells_row = -1
        self._num_shell_params = -1
        # Dictionary of {model name: model class} for the current category
        self.models = {}
        # Dictionary of QModels
        self.model_dict = {}
        self.lst_dict = {}
        self.tabToList = {} # tab_id -> list widget
        self.tabToKey = {} # tab_id -> model key

        # Parameters to fit
        self.main_params_to_fit = []

        # Fit options
        self.q_range_min = OptionsWidget.QMIN_DEFAULT
        self.q_range_max = OptionsWidget.QMAX_DEFAULT
        self.npts = OptionsWidget.NPTS_DEFAULT
        self.log_points = True
        self.weighting = 0
        self.chi2 = None

        # Does the control support UNDO/REDO
        # temporarily off
        self.undo_supported = False
        self.page_stack = []
        self.all_data = []
        # custom plugin models
        # {model.name:model}
        self.custom_models = self.customModels()
        # copy of current kernel model
        self.kernel_module_copy = None

        # dictionaries of current params
        self.magnet_params = {}

        # Page id for fitting
        # To keep with previous SasView values, use 200 as the start offset
        self.page_id = 200 + self.tab_id

        # Data for chosen model
        self.model_data = None
        self._previous_model_index = 0

        # List of all shell-unique parameters
        self.shell_names = []

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
        self.page_parameters = None

        # signal communicator
        self.communicate = self.parent.communicate

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

        # Poly model displayed in poly list
        self.polydispersity_widget.setPolyModel()
        self.lstPoly.customContextMenuRequested.connect(self.showModelContextMenu)

        # Magnetism model displayed in magnetism list
        self.magnetism_widget.setMagneticModel()

        # Initial status of the ordering tab - invisible
        self.tabFitting.removeTab(TAB_ORDERING)

    def initializeCategoryCombo(self) -> None:
        """
        Model category combo setup
        """
        category_list = sorted(self.master_category_dict.keys())
        self.cbCategory.addItem(CATEGORY_DEFAULT)
        self.cbCategory.addItems(category_list)
        if CATEGORY_STRUCTURE not in category_list:
            self.cbCategory.addItem(CATEGORY_STRUCTURE)
        self.cbCategory.setCurrentIndex(0)

    def setEnablementOnDataLoad(self) -> None:
        """
        Enable/disable various UI elements based on data loaded
        """
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
        self.onSelectModel()
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

    def enableBackgroundParameter(self, set_value: float | None = None) -> None:
        """ Enable the background parameter. Optionally set at a specified value. """
        background_row = self.getRowFromName("background")
        if background_row is not None:
            self.setParamEditableByRow(background_row, True)
            if set_value is not None:
                self._model_model.item(background_row, 1).setText(GuiUtils.formatNumber(set_value, high=True))

    def disableBackgroundParameter(self, set_value: float | None = None) -> None:
        """ Disable the background parameter. Optionally set at a specified value. """
        background_row = self.getRowFromName("background")
        if background_row is not None:
            self.setParamEditableByRow(background_row, False)
            if set_value is not None:
                self._model_model.item(background_row, 1).setText(GuiUtils.formatNumber(set_value, high=True))

    def enableStructureCombo(self) -> None:
        """ Enable the combobox """
        self.cbStructureFactor.setEnabled(True)
        self.lblStructure.setEnabled(True)
        self.enabled_sfmodel = True

    def togglePoly(self, isChecked: bool) -> None:
        """ Enable/disable the polydispersity tab """
        self.tabFitting.setTabEnabled(TAB_POLY, isChecked)
        # Check if any parameters are ready for fitting
        self.cmdFit.setEnabled(self.haveParamsToFit())
        self.polydispersity_widget.togglePoly(isChecked)

    def toggleMagnetism(self, isChecked: bool) -> None:
        """ Enable/disable the magnetism tab """
        self.tabFitting.setTabEnabled(TAB_MAGNETISM, isChecked)
        # Check if any parameters are ready for fitting
        self.cmdFit.setEnabled(self.haveParamsToFit())
        self.magnetism_widget.isActive = isChecked

    def toggleChainFit(self, isChecked: bool) -> None:
        """ Enable/disable chain fitting """
        self.is_chain_fitting = isChecked
        # show/hide the ordering tab
        if isChecked:
            self.tabFitting.insertTab(TAB_ORDERING, self.tabOrder, "Order")
        else:
            self.tabFitting.removeTab(TAB_ORDERING)

    def toggle2D(self, isChecked: bool) -> None:
        """ Enable/disable the controls dependent on 1D/2D data instance """
        self.chkMagnetism.setEnabled(isChecked)
        self.is2D = isChecked
        # Reload the current model
        if self.logic.kernel_module:
            self.onSelectModel()

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

        # Respond to change in parameters from the UI
        self._model_model.dataChanged.connect(self.onMainParamsChange)
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
        self.communicate.customModelDirectoryChanged.connect(self.onCustomModelChange)
        self.smearing_widget.smearingChangedSignal.connect(self.onSmearingOptionsUpdate)
        self.polydispersity_widget.cmdFitSignal.connect(lambda: self.cmdFit.setEnabled(self.haveParamsToFit()))
        self.polydispersity_widget.updateDataSignal.connect(lambda: self.updateData())
        self.polydispersity_widget.iterateOverModelSignal.connect(lambda: self.iterateOverModel(self.updateFunctionCaption))
        self.magnetism_widget.cmdFitSignal.connect(lambda: self.cmdFit.setEnabled(self.haveParamsToFit()))
        self.magnetism_widget.updateDataSignal.connect(lambda: self.updateData())

        # Communicator signal
        self.communicate.updateModelCategoriesSignal.connect(self.onCategoriesChanged)
        self.communicate.updateMaskedDataSignal.connect(self.onMaskedData)

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
        return "M%i" % self.tab_id

    def nameForFittedData(self, name: str) -> str:
        """
        Generate name for the current fit
        """
        if self.is2D:
            name += "2d"
        name = "%s [%s]" % (self.modelName(), name)
        return name

    def showModelContextMenu(self, position: QtCore.QPoint) -> None:
        """
        Show context specific menu in the parameter table.
        When clicked on parameter(s): fitting/constraints options
        When clicked on white space: model description
        """
        # See which model we're dealing with by looking at the tab id
        current_list = self.tabToList[self.tabFitting.currentIndex()]
        rows = [s.row() for s in current_list.selectionModel().selectedRows()
                if self.isCheckable(s.row())]

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
        Show the constraint widget and receive the expression
        """
        if current_list is None:
            current_list = self.lstParams
        model = current_list.model()
        for key, val in self.model_dict.items():
            if val == model:
                model_key = key

        selected_rows = current_list.selectionModel().selectedRows()
        # There have to be only two rows selected. The caller takes care of that
        # but let's check the correctness.
        assert len(selected_rows) == 2

        params_list = [s.data() for s in selected_rows]
        # Create and display the widget for param1 and param2
        mc_widget = MultiConstraint(self, params=params_list)
        # Check if any of the parameters are polydisperse
        if not np.any([FittingUtilities.isParamPolydisperse(p, self.logic.model_parameters, is2D=self.is2D) for p in params_list]):
            # no parameters are pd - reset the text to not show the warning
            mc_widget.lblWarning.setText("")
        if mc_widget.exec_() != QtWidgets.QDialog.Accepted:
            return

        constraint = Constraint()
        c_text = mc_widget.txtConstraint.text()

        # widget.params[0] is the parameter we're constraining
        constraint.param = mc_widget.params[0]
        # parameter should have the model name preamble
        model_name = self.logic.kernel_module.name
        # param_used is the parameter we're using in constraining function
        param_used = mc_widget.params[1]
        # Replace param_used with model_name.param_used
        updated_param_used = model_name + "." + param_used
        new_func = c_text.replace(param_used, updated_param_used)
        constraint.func = new_func
        constraint.value_ex = updated_param_used
        # Which row is the constrained parameter in?
        row = self.getRowFromName(constraint.param)

        # what is the parameter to constraint to?
        constraint.value = param_used

        # Should the new constraint be validated?
        constraint.validate = mc_widget.validate

        # Create a new item and add the Constraint object as a child
        self.addConstraintToRow(constraint=constraint, row=row, model_key=model_key)

    def getModelKeyFromName(self, name: str) -> str:
        """
        Given parameter name, get the model index.
        """
        if name in self.getParamNamesMain():
            return "standard"
        elif name in self.polydispersity_widget.getParamNamesPoly():
            return "poly"
        elif name in self.getParamNamesMagnet():
            return "magnet"
        else:
            return "standard"

    def getRowFromName(self, name: str) -> int | None:
        """
        Given parameter name, get the row number in a model.
        The model is the main _model_model by default
        """
        model_key = self.getModelKeyFromName(name)
        model = self.model_dict[model_key]

        for row in range(model.rowCount()):
            row_name = model.item(row).text()
            if model_key == 'poly':
                row_name = self.polydispersity_widget.polyNameToParam(row_name)
            if row_name == name:
                return row
        return None

    def getParamNames(self) -> list[str]:
        """
        Return list of all active parameters for the current model
        """
        main_model_params = self.getParamNamesMain()
        poly_model_params = self.polydispersity_widget.getParamNamesPoly()
        # magnet_model_params = self.getParamNamesMagnet()
        return main_model_params  + poly_model_params # + magnet_model_params

    def getParamNamesMain(self) -> list[str]:
        """
        Return list of main parameters for the current model
        """
        main_model_params = [self._model_model.item(row).text()
                            for row in range(self._model_model.rowCount())
                            if self.isCheckable(row, model_key="standard")]
        return main_model_params

    def getParamNamesMagnet(self) -> list[str]:
        """
        Return list of magnetic parameters for the current model
        """
        if not self.chkMagnetism.isChecked():
            return []
        return self.magnetism_widget.getParamNamesMagnet()

    def modifyViewOnRow(self, row: int, font: QtGui.QFont | None = None, brush: QtGui.QBrush | None = None, model_key: str = "standard") -> None:
        """
        Change how the given row of the main model is shown
        """
        model = self.model_dict[model_key]
        fields_enabled = False
        if font is None:
            font = QtGui.QFont()
            fields_enabled = True
        if brush is None:
            brush = QtGui.QBrush()
            fields_enabled = True
        model.blockSignals(True)
        # Modify font and foreground of affected rows
        for column in range(0, model.columnCount()):
            model.item(row, column).setForeground(brush)
            model.item(row, column).setFont(font)
            # Allow the user to interact or not with the fields depending on
            # whether the parameter is constrained or not
            model.item(row, column).setEditable(fields_enabled)
        # Force checkbox selection when parameter is constrained and disable
        # checkbox interaction
        if not fields_enabled and model.item(row, 0).isCheckable():
            model.item(row, 0).setCheckState(QtCore.Qt.Checked)
            model.item(row, 0).setEnabled(False)
        else:
            # Enable checkbox interaction
            model.item(row, 0).setEnabled(True)
        model.blockSignals(False)

    def getModelKey(self, constraint: Constraint) -> str | None:
        """
        Given parameter name get the model index.
        """
        if constraint.param in self.getParamNamesMain():
            return "standard"
        elif constraint.param in self.polydispersity_widget.getParamNamesPoly():
            return "poly"
        elif constraint.param in self.getParamNamesMagnet():
            return "magnet"
        else:
            return None

    def addConstraintToRow(self, constraint: Constraint | None = None, row: int = 0, model_key: str = "standard") -> None:
        """
        Adds the constraint object to requested row. The constraint is first
        checked for errors, and a  message box interrupting flow is
        displayed, with the reason of the failure.
        """
        # Create a new item and add the Constraint object as a child
        assert isinstance(constraint, Constraint)
        model = self.model_dict[model_key]
        assert 0 <= row <= model.rowCount()
        assert self.isCheckable(row, model_key=model_key)

        # Error checking
        # First, get a list of constraints and symbols
        constraint_list = self.parent.perspective().getActiveConstraintList()
        symbol_dict = self.parent.perspective().getSymbolDictForConstraints()
        if model_key == 'poly' and 'Distribution' in constraint.param:
            constraint.param = self.polydispersity_widget.polyNameToParam(constraint.param)
        constraint_list.append((self.modelName() + '.' + constraint.param,
                                constraint.func))
        # Call the error checking function
        errors = FittingUtilities.checkConstraints(symbol_dict, constraint_list)
        # get the constraint tab
        constraint_tab = self.parent.perspective().getConstraintTab()
        if errors:
            # Display the message box
            QtWidgets.QMessageBox.critical(
                self,
                "Inconsistent constraint",
                errors,
                QtWidgets.QMessageBox.Ok)
            # Check if there is a constraint tab
            if constraint_tab:
                # Set the constraint_accepted flag to False to inform the
                # constraint tab that the constraint was not accepted
                constraint_tab.constraint_accepted = False
            return

        item = QtGui.QStandardItem()
        item.setData(constraint)
        model.item(row, 1).setChild(0, item)
        # Set min/max to the value constrained
        self.constraintAddedSignal.emit([row], model_key)
        # Show visual hints for the constraint
        font = QtGui.QFont()
        font.setItalic(True)
        brush = QtGui.QBrush(QtGui.QColor('blue'))
        self.modifyViewOnRow(row, font=font, brush=brush, model_key=model_key)
        # update the main parameter list so the constrained parameter gets
        # updated when fitting
        self.checkboxSelected(model.item(row, 0), model_key=model_key)
        self.communicate.statusBarUpdateSignal.emit('Constraint added')
        if constraint_tab:
            # Set the constraint_accepted flag to True to inform the
            # constraint tab that the constraint was accepted
            constraint_tab.constraint_accepted = True

    def addSimpleConstraint(self) -> None:
        """
        Adds a constraint on a single parameter.
        """
        model_key = self.tabToKey[self.tabFitting.currentIndex()]
        model = self.model_dict[model_key]
        min_col = self.lstParams.itemDelegate().param_min
        max_col = self.lstParams.itemDelegate().param_max
        for row in self.selectedParameters(model_key=model_key):
            param = model.item(row, 0).text()
            value = model.item(row, 1).text()
            min_t = model.item(row, min_col).text()
            max_t = model.item(row, max_col).text()
            # Create a Constraint object
            constraint = Constraint(param=param, value=value, min=min_t, max=max_t)
            constraint.active = False
            # Create a new item and add the Constraint object as a child
            item = QtGui.QStandardItem()
            item.setData(constraint)
            model.item(row, 1).setChild(0, item)
            # Assumed correctness from the validator
            value = float(value)
            # BUMPS calculates log(max-min) without any checks, so let's assign minor range
            min_v = value - (value/10000.0)
            max_v = value + (value/10000.0)
            # Set min/max to the value constrained
            model.item(row, min_col).setText(str(min_v))
            model.item(row, max_col).setText(str(max_v))
            self.constraintAddedSignal.emit([row], model_key)
            # Show visual hints for the constraint
            font = QtGui.QFont()
            font.setItalic(True)
            brush = QtGui.QBrush(QtGui.QColor('blue'))
            self.modifyViewOnRow(row, font=font, brush=brush, model_key=model_key)
        self.communicate.statusBarUpdateSignal.emit('Constraint added')

    def editConstraint(self) -> None:
        """
        Edit constraints for selected parameters.
        """
        current_list = self.tabToList[self.tabFitting.currentIndex()]
        model_key = self.tabToKey[self.tabFitting.currentIndex()]

        params_list = [s.data() for s in current_list.selectionModel().selectedRows()
                   if self.isCheckable(s.row(), model_key=model_key)]
        assert len(params_list) == 1
        row = current_list.selectionModel().selectedRows()[0].row()
        constraint = self.getConstraintForRow(row, model_key=model_key)
        # Create and display the widget for param1 and param2
        mc_widget = MultiConstraint(self, params=params_list, constraint=constraint)
        # Check if any of the parameters are polydisperse
        if not np.any([FittingUtilities.isParamPolydisperse(p, self.logic.model_parameters, is2D=self.is2D) for p in params_list]):
            # no parameters are pd - reset the text to not show the warning
            mc_widget.lblWarning.setText("")
        if mc_widget.exec_() != QtWidgets.QDialog.Accepted:
            return

        constraint = Constraint()
        c_text = mc_widget.txtConstraint.text()

        # widget.params[0] is the parameter we're constraining
        constraint.param = mc_widget.params[0]
        # parameter should have the model name preamble
        model_name = self.logic.kernel_module.name
        # param_used is the parameter we're using in constraining function
        param_used = mc_widget.params[1]
        # Replace param_used with model_name.param_used
        updated_param_used = model_name + "." + param_used
        # Update constraint with new values
        constraint.func = c_text
        constraint.value_ex = updated_param_used
        constraint.value = param_used
        # Should the new constraint be validated?
        constraint.validate = mc_widget.validate

        # Which row is the constrained parameter in?
        if model_key == 'poly' and 'Distribution' in constraint.param:
            constraint.param = self.polydispersity_widget.polyNameToParam(constraint.param)
        row = self.getRowFromName(constraint.param)

        # Create a new item and add the Constraint object as a child
        self.addConstraintToRow(constraint=constraint, row=row, model_key=model_key)

    def deleteConstraint(self) -> None:
        """
        Delete constraints from selected parameters.
        """
        current_list = self.tabToList[self.tabFitting.currentIndex()]
        model_key = self.tabToKey[self.tabFitting.currentIndex()]
        params = [s.data() for s in current_list.selectionModel().selectedRows()
                   if self.isCheckable(s.row(), model_key=model_key)]
        for param in params:
            if model_key == 'poly':
                param = self.polydispersity_widget.polyNameToParam(param)
            self.deleteConstraintOnParameter(param=param, model_key=model_key)

    def deleteConstraintOnParameter(self, param: str | None = None, model_key: str = "standard") -> None:
        """
        Delete the constraint on model parameter 'param'
        """
        param_list = self.lst_dict[model_key]
        model = self.model_dict[model_key]
        for row in range(model.rowCount()):
            if not self.isCheckable(row, model_key=model_key):
                continue
            if not self.rowHasConstraint(row, model_key=model_key):
                continue
            # Get the Constraint object from of the model item
            item = model.item(row, 1)
            constraint = self.getConstraintForRow(row, model_key=model_key)
            if constraint is None:
                continue
            if not isinstance(constraint, Constraint):
                continue
            if param and constraint.param != param:
                continue
            # Now we got the right row. Delete the constraint and clean up
            # Retrieve old values and put them on the model
            if constraint.min is not None:
                try:
                    min_col = param_list.itemDelegate().param_min
                except AttributeError:
                    min_col = 2
                model.item(row, min_col).setText(constraint.min)
            if constraint.max is not None:
                try:
                    max_col = param_list.itemDelegate().param_max
                except AttributeError:
                    max_col = 3
                model.item(row, max_col).setText(constraint.max)
            # Remove constraint item
            item.removeRow(0)
            self.constraintAddedSignal.emit([row], model_key)
            self.modifyViewOnRow(row, model_key=model_key)

        self.communicate.statusBarUpdateSignal.emit('Constraint removed')

    def getConstraintForRow(self, row: int, model_key: str = "standard") -> Constraint | None:
        """
        For the given row, return its constraint, if any (otherwise None)
        """
        model = self.model_dict[model_key]
        if not self.isCheckable(row, model_key=model_key):
            return None
        item = model.item(row, 1)
        try:
            return item.child(0).data()
        except AttributeError:
            return None

    def allParamNames(self) -> list[str]:
        """
        Returns a list of all parameter names defined on the current model
        """
        all_params = self.logic.kernel_module._model_info.parameters.kernel_parameters
        all_params = list(self.logic.kernel_module.details.keys())

        # all_param_names = [param.name for param in all_params]
        # Assure scale and background are always included
        # if 'scale' not in all_param_names:
        #    all_param_names.append('scale')
        # if 'background' not in all_param_names:
        #    all_param_names.append('background')
        return all_params

    def paramHasConstraint(self, param: str | None = None) -> bool:
        """
        Finds out if the given parameter in all the models has a constraint child
        """
        if param is None:
            return False
        if param not in self.allParamNames():
            return False

        for model_key in self.model_dict.keys():
            for row in range(self.model_dict[model_key].rowCount()):
                param_name = self.model_dict[model_key].item(row,0).text()
                if model_key == 'poly':
                    param_name = self.polydispersity_widget.polyNameToParam(param_name)
                if param_name != param:
                    continue
                return self.rowHasConstraint(row, model_key=model_key)

        # nothing found
        return False

    def rowHasConstraint(self, row: int, model_key: str = "standard") -> bool:
        """
        Finds out if row of the main model has a constraint child
        """
        model = self.model_dict[model_key]

        if not self.isCheckable(row, model_key=model_key):
            return False
        item = model.item(row, 1)
        if not item.hasChildren():
            return False
        c = item.child(0).data()
        if isinstance(c, Constraint):
            return True
        return False

    def rowHasActiveConstraint(self, row: int, model_key: str = "standard") -> bool:
        """
        Finds out if row of the main model has an active constraint child
        """
        model = self.model_dict[model_key]
        if not self.isCheckable(row, model_key=model_key):
            return False
        item = model.item(row, 1)
        if not item.hasChildren():
            return False
        c = item.child(0).data()
        if isinstance(c, Constraint) and c.active:
            return True
        return False

    def rowHasActiveComplexConstraint(self, row: int, model_key: str = "standard") -> bool:
        """
        Finds out if row of the main model has an active, nontrivial constraint child
        """
        model = self.model_dict[model_key]
        if not self.isCheckable(row, model_key=model_key):
            return False
        item = model.item(row, 1)
        if not item.hasChildren():
            return False
        c = item.child(0).data()
        if isinstance(c, Constraint) and c.func and c.active:
            return True
        return False

    def selectParameters(self) -> None:
        """
        Selected parameter is chosen for fitting
        """
        status = QtCore.Qt.Checked
        model_key = self.tabToKey[self.tabFitting.currentIndex()]
        model = self.model_dict[model_key]
        item = model.itemFromIndex(self.lstParams.currentIndex())
        self.setParameterSelection(status, item=item, model_key=model_key)

    def deselectParameters(self) -> None:
        """
        Selected parameters are removed for fitting
        """
        status = QtCore.Qt.Unchecked
        model_key = self.tabToKey[self.tabFitting.currentIndex()]
        model = self.model_dict[model_key]
        item = model.itemFromIndex(self.lstParams.currentIndex())
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
        Return a list of tuples. Each tuple contains constraints mapped as
        ('constrained parameter', 'function to constrain')
        e.g. [('sld','5*sld_solvent')]
        """
        params = []
        for model_key in self.model_dict.keys():
            model = self.model_dict[model_key]
            param_number = model.rowCount()
            if model_key == 'poly':
                params += [(self.polydispersity_widget.polyNameToParam(model.item(s, 0).text()),
                           model.item(s, 1).child(0).data().func)
                           for s in range(param_number) if self.rowHasActiveConstraint(s, model_key=model_key)]
            else:
                params += [(model.item(s, 0).text(),
                           model.item(s, 1).child(0).data().func)
                           for s in range(param_number) if self.rowHasActiveConstraint(s, model_key=model_key)]
        return params

    def getComplexConstraintsForAllModels(self) -> list[tuple[str, str]]:
        """
        Returns a list of tuples containing all the constraints defined
        for a given FitPage
        """
        constraints = []
        for model_key in self.model_dict.keys():
            constraints += self.getComplexConstraintsForModel(model_key=model_key)
        return constraints

    def getComplexConstraintsForModel(self, model_key: str) -> list[tuple[str, str]]:
        """
        Return a list of tuples. Each tuple contains constraints mapped as
        ('constrained parameter', 'function to constrain')
        e.g. [('sld','5*M2.sld_solvent')].
        Only for constraints with defined VALUE
        """
        model = self.model_dict[model_key]
        params = []
        param_number = model.rowCount()
        for s in range(param_number):
            if self.rowHasActiveComplexConstraint(s, model_key):
                if model.item(s, 0).data(role=QtCore.Qt.UserRole):
                    parameter_name = str(model.item(s, 0).data(role=QtCore.Qt.UserRole))
                else:
                    parameter_name = str(model.item(s, 0).data(0))
                params.append((parameter_name, model.item(s, 1).child(0).data().func))
        return params

    def getFullConstraintNameListForModel(self, model_key: str) -> list[tuple[str, str]]:
        """
        Return a list of tuples. Each tuple contains constraints mapped as
        ('constrained parameter', 'function to constrain')
        e.g. [('sld','5*M2.sld_solvent')].
        Returns a list of all constraints, not only active ones
        """
        model = self.model_dict[model_key]
        param_number = model.rowCount()
        params = list()
        for s in range(param_number):
            if self.rowHasConstraint(s, model_key=model_key):
                param_name = model.item(s, 0).text()
                if model_key == 'poly':
                    param_name = self.polydispersity_widget.polyNameToParam(model.item(s, 0).text())
                params.append((param_name, model.item(s, 1).child(0).data().func))
        return params

    def getConstraintObjectsForAllModels(self) -> list[Constraint]:
        """
        Returns a list of the constraint object for a given FitPage
        """
        constraints = []
        for model_key in self.model_dict.keys():
            constraints += self.getConstraintObjectsForModel(model_key=model_key)
        return constraints

    def getConstraintObjectsForModel(self, model_key: str) -> list[Constraint]:
        """
        Returns Constraint objects present on the whole model
        """
        model = self.model_dict[model_key]
        param_number = model.rowCount()
        constraints = [model.item(s, 1).child(0).data()
                       for s in range(param_number) if self.rowHasConstraint(s, model_key=model_key)]
        return constraints

    def getConstraintsForFitting(self) -> list[tuple[str, str]]:
        """
        Return a list of constraints in format ready for use in fiting
        """
        # Get constraints
        constraints = []
        for model_key in self.model_dict.keys():
            constraints += self.getComplexConstraintsForModel(model_key=model_key)
        # See if there are any constraints across models
        multi_constraints = [cons for cons in constraints if self.isConstraintMultimodel(cons[1])]

        if multi_constraints:
            # Let users choose what to do
            msg = "The current fit contains constraints relying on other fit pages.\n"
            msg += ("Parameters with those constraints are:\n" +
                    '\n'.join([cons[0] for cons in multi_constraints]))
            msg += ("\n\nWould you like to deactivate these constraints or "
                    "cancel fitting?")
            msgbox = QtWidgets.QMessageBox(self)
            msgbox.setIcon(QtWidgets.QMessageBox.Warning)
            msgbox.setText(msg)
            msgbox.setWindowTitle("Existing Constraints")
            # custom buttons
            button_remove = QtWidgets.QPushButton("Deactivate")
            msgbox.addButton(button_remove, QtWidgets.QMessageBox.YesRole)
            button_cancel = QtWidgets.QPushButton("Cancel")
            msgbox.addButton(button_cancel, QtWidgets.QMessageBox.RejectRole)
            retval = msgbox.exec_()
            if retval == QtWidgets.QMessageBox.RejectRole:
                # cancel fit
                raise ValueError("Fitting cancelled")
            else:
                constraint_tab = self.parent.perspective().getConstraintTab()
                for cons in multi_constraints:
                    # deactivate the constraint
                    row = self.getRowFromName(cons[0])
                    model_key = self.getModelKeyFromName(cons[0])
                    self.getConstraintForRow(row, model_key=model_key).active = False
                    # uncheck in the constraint tab
                    if constraint_tab:
                        constraint_tab.uncheckConstraint(
                            self.logic.kernel_module.name + ':' + cons[0])
                # re-read the constraints
                constraints = self.getComplexConstraintsForModel(model_key=model_key)

        return constraints

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
        has_mag_params = False
        if self.logic.kernel_module:
            has_mag_params = len(self.logic.kernel_module.magnetic_params) > 0
        return self.is2D and has_mag_params

    def onSelectModel(self) -> None:
        """
        Respond to select Model from list event
        """
        model = self.cbModel.currentText()

        if model == MODEL_DEFAULT:
            # if the previous category was not the default, keep it.
            # Otherwise, just return
            if self._previous_model_index != 0:
                # We need to block signals, or else state changes on perceived unchanged conditions
                self.cbModel.blockSignals(True)
                self.cbModel.setCurrentIndex(self._previous_model_index)
                self.cbModel.blockSignals(False)
            return
        if self.model_data is not None:
            # Store any old parameters before switching to a new model
            self.page_parameters = self.getParameterDict()

        # Assure the control is active
        if not self.cbModel.isEnabled():
            return
        # Empty combobox forced to be read
        if not model:
            return

        self.chkMagnetism.setEnabled(self.canHaveMagnetism())
        self.tabFitting.setTabEnabled(TAB_MAGNETISM, self.chkMagnetism.isChecked() and self.canHaveMagnetism())
        self._previous_model_index = self.cbModel.currentIndex()

        # Reset parameters to fit
        self.resetParametersToFit()
        self.has_error_column = False

        structure = None
        if self.cbStructureFactor.isEnabled():
            structure = str(self.cbStructureFactor.currentText())
        self.respondToModelStructure(model=model, structure_factor=structure)

        # paste parameters from previous state
        if self.page_parameters:
            self.updatePageWithParameters(self.page_parameters, warn_user=False)

        # disable polydispersity if the model does not support it
        has_poly = self.polydispersity_widget.poly_model.rowCount() != 0
        self.chkPolydispersity.setEnabled(has_poly)
        # self.tabFitting.setTabEnabled(TAB_POLY, has_poly)

        # set focus so it doesn't move up
        self.cbModel.setFocus()

    def onSelectBatchFilename(self, data_index: int) -> None:
        """
        Update the logic based on the selected file in batch fitting
        """
        self.data_index = data_index
        self.updateQRange()

    def onSelectStructureFactor(self) -> None:
        """
        Select Structure Factor from list
        """
        model = str(self.cbModel.currentText())
        category = str(self.cbCategory.currentText())
        structure = str(self.cbStructureFactor.currentText())
        if category == CATEGORY_STRUCTURE:
            model = None
        # copy original clipboard
        cb = QtWidgets.QApplication.clipboard()
        cb_text = cb.text()
        # get the screenshot of the current param state
        self.clipboard_copy()

        # Reset parameters to fit
        self.resetParametersToFit()
        self.has_error_column = False

        self.respondToModelStructure(model=model, structure_factor=structure)
        # recast the original parameters into the model
        self.clipboard_paste()
        # revert to the original clipboard
        cb.setText(cb_text)

    def resetParametersToFit(self) -> None:
        """
        Clears the list of parameters to be fitted
        """
        self.main_params_to_fit = []
        self.polydispersity_widget.resetParameters()
        self.magnetism_widget.magnet_params_to_fit = []

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
        self.communicate.statusBarUpdateSignal.emit("")
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
            self.communicate.statusBarUpdateSignal.emit(update_text)

    def onSesansData(self) -> None:
        """
        Updates the fitting widget format when SESANS data is loaded.
        """
        # update the units in the 'Fitting details' box of the Model tab on the Fit Panel
        self.label_17.setText("Å")
        self.label_19.setText("Å")
        # disable the background parameter and set at 0 for sesans
        self.disableBackgroundParameter(set_value=0.0)
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
        Replace names of models in defined constraints
        """
        param_number = self._model_model.rowCount()
        # loop over parameters
        for row in range(param_number):
            if self.rowHasConstraint(row):
                func = self._model_model.item(row, 1).child(0).data().func
                if old_name in func:
                    new_func = func.replace(old_name, new_name)
                    self._model_model.item(row, 1).child(0).data().func = new_func

    def isConstraintMultimodel(self, constraint: str) -> bool:
        """
        Check if the constraint function text contains current model name
        """
        current_model_name = self.logic.kernel_module.name
        if current_model_name in constraint:
            return False
        else:
            return True

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

    def respondToModelStructure(self, model: str | None = None, structure_factor: str | None = None) -> None:
        # Set enablement on calculate/plot
        self.cmdPlot.setEnabled(True)

        # kernel parameters -> model_model
        self.SASModelToQModel(model, structure_factor)

        # Enable magnetism checkbox for selected models
        self.chkMagnetism.setEnabled(self.canHaveMagnetism())
        self.tabFitting.setTabEnabled(TAB_MAGNETISM, self.chkMagnetism.isChecked() and self.canHaveMagnetism())

        # Update column widths
        for column, width in self.lstParamHeaderSizes.items():
            self.lstParams.setColumnWidth(column, width)

        # disable background for SESANS data
        # this should be forced to 0 in sasmodels but this tells the user it is enforced to 0 and disables the box
        if self.data_is_loaded:
            if self.data.isSesans:
                self.disableBackgroundParameter(set_value=0)

        # Update plot
        self.updateData()

        # Update state stack
        self.updateUndo()

        # Let others know
        self.newModelSignal.emit()

    def onSelectCategory(self) -> None:
        """
        Select Category from list
        """
        category = self.cbCategory.currentText()
        # Check if the user chose "Choose category entry"
        if category == CATEGORY_DEFAULT:
            # if the previous category was not the default, keep it.
            # Otherwise, just return
            if self._previous_category_index != 0:
                # We need to block signals, or else state changes on perceived unchanged conditions
                self.cbCategory.blockSignals(True)
                self.cbCategory.setCurrentIndex(self._previous_category_index)
                self.cbCategory.blockSignals(False)
            return

        if category == CATEGORY_STRUCTURE:
            self.disableModelCombo()
            self.enableStructureCombo()
            # set the index to 0
            self.cbStructureFactor.setCurrentIndex(0)
            self.logic.model_parameters = None
            self._model_model.clear()
            return

        if self.model_data is not None:
            # Store any old parameters before switching to a new category
            self.page_parameters = self.getParameterDict()
        # Wipe out the parameter model
        self._model_model.clear()
        # Safely clear and enable the model combo
        self.cbModel.blockSignals(True)
        self.cbModel.clear()
        self.cbModel.blockSignals(False)
        self.enableModelCombo()
        self.disableStructureCombo()

        self._previous_category_index = self.cbCategory.currentIndex()
        # Retrieve the list of models
        model_list = self.master_category_dict[category]
        # Populate the models combobox
        self.cbModel.blockSignals(True)
        self.cbModel.addItem(MODEL_DEFAULT)
        models_to_show = [m[0] for m in model_list if m[0] not in SUPPRESSED_MODELS and m[1]]
        self.cbModel.addItems(sorted(models_to_show))
        self.cbModel.blockSignals(False)

    def onHelp(self):
        """
        Show the "Fitting" section of help
        """
        help_location = self.getHelpLocation(HELP_DIRECTORY_LOCATION)
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
            fitters, _ = self.prepareFitters()
        except ValueError as ex:
            # This should not happen! GUI explicitly forbids this situation
            self.communicate.statusBarUpdateSignal.emit(str(ex))
            return

        # keep local copy of kernel parameters, as they will change during the update
        self.kernel_module_copy = copy.deepcopy(self.logic.kernel_module)

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

        self.communicate.statusBarUpdateSignal.emit('Fitting started...')
        self.fit_started = True

        # Disable some elements
        self.disableInteractiveElements()

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
        self.communicate.statusBarUpdateSignal.emit(msg)

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
        self.communicate.statusBarUpdateSignal.emit(msg)

    def batchFittingCompleted(self, result: tuple | None) -> None:
        """
        Send the finish message from calculate threads to main thread
        """
        if result is None:
            result = tuple()
        self.batchFittingFinishedSignal.emit(result)

    def batchFitComplete(self, result: tuple) -> None:
        """
        Receive and display batch fitting results
        """
        #re-enable the Fit button
        self.enableInteractiveElements()

        if len(result) == 0:
            msg = "Fitting failed."
            self.communicate.statusBarUpdateSignal.emit(msg)
            return

        # Show the grid panel
        page_name = "BatchPage" + str(self.tab_id)
        results = copy.deepcopy(result[0])
        results.append(page_name)
        self.communicate.sendDataToGridSignal.emit(results)

        elapsed = result[1]
        msg = "Fitting completed successfully in: %s s.\n" % GuiUtils.formatNumber(elapsed)
        self.communicate.statusBarUpdateSignal.emit(msg)

        # Run over the list of results and update the items
        for res_index, res_list in enumerate(result[0]):
            # results
            res = res_list[0]
            param_dict = self.paramDictFromResults(res)

            # create local kernel_module
            kernel_module = FittingUtilities.updateKernelWithResults(self.logic.kernel_module, param_dict)
            # pull out current data
            data = self._logic[res_index].data

            # Switch indexes
            self.data_index = res_index

            # Recalculate theories
            method = self.complete1D if isinstance(self.data, Data1D) else self.complete2D
            self.calculateQGridForModelExt(data=data, model=kernel_module, completefn=method, use_threads=False)

        # Restore original kernel_module, so subsequent fits on the same model don't pick up the new params
        if self.logic.kernel_module is not None:
            self.logic.kernel_module = copy.deepcopy(self.kernel_module_copy)

    def paramDictFromResults(self, results: Any) -> dict[str, tuple[float, float]] | None:
        """
        Given the fit results structure, pull out optimized parameters and return them as nicely
        formatted dict
        """
        pvec = [float(p) for p in results.pvec]
        if results.fitness is None or \
            not np.isfinite(results.fitness) or \
            np.any(pvec is None) or \
            not np.all(np.isfinite(pvec)):
            msg = "Fitting did not converge!"
            self.communicate.statusBarUpdateSignal.emit(msg)
            msg += results.mesg
            logger.error(msg)
            return

        if results.mesg:
            logger.warning(results.mesg)

        param_list = results.param_list # ['radius', 'radius.width']
        param_values = pvec             # array([ 0.36221662,  0.0146783 ])
        param_stderr = results.stderr   # array([ 1.71293015,  1.71294233])
        params_and_errors = list(zip(param_values, param_stderr))
        param_dict = dict(zip(param_list, params_and_errors))

        return param_dict

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
            self.communicate.statusBarUpdateSignal.emit(msg)
            # reload the kernel_module in case it's corrupted
            self.kernel_module = copy.deepcopy(self.kernel_module_copy)
            return

        # Don't recalculate chi2 - it's in res.fitness already
        self.fitResults = True
        if result is None or len(result) == 0 or len(result[0]) == 0:
            msg = "Fitting failed."
            self.communicate.statusBarUpdateSignal.emit(msg)
            return
        res_list = result[0][0]
        res = res_list[0]
        self.chi2 = res.fitness
        param_dict = self.paramDictFromResults(res)

        if param_dict is None:
            return

        # Show bumps convergence plots
        self.communicate.resultPlotUpdateSignal.emit(result[0])

        elapsed = result[1]
        if self.calc_fit is not None and self.calc_fit._interrupting:
            msg = "Fitting cancelled by user after: %s s." % GuiUtils.formatNumber(elapsed)
            logger.warning("\n"+msg+"\n")
        else:
            msg = "Fitting completed successfully in: %s s." % GuiUtils.formatNumber(elapsed)
        self.communicate.statusBarUpdateSignal.emit(msg)

        # Dictionary of fitted parameter: value, error
        # e.g. param_dic = {"sld":(1.703, 0.0034), "length":(33.455, -0.0983)}
        self.updateModelFromList(param_dict)

        self.polydispersity_widget.updatePolyModelFromList(param_dict)

        self.magnetism_widget.updateMagnetModelFromList(param_dict)

        # update charts
        self.onPlot()

        # Read only value - we can get away by just printing it here
        chi2_repr = GuiUtils.formatNumber(self.chi2, high=True)
        self.lblChi2Value.setText(chi2_repr)


    def prepareFitters(self, fitter: Fit | None = None, fit_id: int = 0, weight_increase: int = 1) -> tuple[list[Fit], int]:
        """
        Prepare the Fitter object for use in fitting
        """
        # fitter = None -> single/batch fitting
        # fitter = Fit() -> simultaneous fitting

        # Data going in
        data = self.logic.data
        model = self.logic.kernel_module
        qmin = self.q_range_min
        qmax = self.q_range_max

        params_to_fit = copy.deepcopy(self.main_params_to_fit)
        if self.chkPolydispersity.isChecked():
            for p in self.polydispersity_widget.poly_params_to_fit:
                if "Distribution of" in p:
                    params_to_fit += [self.polydispersity_widget.polyNameToParam(p)]
                else:
                    params_to_fit += [p]
        if self.chkMagnetism.isChecked() and self.canHaveMagnetism():
            params_to_fit += self.magnetism_widget.magnet_params_to_fit
        if not params_to_fit:
            raise ValueError('Fitting requires at least one parameter to optimize.')

        # Get the constraints.
        constraints = []
        for model_key in self.model_dict.keys():
            constraints += self.getComplexConstraintsForModel(model_key=model_key)
        if fitter is None:
            # For single fits - check for inter-model constraints
            constraints = self.getConstraintsForFitting()

        smearer = self.smearing_widget.smearer()

        fitters = []
        # order datasets if chain fit
        order = self.all_data
        if self.is_chain_fitting:
            order = self.order_widget.ordering()
        for fit_index in order:
            fitter_single = Fit() if fitter is None else fitter
            data = GuiUtils.dataFromItem(fit_index)
            # Potential weights added directly to data
            weighted_data = self.addWeightingToData(data)
            try:
                fitter_single.set_model(model, fit_id, params_to_fit, data=weighted_data,
                             constraints=constraints)
            except ValueError as ex:
                raise ValueError("Setting model parameters failed with: %s" % ex)

            fitter_single.set_data(data=weighted_data, id=fit_id, smearer=smearer, qmin=qmin,
                            qmax=qmax)
            fitter_single.select_problem_for_fit(id=fit_id, value=1)
            fitter_single.set_weight_increase(fit_id, weight_increase)
            if fitter is None:
                # Assign id to the new fitter only
                fitter_single.fitter_id = [self.page_id]
            fit_id += 1
            fitters.append(fitter_single)

        return fitters, fit_id

    def iterateOverModel(self, func: Any) -> None:
        """
        Take func and throw it inside the model row loop
        """
        for row_i in range(self._model_model.rowCount()):
            func(row_i)

    def updateFunctionCaption(self, row):
        # Utility function for update of polydispersity function name in the main model
        param_name = self._model_model.item(row, 0).text()
        dispersion_value = self.polydispersity_widget.poly_params.get(param_name + ".width", None)
        # This is an explicit check against None which means the param is not in the polydispersity list
        if dispersion_value is None:
            return
        try:
            dispersion_model = self.logic.kernel_module.dispersion.get(param_name, None)
            combo_string = dispersion_model.get('type')
        except AttributeError:
            combo_string = DEFAULT_POLYDISP_FUNCTION
        # Modify the param value
        param_row = self._model_model.item(row, 0).child(0)
        self._model_model.blockSignals(True)
        param_row.child(0, 1).setText(f"{dispersion_value:.3f}")
        if self.has_error_column:
            # err column changes the indexing
            param_row.child(0, 5).setText(combo_string)
        else:
            param_row.child(0, 4).setText(combo_string)
        self._model_model.blockSignals(False)

    def updateModelFromList(self, param_dict: dict[str, tuple[float, float]]) -> None:
        """
        Update the model with new parameters, create the errors column
        """
        assert isinstance(param_dict, dict)

        def updateFittedValues(row):
            # Utility function for main model update
            # internal so can use closure for param_dict
            param_name = str(self._model_model.item(row, 0).text())
            if not self.isCheckable(row) or param_name not in list(param_dict.keys()):
                return
            # modify the param value
            param_repr = GuiUtils.formatNumber(param_dict[param_name][0], high=True)
            self._model_model.item(row, 1).setText(param_repr)
            self.logic.kernel_module.setParam(param_name, param_dict[param_name][0])
            if self.has_error_column:
                error_repr = GuiUtils.formatNumber(param_dict[param_name][1], high=True)
                self._model_model.item(row, 2).setText(error_repr)

        def updatePolyValues(row):
            # Utility function for updateof polydispersity part of the main model
            param_name = str(self._model_model.item(row, 0).text())+'.width'
            if not self.isCheckable(row) or param_name not in list(param_dict.keys()):
                return
            # modify the param value
            param_repr = GuiUtils.formatNumber(param_dict[param_name][0], high=True)
            self._model_model.item(row, 0).child(0).child(0,1).setText(param_repr)
            # modify the param error
            if self.has_error_column:
                error_repr = GuiUtils.formatNumber(param_dict[param_name][1], high=True)
                self._model_model.item(row, 0).child(0).child(0,2).setText(error_repr)

        def createErrorColumn(row):
            # Utility function for error column update
            item = QtGui.QStandardItem()
            def createItem(param_name):
                if param_name not in self.main_params_to_fit:
                    error_repr = ""
                else:
                    error_repr = GuiUtils.formatNumber(param_dict[param_name][1], high=True)
                item.setText(error_repr)
            def curr_param():
                return str(self._model_model.item(row, 0).text())

            [createItem(param_name) for param_name in list(param_dict.keys()) if curr_param() == param_name]

            error_column.append(item)

        def createPolyErrorColumn(row):
            # Utility function for error column update in the polydispersity sub-rows
            # NOTE: only creates empty items; updatePolyValues adds the error value
            item = self._model_model.item(row, 0)
            if not item.hasChildren():
                return
            poly_item = item.child(0)
            if not poly_item.hasChildren():
                return
            poly_item.insertColumn(2, [QtGui.QStandardItem("")])

        def deletePolyErrorColumn(row):
            # Utility function for error column removal in the polydispersity sub-rows
            item = self._model_model.item(row, 0)
            if not item.hasChildren():
                return
            poly_item = item.child(0)
            if not poly_item.hasChildren():
                return
            poly_item.removeColumn(2)

        if self.has_error_column:
            # remove previous entries
            self._model_model.removeColumn(2)
            self.iterateOverModel(deletePolyErrorColumn)

        #if not self.has_error_column:
            # create top-level error column
        error_column = []
        self.lstParams.itemDelegate().addErrorColumn()
        self.iterateOverModel(createErrorColumn)

        self._model_model.insertColumn(2, error_column)

        FittingUtilities.addErrorHeadersToModel(self._model_model)

        # create error column in polydispersity sub-rows
        self.iterateOverModel(createPolyErrorColumn)

        self.has_error_column = True

        # block signals temporarily, so we don't end up
        # updating charts with every single model change on the end of fitting
        self._model_model.dataChanged.disconnect()
        self.iterateOverModel(updateFittedValues)
        self.iterateOverModel(updatePolyValues)
        self._model_model.dataChanged.connect(self.onMainParamsChange)

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
        React to changes in the smearing widget
        """
        # update display
        smearing, accuracy, smearing_min, smearing_max = self.smearing_widget.state()
        self.lblCurrentSmearing.setText(smearing)
        self.calculateQGridForModel()

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
            self.communicate.plotRequestedSignal.emit([item, data_to_show], self.tab_id)

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
                self.communicate.plotRequestedSignal.emit([item, plot], self.tab_id)
        # return the last data item seen, if nothing was plotted; supposed to be just data)
        return None if data_shown else item

    def onOptionsUpdate(self) -> None:
        """
        Update local option values and replot
        """
        self.q_range_min, self.q_range_max, self.npts, self.log_points, self.weighting = \
            self.options_widget.state()
        # set Q range labels on the main tab
        self.lblMinRangeDef.setText(GuiUtils.formatNumber(self.q_range_min, high=True))
        self.lblMaxRangeDef.setText(GuiUtils.formatNumber(self.q_range_max, high=True))
        self.recalculatePlotData()

    def setDefaultStructureCombo(self) -> None:
        """
        Fill in the structure factors combo box with defaults
        """
        structure_factor_list = self.master_category_dict.pop(CATEGORY_STRUCTURE)
        factors = [factor[0] for factor in structure_factor_list]
        factors.insert(0, STRUCTURE_DEFAULT)
        self.cbStructureFactor.clear()
        self.cbStructureFactor.addItems(sorted(factors))

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
        for category in self.master_category_dict:
            for (model, enabled) in self.master_category_dict[category]:
                self.by_model_dict[model].append(category)
                self.model_enabled_dict[model] = enabled

    def addBackgroundToModel(self, model: QtGui.QStandardItemModel) -> None:
        """
        Adds background parameter with default values to the model
        """
        assert isinstance(model, QtGui.QStandardItemModel)
        checked_list = ['background', '0.001', '-inf', 'inf', '1/cm']
        FittingUtilities.addCheckedListToModel(model, checked_list)
        last_row = model.rowCount()-1
        model.item(last_row, 0).setEditable(False)
        model.item(last_row, 4).setEditable(False)
        model.item(last_row,0).setData('background', role=QtCore.Qt.UserRole)


    def addScaleToModel(self, model: QtGui.QStandardItemModel) -> None:
        """
        Adds scale parameter with default values to the model
        """
        assert isinstance(model, QtGui.QStandardItemModel)
        checked_list = ['scale', '1.0', '0.0', 'inf', '']
        FittingUtilities.addCheckedListToModel(model, checked_list)
        last_row = model.rowCount()-1
        model.item(last_row, 0).setEditable(False)
        model.item(last_row, 4).setEditable(False)
        model.item(last_row,0).setData('scale', role=QtCore.Qt.UserRole)

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

    def SASModelToQModel(self, model_name: str | None, structure_factor: str | None = None) -> None:
        """
        Setting model parameters into table based on selected category
        """
        # Crete/overwrite model items
        self._model_model.clear()
        self.polydispersity_widget.poly_model.clear()
        self.magnetism_widget._magnet_model.clear()

        if model_name is None:
            if structure_factor not in (None, "None"):
                # S(Q) on its own, treat the same as a form factor
                self.logic.kernel_module = None
                self.fromStructureFactorToQModel(structure_factor)
            else:
                # No models selected
                return
        else:
            self.fromModelToQModel(model_name)
            self.addExtraShells()

            # Allow the SF combobox visibility for the given sasmodel
            self.enableStructureFactorControl(structure_factor)

            # Add S(Q)
            if self.cbStructureFactor.isEnabled():
                structure_factor = self.cbStructureFactor.currentText()
                self.fromStructureFactorToQModel(structure_factor)

            # Add polydispersity to the model
            self.polydispersity_widget.setPolyModel()
            # Add magnetic parameters to the model
            self.magnetism_widget.magnet_params = {}
            self.magnetism_widget.setMagneticModel()

        # Now we claim the model has been loaded
        self.model_is_loaded = True
        # Change the model name to a monicker
        self.logic.kernel_module.name = self.modelName()
        # Update the smearing tab
        self.smearing_widget.updateKernelModel(kernel_model=self.logic.kernel_module)

        # (Re)-create headers
        FittingUtilities.addHeadersToModel(self._model_model)
        self.lstParams.header().setFont(self.boldFont)

    def fromModelToQModel(self, model_name: str) -> None:
        """
        Setting model parameters into QStandardItemModel based on selected model
        """
        name = model_name
        kernel_module = None
        if self.cbCategory.currentText() == CATEGORY_CUSTOM:
            # custom kernel load requires full path
            name = os.path.join(models.find_plugins_dir(), model_name+".py")
        try:
            kernel_module = generate.load_kernel_module(name)
        except ModuleNotFoundError:
            pass
        except FileNotFoundError:
            # can happen when name attribute not the same as actual filename
            pass

        if kernel_module is None:
            # mismatch between "name" attribute and actual filename.
            curr_model = self.models[model_name]
            name, _ = os.path.splitext(os.path.basename(curr_model.filename))
            try:
                kernel_module = generate.load_kernel_module(name)
            except ModuleNotFoundError as ex:
                logger.error("Can't find the model "+ str(ex))
                return

        if hasattr(kernel_module, 'model_info'):
            # for sum/multiply models
            self.logic.model_parameters = kernel_module.model_info.parameters

        elif hasattr(kernel_module, 'parameters'):
            # built-in and custom models
            self.logic.model_parameters = modelinfo.make_parameter_table(getattr(kernel_module, 'parameters', []))

        elif hasattr(kernel_module, 'model_info'):
            # for sum/multiply models
            self.logic.model_parameters = kernel_module.model_info.parameters

        elif hasattr(kernel_module, 'Model') and hasattr(kernel_module.Model, "_model_info"):
            # this probably won't work if there's no model_info, but just in case
            self.logic.model_parameters = kernel_module.Model._model_info.parameters
        else:
            # no parameters - default to blank table
            msg = f"No parameters found in model '{model_name}'."
            logger.warning(msg)
            self.logic.model_parameters = modelinfo.ParameterTable([])

        # Instantiate the current sasmodel
        self.logic.kernel_module = self.models[model_name]()

        # Change the model name to a monicker
        self.logic.kernel_module.name = self.modelName()

        # Explicitly add scale and background with default values
        temp_undo_state = self.undo_supported
        self.undo_supported = False
        self.addScaleToModel(self._model_model)
        self.addBackgroundToModel(self._model_model)
        self.undo_supported = temp_undo_state

        self.logic.shell_names = self.shellNamesList()

        # Add heading row
        FittingUtilities.addHeadingRowToModel(self._model_model, model_name)

        # Update the QModel
        FittingUtilities.addParametersToModel(
                self.logic.model_parameters,
                self.logic.kernel_module,
                self.is2D,
                self._model_model,
                self.lstParams)

    def fromStructureFactorToQModel(self, structure_factor: str) -> None:
        """
        Setting model parameters into QStandardItemModel based on selected structure factor
        """
        if structure_factor is None or structure_factor=="None":
            return

        product_params = None
        kernel_module = self.models[structure_factor]()

        if self.logic.kernel_module is None:
            self.logic.kernel_module = kernel_module
            # Structure factor is the only selected model; build it and show all its params
            self.logic.kernel_module.name = self.modelName()
            s_params = self.logic.kernel_module._model_info.parameters
        else:
            # Assure we only have one volfraction shown
            s_params, product_params = self._volfraction_hack(kernel_module)

        # Add heading row
        FittingUtilities.addHeadingRowToModel(self._model_model, structure_factor)

        # Get new rows for QModel
        # Any renamed parameters are stored as data in the relevant item, for later handling
        FittingUtilities.addSimpleParametersToModel(
                parameters=s_params,
                is2D=self.is2D,
                parameters_original=None,
                model=self._model_model,
                view=self.lstParams)

        # Insert product-only params into QModel
        if product_params:
            prod_rows = FittingUtilities.addSimpleParametersToModel(
                    parameters=product_params,
                    is2D=self.is2D,
                    parameters_original=None,
                    model=self._model_model,
                    view=self.lstParams,
                    row_num=2)

            # Since this all happens after shells are dealt with and we've inserted rows, fix this counter
            self._n_shells_row += len(prod_rows)

    def _volfraction_hack(self, s_kernel: Any) -> tuple[modelinfo.ParameterTable, modelinfo.ParameterTable | None]:
        """
        Only show volfraction once if it appears in both P and S models.
        Issues SV:1280, SV:1295, SM:219, SM:199, SM:101
        """
        from sasmodels.product import RADIUS_MODE_ID, STRUCTURE_MODE_ID, VOLFRAC_ID

        product_params = None
        p_kernel = self.logic.kernel_module
        # need to reset multiplicity to get the right product
        if p_kernel.is_multiplicity_model:
            p_kernel.multiplicity = p_kernel.multiplicity_info.number

        self.logic.kernel_module = MultiplicationModel(p_kernel, s_kernel)
        # Modify the name to correspond to shown items
        self.logic.kernel_module.name = self.modelName()

        # TODO: set model layout in sasmodels
        info = self.logic.kernel_module._model_info
        p_info = p_kernel._model_info
        s_info = s_kernel._model_info

        def par_index(info, key):
            for k, p in enumerate(info.parameters.kernel_parameters):
                if p.id == key:
                    return k
            return -1
        p_volfrac_id = par_index(p_info, VOLFRAC_ID)
        s_volfrac_id = par_index(s_info, VOLFRAC_ID)
        s_pars = s_info.parameters.kernel_parameters[:]
        if p_volfrac_id >= 0 and s_volfrac_id >= 0:
            del s_pars[s_volfrac_id]

        er_mode_id = par_index(info, RADIUS_MODE_ID)
        interaction_mode_id = par_index(info, STRUCTURE_MODE_ID)
        extras = []
        if interaction_mode_id >= 0:
            extras.append(info.parameters.kernel_parameters[interaction_mode_id])
        if (er_mode_id >= 0):
            extras.append(info.parameters.kernel_parameters[er_mode_id])

        s_params = modelinfo.ParameterTable(s_pars)
        product_params = modelinfo.ParameterTable(extras)

        return (s_params, product_params)

    def haveParamsToFit(self) -> bool:
        """
        Finds out if there are any parameters ready to be fitted
        """
        if not self.logic.data_is_loaded:
            return False
        if self.main_params_to_fit:
            return True
        if self.chkPolydispersity.isChecked() and self.polydispersity_widget.poly_params_to_fit:
            return True
        if self.chkMagnetism.isChecked() and self.canHaveMagnetism() and self.magnetism_widget.magnet_params_to_fit:
            return True
        return False

    def onMainParamsChange(self, top: QtCore.QModelIndex, bottom: QtCore.QModelIndex) -> None:
        """
        Callback method for updating the sasmodel parameters with the GUI values
        """
        item = self._model_model.itemFromIndex(top)

        model_column = item.column()

        if model_column == 0:
            self.checkboxSelected(item, model_key="standard")
            self.cmdFit.setEnabled(self.haveParamsToFit())
            # Update state stack
            self.updateUndo()
            return

        model_row = item.row()
        name_index = self._model_model.index(model_row, 0)
        name_item = self._model_model.itemFromIndex(name_index)

        # Extract changed value.
        try:
            value = GuiUtils.toDouble(item.text())
        except TypeError:
            # Unparsable field
            return

        # if the item has user data, this is the actual parameter name (e.g. to handle duplicate names)
        if name_item.data(QtCore.Qt.UserRole):
            parameter_name = str(name_item.data(QtCore.Qt.UserRole))
        else:
            parameter_name = str(self._model_model.data(name_index))

        # Update the parameter value - note: this supports +/-inf as well
        param_column = self.lstParams.itemDelegate().param_value
        min_column = self.lstParams.itemDelegate().param_min
        max_column = self.lstParams.itemDelegate().param_max
        if model_column == param_column:
            # don't try to update multiplicity counters if they aren't there.
            # Note that this will fail for proper bad update where the model
            # doesn't contain multiplicity parameter
            self.logic.kernel_module.setParam(parameter_name, value)

        elif model_column == min_column:
            # min/max to be changed in self.logic.kernel_module.details[parameter_name] = ['Ang', 0.0, inf]
            self.logic.kernel_module.details[parameter_name][1] = value
        elif model_column == max_column:
            self.logic.kernel_module.details[parameter_name][2] = value
        else:
            # don't update the chart
            return

        # handle display of effective radius parameter according to radius_effective_mode; pass ER into model if
        # necessary
        self.processEffectiveRadius()

        # Update state stack
        self.updateUndo()
        self.page_parameters = self.getParameterDict()

    def processEffectiveRadius(self) -> None:
        """
        Checks the value of radius_effective_mode, if existent, and processes radius_effective as necessary.
        * mode == 0: This means 'unconstrained'; ensure use can specify ER.
        * mode > 0: This means it is constrained to a P(Q)-computed value in sasmodels; prevent user from editing ER.

        Note: If ER has been computed, it is passed back to SasView as an intermediate result. That value must be
        displayed for the user; that is not dealt with here, but in complete1D.
        """
        ER_row = self.getRowFromName("radius_effective")
        if ER_row is None:
            return

        ER_mode_row = self.getRowFromName("radius_effective_mode")
        if ER_mode_row is None:
            return

        try:
            ER_mode = int(self._model_model.item(ER_mode_row, 1).text())
        except ValueError:
            logging.error("radius_effective_mode was set to an invalid value.")
            return

        if ER_mode == 0:
            # ensure the ER value can be modified by user
            self.setParamEditableByRow(ER_row, True)
        elif ER_mode > 0:
            # ensure the ER value cannot be modified by user
            self.setParamEditableByRow(ER_row, False)
        else:
            logging.error("radius_effective_mode was set to an invalid value.")

    def setParamEditableByRow(self, row: int, editable: bool = True) -> None:
        """
        Sets whether the user can edit a parameter in the table. If they cannot, the parameter name's font is changed,
        the value itself cannot be edited if clicked on, and the parameter may not be fitted.
        """
        item_name = self._model_model.item(row, 0)
        item_value = self._model_model.item(row, 1)

        item_value.setEditable(editable)

        if editable:
            # reset font
            item_name.setFont(QtGui.QFont())
            # reset colour
            item_name.setForeground(QtGui.QBrush())
            # make checkable
            item_name.setCheckable(True)
        else:
            # change font
            font = QtGui.QFont()
            font.setItalic(True)
            item_name.setFont(font)
            # change colour
            item_name.setForeground(QtGui.QBrush(QtGui.QColor(50, 50, 50)))
            # make not checkable (and uncheck)
            item_name.setCheckState(QtCore.Qt.Unchecked)
            item_name.setCheckable(False)

    def isCheckable(self, row: int, model_key: str = "standard") -> bool:
        model = self.model_dict[model_key]
        if model.item(row,0) is None:
            return False
        return model.item(row, 0).isCheckable()

    def changeCheckboxStatus(self, row: int, checkbox_status: bool, model_key: str = "standard") -> None:
        """
        Checks/unchecks the checkbox at given row
        """
        model = self.model_dict[model_key]

        assert 0<= row <= model.rowCount()
        index = model.index(row, 0)
        item = model.itemFromIndex(index)
        if checkbox_status:
            item.setCheckState(QtCore.Qt.Checked)
        else:
            item.setCheckState(QtCore.Qt.Unchecked)

    def checkboxSelected(self, item: QtGui.QStandardItem, model_key: str = "standard") -> None:
        # Assure we're dealing with checkboxes
        if not item.isCheckable():
            return
        status = item.checkState()

        # If multiple rows selected - toggle all of them, filtering uncheckable
        # Convert to proper indices and set requested enablement
        # Careful with `item` NOT being selected. This means we only want to
        # select that one item.
        self.setParameterSelection(status, item=item, model_key=model_key)

        # update the list of parameters to fit
        self.main_params_to_fit = self.checkedListFromModel("standard")
        self.polydispersity_widget.poly_params_to_fit = self.checkedListFromModel("poly")
        self.magnetism_widget.magnet_params_to_fit = self.checkedListFromModel("magnet")

    def checkedListFromModel(self, model_key: str) -> list[str]:
        """
        Returns list of checked parameters for given model
        """
        def isChecked(row):
            model = self.model_dict[model_key]
            return model.item(row, 0).checkState() == QtCore.Qt.Checked

        model = self.model_dict[model_key]

        if model_key == "poly":
            return [self.polydispersity_widget.polyNameToParam(str(model.item(row_index, 0).text()))
                    for row_index in range(model.rowCount())
                    if isChecked(row_index)]
        else:
            return [str(model.item(row_index, 0).text())
                    for row_index in range(model.rowCount())
                    if isChecked(row_index)]
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
            self.communicate.changeDataExplorerTabSignal.emit(1)

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
        self.communicate.updateTheoryFromPerspectiveSignal.emit(theory_item)

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

    def updateKernelModelWithExtraParams(self, model: Any | None = None) -> None:
        """
        Updates kernel model 'model' with extra parameters from
        the polydisp and magnetism tab, if the tabs are enabled
        """
        if model is None:
            return
        if not hasattr(model, 'setParam'):
            return

        self.polydispersity_widget.updateModel(model)
        # add magnetic params if asked
        self.magnetism_widget.updateModel(model)

    def calculateQGridForModelExt(self, data: Data1D | Data2D | None = None, model: Any | None = None, completefn: Any | None = None, use_threads: bool = True) -> None:
        """
        Wrapper for Calc1D/2D calls
        """
        if data is None:
            data = self.data
        if model is None:
            model = copy.deepcopy(self.logic.kernel_module)
            self.updateKernelModelWithExtraParams(model)

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
            plot.id = "{} [{}] {}".format(data_id[0], plot.name, " ".join(data_id[1:]))
            data_name = fitted_data.name.split()
            plot.name = " ".join([data_name[0], plot.name] + data_name[1:])
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
            self.communicate.deleteIntermediateTheoryPlotsSignal.emit(str(self.tab_id))

        self._appendPlotsPolyDisp(new_plots, return_data, fitted_data)

        # Create plots for intermediate product data
        plots = self.logic.new1DProductPlots(return_data, self.tab_id)
        for plot in plots:
            plot.symbol = "Line"
            self.createNewIndex(plot)
            new_plots.append(plot)

        for plot in new_plots:
            self.communicate.plotUpdateSignal.emit([plot])
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
            self.communicate.plotUpdateSignal.emit([plot])

    def updateEffectiveRadius(self, return_data: dict) -> None:
        """
        Given return data from sasmodels, update the effective radius parameter in the GUI table with the new
        calculated value as returned by sasmodels (if the value was returned).
        """
        ER_mode_row = self.getRowFromName("radius_effective_mode")
        if ER_mode_row is None:
            return
        try:
            ER_mode = int(self._model_model.item(ER_mode_row, 1).text())
        except ValueError:
            logging.error("radius_effective_mode was set to an invalid value.")
            return
        if ER_mode < 1:
            # does not need updating if it is not being computed
            return

        ER_row = self.getRowFromName("radius_effective")
        if ER_row is None:
            return

        scalar_results = self.logic.getScalarIntermediateResults(return_data)
        ER_value = scalar_results.get("radius_effective")
        if ER_value is None:
            return
        # ensure the model does not recompute when updating the value
        self._model_model.blockSignals(True)
        self._model_model.item(ER_row, 1).setText(GuiUtils.formatNumber(ER_value, high=True))
        self._model_model.blockSignals(False)
        # ensure the view is updated immediately
        self._model_model.layoutChanged.emit()

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

    def shellNamesList(self) -> list[str]:
        """
        Returns list of names of all multi-shell parameters
        E.g. for sld[n], radius[n], n=1..3 it will return
        [sld1, sld2, sld3, radius1, radius2, radius3]
        """
        multi_names = [p.name[:p.name.index('[')] for p in self.logic.model_parameters.iq_parameters if '[' in p.name]
        top_index = self.logic.kernel_module.multiplicity_info.number
        shell_names = []
        for i in range(1, top_index+1):
            for name in multi_names:
                shell_names.append(name+str(i))
        return shell_names

    def enableStructureFactorControl(self, structure_factor: str | None) -> None:
        """
        Add structure factors to the list of parameters
        """
        if self.logic.kernel_module.is_form_factor or structure_factor == 'None':
            self.enableStructureCombo()
        else:
            self.disableStructureCombo()

    def addExtraShells(self) -> None:
        """
        Add a combobox for multiple shell display
        """
        param_name, param_length = FittingUtilities.getMultiplicity(self.logic.model_parameters)

        if param_length == 0:
            return

        # cell 1: variable name
        item1 = QtGui.QStandardItem(param_name)

        func = QtWidgets.QComboBox()

        # cell 2: combobox
        item2 = QtGui.QStandardItem()

        # cell 3: min value
        item3 = QtGui.QStandardItem()
        # set the cell to be non-editable
        item3.setFlags(item3.flags() ^ QtCore.Qt.ItemIsEditable)

        # cell 4: max value
        item4 = QtGui.QStandardItem()
        # set the cell to be non-editable
        item4.setFlags(item4.flags() ^ QtCore.Qt.ItemIsEditable)

        # cell 5: SLD button
        item5 = QtGui.QStandardItem()
        button = None
        for p in self.logic.kernel_module.params.keys():
            if re.search(r'^[\w]{0,3}sld.*[1-9]$', p):
                # Only display the SLD Profile button for models with SLD parameters
                button = QtWidgets.QPushButton()
                button.setText("Show SLD Profile")
                # Respond to button press
                button.clicked.connect(self.onShowSLDProfile)
                break

        self._model_model.appendRow([item1, item2, item3, item4, item5])

        # Beautify the row:  span columns 2-4
        shell_row = self._model_model.rowCount()
        shell_index = self._model_model.index(shell_row-1, 1)
        button_index = self._model_model.index(shell_row-1, 4)

        self.lstParams.setIndexWidget(shell_index, func)
        self.lstParams.setIndexWidget(button_index, button)
        self._n_shells_row = shell_row - 1

        # Get the default number of shells for the model
        kernel_pars = self.logic.kernel_module._model_info.parameters.kernel_parameters
        shell_par = None
        for par in kernel_pars:
            parname = par.name
            if '[' in parname:
                 parname = parname[:parname.index('[')]
            if parname == param_name:
                shell_par = par
                break
        if shell_par is None:
            logger.error("Could not find %s in kernel parameters.", param_name)
            return
        default_shell_count = shell_par.default
        shell_min = 0
        shell_max = 0
        try:
            shell_min = int(shell_par.limits[0])
            shell_max = int(shell_par.limits[1])
        except IndexError:
            # no info about limits
            pass
        except OverflowError:
            # Try to limit shell_par, if possible
            if float(shell_par.limits[1])==np.inf:
                shell_max = 9
            logging.warning("Limiting shell count to 9.")
        except Exception as ex:
            logging.error("Badly defined multiplicity: "+ str(ex))
            return
        # don't update the kernel here - this data is display only
        self._model_model.blockSignals(True)
        item3.setText(str(shell_min))
        item4.setText(str(shell_max))
        self._model_model.blockSignals(False)

        ## Respond to index change
        #func.currentTextChanged.connect(self.modifyShellsInList)


        # Available range of shells displayed in the combobox
        func.addItems([str(i) for i in range(shell_min, shell_max+1)])

        # Respond to index change
        func.currentTextChanged.connect(self.modifyShellsInList)

        # Add default number of shells to the model
        func.setCurrentText(str(default_shell_count))
        self.modifyShellsInList(str(default_shell_count))

    def modifyShellsInList(self, text: str) -> None:
        """
        Add/remove additional multishell parameters
        """
        # Find row location of the combobox
        first_row = self._n_shells_row + 1
        remove_rows = self._num_shell_params
        try:
            index = int(text)
        except ValueError:
            # bad text on the control!
            index = 0
            logger.error("Multiplicity incorrect! Setting to 0")
        self.logic.kernel_module.multiplicity = index
        # Copy existing param values before removing rows to retain param values when changing n-shells
        self.clipboard_copy()
        if remove_rows > 1:
            self._model_model.removeRows(first_row, remove_rows)

        new_rows = FittingUtilities.addShellsToModel(
                self.logic.model_parameters,
                self._model_model,
                index,
                first_row,
                self.lstParams)

        self._num_shell_params = len(new_rows)
        self.logic.current_shell_displayed = index

        # Param values for existing shells were reset to default; force all changes into kernel module
        for row in new_rows:
            par = row[0].text()
            val = GuiUtils.toDouble(row[1].text())
            self.logic.kernel_module.setParam(par, val)

        # Change 'n' in the parameter model; also causes recalculation
        self._model_model.item(self._n_shells_row, 1).setText(str(index))

        # Update relevant models
        self.polydispersity_widget.setPolyModel()
        if self.canHaveMagnetism():
            self.magnetism_widget.setMagneticModel()

        self.clipboard_paste()

    def onShowSLDProfile(self) -> None:
        """
        Show a quick plot of SLD profile
        """
        # get profile data
        try:
            x, y = self.logic.kernel_module.getProfile()
        except TypeError:
            msg = "SLD profile calculation failed."
            logging.error(msg)
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
        self.cmdFit.setStyleSheet('QPushButton {color: black;}')
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
        self.cmdFit.setStyleSheet('QPushButton {color: red;}')
        self.cmdFit.setText('Stop fit')
        self.setInteractiveElements(False)

    def disableInteractiveElementsOnCalculate(self) -> None:
        """
        Set button caption on fitting/calculate start
        Disable the param table(s)
        """
        # Notify the user that fitting is being run
        # Allow for stopping the job
        self.cmdFit.setStyleSheet('QPushButton {color: red;}')
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
        fp.main_params_to_fit = self.main_params_to_fit
        fp.poly_params_to_fit = self.polydispersity_widget.poly_params_to_fit
        fp.magnet_params_to_fit = self.magnetism_widget.magnet_params_to_fit
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

    def updateUndo(self) -> None:
        """
        Create a new state page and add it to the stack
        """
        if self.undo_supported:
            self.pushFitPage(self.currentState())

    def currentState(self) -> FitPage:
        """
        Return fit page with current state
        """
        new_page = FitPage()
        self.saveToFitPage(new_page)

        return new_page

    def pushFitPage(self, new_page: FitPage) -> None:
        """
        Add a new fit page object with current state
        """
        self.page_stack.append(new_page)

    def popFitPage(self) -> None:
        """
        Remove top fit page from stack
        """
        if self.page_stack:
            self.page_stack.pop()

    def getReport(self) -> list[str]:
        """
        Create and return HTML report with parameters and charts
        """
        index = None
        if self.all_data:
            index = self.all_data[self.data_index]
        else:
            index = self.theory_item
        params = FittingUtilities.getStandardParam(self._model_model)
        poly_params = []
        magnet_params = []
        if self.chkPolydispersity.isChecked() and self.polydispersity_widget.poly_model.rowCount() > 0:
            poly_params = FittingUtilities.getStandardParam(self.polydispersity_widget.poly_model)
        if self.chkMagnetism.isChecked() and self.canHaveMagnetism() and self.magnetism_widget._magnet_model.rowCount() > 0:
            magnet_params = FittingUtilities.getStandardParam(self.magnetism_widget._magnet_model)
        report_logic = ReportPageLogic(self,
                                       kernel_module=self.logic.kernel_module,
                                       data=self.data,
                                       index=index,
                                       params=params+poly_params+magnet_params)

        return report_logic.reportList()

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
        cb_text = cb.text()

        lines = cb_text.split(':')
        if lines[0] != 'sasview_parameter_values':
            msg = "Clipboard content is incompatible with the Fit Page."
            msgbox = QtWidgets.QMessageBox(self)
            msgbox.setIcon(QtWidgets.QMessageBox.Warning)
            msgbox.setText(msg)
            msgbox.setWindowTitle("Clipboard")
            msgbox.exec_()
            return

        # put the text into dictionary
        line_dict = {}
        for line in lines[1:]:
            content = line.split(',')
            if len(content) > 1 and content[0] != "tab_name":
                line_dict[content[0]] = content[1:]

        self.updatePageWithParameters(line_dict)

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
        serializes combobox state
        """
        param_list = []
        model = str(self.cbModel.currentText())
        category = str(self.cbCategory.currentText())
        structure = str(self.cbStructureFactor.currentText())
        param_list.append(['fitpage_category', category])
        param_list.append(['fitpage_model', model])
        param_list.append(['fitpage_structure', structure])

        return param_list

    def getFitPage(self) -> list[list[str]]:
        """
        serializes full state of this fit page
        """
        # run a loop over all parameters and pull out
        # first - regular params
        param_list = self.getFitParameters()

        param_list.append(['is_data', str(self.data_is_loaded)])
        data_ids = []
        names = []
        if self.is_batch_fitting:
            for item in self.all_data:
                # need item->data->data_id
                data = GuiUtils.dataFromItem(item)
                data_ids.append(data.id)
                names.append(data.name)
        else:
            if self.data_is_loaded:
                data_ids = [str(self.logic.data.id)]
                names = [str(self.logic.data.name)]
        param_list.append(['tab_index', str(self.tab_id)])
        param_list.append(['is_batch_fitting', str(self.is_batch_fitting)])
        param_list.append(['data_name', names])
        param_list.append(['data_id', data_ids])
        param_list.append(['tab_name', self.modelName()])
        # option tab
        param_list.append(['q_range_min', str(self.q_range_min)])
        param_list.append(['q_range_max', str(self.q_range_max)])
        param_list.append(['q_weighting', str(self.weighting)])
        param_list.append(['weighting', str(self.options_widget.weighting)])

        # resolution
        smearing, accuracy, smearing_min, smearing_max = self.smearing_widget.state()
        index = self.smearing_widget.cbSmearing.currentIndex()
        param_list.append(['smearing', str(index)])
        param_list.append(['smearing_min', str(smearing_min)])
        param_list.append(['smearing_max', str(smearing_max)])

        # checkboxes, if required
        has_polydisp = self.chkPolydispersity.isChecked()
        has_magnetism = self.chkMagnetism.isChecked()
        has_chain = self.chkChainFit.isChecked()
        has_2D = self.chk2DView.isChecked()
        param_list.append(['polydisperse_params', str(has_polydisp)])
        param_list.append(['magnetic_params', str(has_magnetism)])
        param_list.append(['chainfit_params', str(has_chain)])
        param_list.append(['2D_params', str(has_2D)])

        return param_list

    def getFitParameters(self) -> list[list[str | tuple]]:
        """
        serializes current parameters
        """
        param_list = []
        if self.logic.kernel_module is None:
            return param_list

        param_list.append(['model_name', str(self.cbModel.currentText())])

        def gatherParams(row):
            """
            Create list of main parameters based on _model_model
            """
            param_name = str(self._model_model.item(row, 0).text())
            model = self._model_model
            if model.item(row, 0) is None:
                return
            # Assure this is a parameter - must contain a checkbox
            if not model.item(row, 0).isCheckable():
                param_checked = None
            else:
                param_checked = str(model.item(row, 0).checkState() == QtCore.Qt.Checked)
            # Value of the parameter. In some cases this is the text of the combobox choice.
            param_value = str(model.item(row, 1).text())
            param_error = None
            _, param_min, param_max = self.logic.kernel_module.details.get(param_name, ('', None, None))
            column_offset = 0
            if self.has_error_column:
                column_offset = 1
                param_error = str(model.item(row, 1+column_offset).text())
            try:
                param_min = str(model.item(row, 2+column_offset).text())
                param_max = str(model.item(row, 3+column_offset).text())
            except Exception:
                pass
            # Do we have any constraints on this parameter?
            constraint = self.getConstraintForRow(row, model_key="standard")
            cons = ()
            if constraint is not None:
                value = constraint.value
                func = constraint.func
                value_ex = constraint.value_ex
                param = constraint.param
                validate = constraint.validate

                cons = (value, param, value_ex, validate, func)

            param_list.append([param_name, param_checked, param_value,param_error, param_min, param_max, cons])

        def gatherPolyParams(row):
            """
            Create list of polydisperse parameters based on _poly_model
            """
            param_list.extend(self.polydispersity_widget.gatherPolyParams(row))

        def gatherMagnetParams(row):
            """
            Create list of magnetic parameters based on _magnet_model
            """
            param_list.extend(self.magnetism_widget.gatherMagnetParams(row))

        self.iterateOverModel(gatherParams)
        if self.chkPolydispersity.isChecked():
            self.polydispersity_widget.iterateOverPolyModel(gatherPolyParams)
        if self.chkMagnetism.isChecked() and self.canHaveMagnetism():
            self.magnetism_widget.iterateOverMagnetModel(gatherMagnetParams)

        if self.logic.kernel_module.is_multiplicity_model:
            param_list.append(['multiplicity', str(self.logic.kernel_module.multiplicity)])

        return param_list

    def createPageForParameters(self, line_dict: dict[str, list[str]]) -> None:
        """
        Sets up page with requested model/str factor
        and fills it up with sent parameters
        """
        if 'fitpage_category' in line_dict:
            self.cbCategory.setCurrentIndex(self.cbCategory.findText(line_dict['fitpage_category'][0]))
        if 'fitpage_model' in line_dict:
            self.cbModel.setCurrentIndex(self.cbModel.findText(line_dict['fitpage_model'][0]))
        if 'fitpage_structure' in line_dict:
            self.cbStructureFactor.setCurrentIndex(self.cbStructureFactor.findText(line_dict['fitpage_structure'][0]))

        # Now that the page is ready for parameters, fill it up
        self.updatePageWithParameters(line_dict)

    def updatePageWithParameters(self, line_dict: dict[str, list[str]], warn_user: bool = True) -> None:
        """
        Update FitPage with parameters in line_dict
        """
        if 'model_name' not in line_dict:
            return
        model = line_dict['model_name'][0]
        context = {}

        if 'multiplicity' in line_dict:
            multip = int(line_dict['multiplicity'][0], 0)
            # reset the model with multiplicity, so further updates are saved
            if self.logic.kernel_module.is_multiplicity_model:
                self.logic.kernel_module.multiplicity=multip
                self.updateMultiplicityCombo(multip)

        if 'tab_name' in line_dict and self.logic.kernel_module is not None:
            self.logic.kernel_module.name = line_dict['tab_name'][0]
        if 'polydisperse_params' in line_dict:
            self.chkPolydispersity.setChecked(line_dict['polydisperse_params'][0]=='True')
        if 'magnetic_params' in line_dict:
            self.chkMagnetism.setChecked(line_dict['magnetic_params'][0]=='True')
        if 'chainfit_params' in line_dict:
            self.chkChainFit.setChecked(line_dict['chainfit_params'][0]=='True')
        if '2D_params' in line_dict:
            self.chk2DView.setChecked(line_dict['2D_params'][0]=='True')

        # Create the context dictionary for parameters
        # Exclude multiplicity and number of shells params from context
        context = {k: v for (k, v) in line_dict.items() if len(v) > 3 and k != model}
        context['model_name'] = model

        if warn_user and str(self.cbModel.currentText()) != str(context['model_name']):
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Information)
            msg.setText("The model in the clipboard is not the same as the currently loaded model. \
                         Not all parameters saved may paste correctly.")
            msg.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
            result = msg.exec_()
            if result == QtWidgets.QMessageBox.Ok:
                pass
            else:
                return

        if 'smearing' in line_dict:
            try:
                index = int(line_dict['smearing'][0])
                self.smearing_widget.cbSmearing.setCurrentIndex(index)
            except ValueError:
                pass
        if 'smearing_min' in line_dict:
            try:
                self.smearing_widget.dq_r = float(line_dict['smearing_min'][0])
            except ValueError:
                pass
        if 'smearing_max' in line_dict:
            try:
                self.smearing_widget.dq_l = float(line_dict['smearing_max'][0])
            except ValueError:
                pass

        if 'q_range_max' in line_dict:
            try:
                self.q_range_min = float(line_dict['q_range_min'][0])
                self.q_range_max = float(line_dict['q_range_max'][0])
            except ValueError:
                pass
        self.options_widget.updateQRange(self.q_range_min, self.q_range_max, self.npts)
        try:
            if 'weighting' in line_dict:
                button_id = int(line_dict['weighting'][0])
                for button in self.options_widget.weightingGroup.buttons():
                    if abs(self.options_widget.weightingGroup.id(button)) == button_id+2:
                        button.setChecked(True)
                        break
        except ValueError:
            pass

        self.updateFullModel(context)
        self.polydispersity_widget.updateFullPolyModel(context)
        self.magnetism_widget.updateFullMagnetModel(context)

    def updateMultiplicityCombo(self, multip: int) -> None:
        """
        Find and update the multiplicity combobox
        """
        index = self._model_model.index(self._n_shells_row, 1)
        widget = self.lstParams.indexWidget(index)
        if widget is not None and isinstance(widget, QtWidgets.QComboBox):
            widget.setCurrentIndex(widget.findText(str(multip)))
        self.logic.current_shell_displayed = multip

    def updateFullModel(self, param_dict: dict[str, list[str]]) -> None:
        """
        Update the model with new parameters
        """
        assert isinstance(param_dict, dict)

        def updateFittedValues(row):
            # Utility function for main model update
            # internal so can use closure for param_dict
            param_name = str(self._model_model.item(row, 0).text())
            if param_name not in list(param_dict.keys()) or row == self._n_shells_row:
                # Skip magnetic, polydisperse (.pd), and shell parameters - they are handled elsewhere
                return
            # checkbox state
            param_checked = QtCore.Qt.Checked if param_dict[param_name][0] == "True" else QtCore.Qt.Unchecked
            self._model_model.item(row, 0).setCheckState(param_checked)

            # parameter value can be either just a value or text on the combobox
            param_text = param_dict[param_name][1]
            index = self._model_model.index(row, 1)
            widget = self.lstParams.indexWidget(index)
            if widget is not None and isinstance(widget, QtWidgets.QComboBox):
                # Find the right index based on text
                combo_index = int(param_text, 0)
                widget.setCurrentIndex(combo_index)
            else:
                # modify the param value
                param_repr = GuiUtils.formatNumber(param_text, high=True)
                self._model_model.item(row, 1).setText(param_repr)

            # Potentially the error column
            ioffset = 0
            joffset = 0
            if len(param_dict[param_name])>5:
                # error values are not editable - no need to update
                ioffset = 1
            if self.has_error_column:
                joffset = 1
            # min/max
            try:
                self._model_model.item(row, 2+joffset).setText(param_dict[param_name][2+ioffset])
                self._model_model.item(row, 3+joffset).setText(param_dict[param_name][3+ioffset])
            except: # noqa: E722
                pass

            self.setFocus()

        self.iterateOverModel(updateFittedValues)

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
        # Comboboxes
        state.categorycombobox = self.cbCategory.currentText()
        state.formfactorcombobox = self.cbModel.currentText()
        if self.cbStructureFactor.isEnabled():
            state.structurecombobox = self.cbStructureFactor.currentText()
        state.tcChi = self.chi2

        state.enable2D = self.is2D

        # save data
        state.data = copy.deepcopy(self.data)

        # save plotting range
        state.qmin = self.q_range_min
        state.qmax = self.q_range_max
        state.npts = self.npts

        # save checkbutton state and txtcrtl values
        state.parameters = FittingUtilities.getStandardParam(self._model_model)
        state.orientation_params_disp = FittingUtilities.getOrientationParam(self.logic.kernel_module)

    def getSymbolDict(self) -> dict[str, float]:
        """
        Return a dict containing a list of all the symbols used for fitting
        and their values, e.g. {'M1.scale':1, 'M1.background': 0.001}
        """
        sym_dict = {}
        # return an empty dict if no model has been selected
        if self.logic.kernel_module is None:
            return sym_dict
        model_name = self.logic.kernel_module.name
        for param in self.getParamNames():
            model_key = self.getModelKeyFromName(param)
            sym_dict[f"{model_name}.{param}"] = GuiUtils.toDouble(
                self.model_dict[model_key].item(self.getRowFromName(param), 1).text())
        return sym_dict
