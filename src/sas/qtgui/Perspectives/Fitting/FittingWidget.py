import json
import os
import sys
from collections import defaultdict

import copy
import logging
import traceback
from twisted.internet import threads
import numpy as np
import webbrowser

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from sasmodels import generate
from sasmodels import modelinfo
from sasmodels.sasview_model import load_standard_models
from sasmodels.sasview_model import MultiplicationModel
from sasmodels.weights import MODELS as POLYDISPERSITY_MODELS

from sas.sascalc.fit.BumpsFitting import BumpsFit as Fit
from sas.sascalc.fit.pagestate import PageState

import sas.qtgui.Utilities.GuiUtils as GuiUtils
import sas.qtgui.Utilities.LocalConfig as LocalConfig
from sas.qtgui.Utilities.CategoryInstaller import CategoryInstaller
from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Plotting.PlotterData import Data2D
from sas.qtgui.Plotting.Plotter import PlotterWidget

from sas.qtgui.Perspectives.Fitting.UI.FittingWidgetUI import Ui_FittingWidgetUI
from sas.qtgui.Perspectives.Fitting.FitThread import FitThread
from sas.qtgui.Perspectives.Fitting.ConsoleUpdate import ConsoleUpdate

from sas.qtgui.Perspectives.Fitting.ModelThread import Calc1D
from sas.qtgui.Perspectives.Fitting.ModelThread import Calc2D
from sas.qtgui.Perspectives.Fitting.FittingLogic import FittingLogic
from sas.qtgui.Perspectives.Fitting import FittingUtilities
from sas.qtgui.Perspectives.Fitting import ModelUtilities
from sas.qtgui.Perspectives.Fitting.SmearingWidget import SmearingWidget
from sas.qtgui.Perspectives.Fitting.OptionsWidget import OptionsWidget
from sas.qtgui.Perspectives.Fitting.FitPage import FitPage
from sas.qtgui.Perspectives.Fitting.ViewDelegate import ModelViewDelegate
from sas.qtgui.Perspectives.Fitting.ViewDelegate import PolyViewDelegate
from sas.qtgui.Perspectives.Fitting.ViewDelegate import MagnetismViewDelegate
from sas.qtgui.Perspectives.Fitting.Constraint import Constraint
from sas.qtgui.Perspectives.Fitting.MultiConstraint import MultiConstraint
from sas.qtgui.Perspectives.Fitting.ReportPageLogic import ReportPageLogic
from sas.qtgui.Perspectives.Fitting.OrderWidget import OrderWidget

TAB_MAGNETISM = 4
TAB_POLY = 3
TAB_ORDERING = 5
CATEGORY_DEFAULT = "Choose category..."
MODEL_DEFAULT = "Choose model..."
CATEGORY_STRUCTURE = "Structure Factor"
CATEGORY_CUSTOM = "Plugin Models"
STRUCTURE_DEFAULT = "None"

DEFAULT_POLYDISP_FUNCTION = 'gaussian'

# CRUFT: remove when new release of sasmodels is available
# https://github.com/SasView/sasview/pull/181#discussion_r218135162
from sasmodels.sasview_model import SasviewModel
if not hasattr(SasviewModel, 'get_weights'):
    def get_weights(self, name):
        """
        Returns the polydispersity distribution for parameter *name* as *value* and *weight* arrays.
        """
        # type: (str) -> Tuple(np.ndarray, np.ndarray)
        _, x, w = self._get_weights(self._model_info.parameters[name])
        return x, w

    SasviewModel.get_weights = get_weights

logger = logging.getLogger(__name__)

class ToolTippedItemModel(QtGui.QStandardItemModel):
    """
    Subclass from QStandardItemModel to allow displaying tooltips in
    QTableView model.
    """
    def __init__(self, parent=None):
        QtGui.QStandardItemModel.__init__(self, parent)

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        """
        Displays tooltip for each column's header
        :param section:
        :param orientation:
        :param role:
        :return:
        """
        if role == QtCore.Qt.ToolTipRole:
            if orientation == QtCore.Qt.Horizontal:
                return str(self.header_tooltips[section])

        return QtGui.QStandardItemModel.headerData(self, section, orientation, role)

class FittingWidget(QtWidgets.QWidget, Ui_FittingWidgetUI):
    """
    Main widget for selecting form and structure factor models
    """
    constraintAddedSignal = QtCore.pyqtSignal(list)
    newModelSignal = QtCore.pyqtSignal()
    fittingFinishedSignal = QtCore.pyqtSignal(tuple)
    batchFittingFinishedSignal = QtCore.pyqtSignal(tuple)
    Calc1DFinishedSignal = QtCore.pyqtSignal(dict)
    Calc2DFinishedSignal = QtCore.pyqtSignal(dict)

    MAGNETIC_MODELS = ['sphere', 'core_shell_sphere', 'core_multi_shell', 'cylinder', 'parallelepiped']

    def __init__(self, parent=None, data=None, tab_id=1):

        super(FittingWidget, self).__init__()

        # Necessary globals
        self.parent = parent

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
            self.data = data

        # New font to display angstrom symbol
        new_font = 'font-family: -apple-system, "Helvetica Neue", "Ubuntu";'
        self.label_17.setStyleSheet(new_font)
        self.label_19.setStyleSheet(new_font)

    def info(self, type, value, tb):
        logger.error("SasView threw exception: " + str(value))
        traceback.print_exception(type, value, tb)

    @property
    def logic(self):
        # make sure the logic contains at least one element
        assert self._logic
        # logic connected to the currently shown data
        return self._logic[self.data_index]

    @property
    def data(self):
        return self.logic.data

    @data.setter
    def data(self, value):
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
            # update the ordering tab
            self.order_widget.updateData(self.all_data)

        # Overwrite data type descriptor

        self.is2D = True if isinstance(self.logic.data, Data2D) else False

        # Let others know we're full of data now
        self.data_is_loaded = True

        # Enable/disable UI components
        self.setEnablementOnDataLoad()

    def initializeGlobals(self):
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
        # Current SasModel in view
        self.kernel_module = None
        # Current SasModel view dimension
        self.is2D = False
        # Current SasModel is multishell
        self.model_has_shells = False
        # Utility variable to enable unselectable option in category combobox
        self._previous_category_index = 0
        # Utility variables for multishell display
        self._n_shells_row = 0
        self._num_shell_params = 0
        # Dictionary of {model name: model class} for the current category
        self.models = {}
        # Parameters to fit
        self.main_params_to_fit = []
        self.poly_params_to_fit = []
        self.magnet_params_to_fit = []

        # Fit options
        self.q_range_min = OptionsWidget.QMIN_DEFAULT
        self.q_range_max = OptionsWidget.QMAX_DEFAULT
        self.npts = OptionsWidget.NPTS_DEFAULT
        self.log_points = False
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
        # Polydisp widget table default index for function combobox
        self.orig_poly_index = 4
        # copy of current kernel model
        self.kernel_module_copy = None

        # dictionaries of current params
        self.poly_params = {}
        self.magnet_params = {}

        # Page id for fitting
        # To keep with previous SasView values, use 200 as the start offset
        self.page_id = 200 + self.tab_id

        # Data for chosen model
        self.model_data = None
        self._previous_model_index = 0

        # Which shell is being currently displayed?
        self.current_shell_displayed = 0
        # List of all shell-unique parameters
        self.shell_names = []

        # Error column presence in parameter display
        self.has_error_column = False
        self.has_poly_error_column = False
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

        # signal communicator
        self.communicate = self.parent.communicate

    def initializeWidgets(self):
        """
        Initialize widgets for tabs
        """
        # Options widget
        layout = QtWidgets.QGridLayout()
        self.options_widget = OptionsWidget(self, self.logic)
        layout.addWidget(self.options_widget)
        self.tabOptions.setLayout(layout)

        # Smearing widget
        layout = QtWidgets.QGridLayout()
        self.smearing_widget = SmearingWidget(self)
        layout.addWidget(self.smearing_widget)
        self.tabResolution.setLayout(layout)

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

        # Magnetic angles explained in one picture
        self.magneticAnglesWidget = QtWidgets.QWidget()
        labl = QtWidgets.QLabel(self.magneticAnglesWidget)
        pixmap = QtGui.QPixmap(GuiUtils.IMAGES_DIRECTORY_LOCATION + '/M_angles_pic.png')
        labl.setPixmap(pixmap)
        self.magneticAnglesWidget.setFixedSize(pixmap.width(), pixmap.height())

    def initializeModels(self):
        """
        Set up models and views
        """
        # Set the main models
        # We can't use a single model here, due to restrictions on flattening
        # the model tree with subclassed QAbstractProxyModel...
        self._model_model = ToolTippedItemModel()
        self._poly_model = ToolTippedItemModel()
        self._magnet_model = ToolTippedItemModel()

        # Param model displayed in param list
        self.lstParams.setModel(self._model_model)
        self.readCategoryInfo()

        self.model_parameters = None

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
        self.lstPoly.setModel(self._poly_model)
        self.setPolyModel()
        self.setTableProperties(self.lstPoly)
        # Delegates for custom editing and display
        self.lstPoly.setItemDelegate(PolyViewDelegate(self))
        # Polydispersity function combo response
        self.lstPoly.itemDelegate().combo_updated.connect(self.onPolyComboIndexChange)
        self.lstPoly.itemDelegate().filename_updated.connect(self.onPolyFilenameChange)

        # Magnetism model displayed in magnetism list
        self.lstMagnetic.setModel(self._magnet_model)
        self.setMagneticModel()
        self.setTableProperties(self.lstMagnetic)
        # Delegates for custom editing and display
        self.lstMagnetic.setItemDelegate(MagnetismViewDelegate(self))
        # Initial status of the ordering tab - invisible
        self.tabFitting.removeTab(TAB_ORDERING)

    def initializeCategoryCombo(self):
        """
        Model category combo setup
        """
        category_list = sorted(self.master_category_dict.keys())
        self.cbCategory.addItem(CATEGORY_DEFAULT)
        self.cbCategory.addItems(category_list)
        if CATEGORY_STRUCTURE not in category_list:
            self.cbCategory.addItem(CATEGORY_STRUCTURE)
        self.cbCategory.setCurrentIndex(0)

    def setEnablementOnDataLoad(self):
        """
        Enable/disable various UI elements based on data loaded
        """
        # Tag along functionality
        self.label.setText("Data loaded from: ")
        if self.logic.data.filename:
            self.lblFilename.setText(self.logic.data.filename)
        else:
            self.lblFilename.setText(self.logic.data.name)
        self.updateQRange()
        # Switch off Data2D control
        self.chk2DView.setEnabled(False)
        self.chk2DView.setVisible(False)
        self.chkMagnetism.setEnabled(False)
        self.tabFitting.setTabEnabled(TAB_MAGNETISM, self.chkMagnetism.isChecked())
        # Combo box or label for file name"
        if self.is_batch_fitting:
            self.lblFilename.setVisible(False)
            for dataitem in self.all_data:
                filename = GuiUtils.dataFromItem(dataitem).filename
                self.cbFileNames.addItem(filename)
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

    def acceptsData(self):
        """ Tells the caller this widget can accept new dataset """
        return not self.data_is_loaded

    def disableModelCombo(self):
        """ Disable the combobox """
        self.cbModel.setEnabled(False)
        self.lblModel.setEnabled(False)
        self.enabled_cbmodel = False

    def enableModelCombo(self):
        """ Enable the combobox """
        self.cbModel.setEnabled(True)
        self.lblModel.setEnabled(True)
        self.enabled_cbmodel = True

    def disableStructureCombo(self):
        """ Disable the combobox """
        self.cbStructureFactor.setEnabled(False)
        self.lblStructure.setEnabled(False)
        self.enabled_sfmodel = False

    def enableStructureCombo(self):
        """ Enable the combobox """
        self.cbStructureFactor.setEnabled(True)
        self.lblStructure.setEnabled(True)
        self.enabled_sfmodel = True

    def togglePoly(self, isChecked):
        """ Enable/disable the polydispersity tab """
        self.tabFitting.setTabEnabled(TAB_POLY, isChecked)
        # Check if any parameters are ready for fitting
        self.cmdFit.setEnabled(self.haveParamsToFit())

    def toggleMagnetism(self, isChecked):
        """ Enable/disable the magnetism tab """
        self.tabFitting.setTabEnabled(TAB_MAGNETISM, isChecked)
        # Check if any parameters are ready for fitting
        self.cmdFit.setEnabled(self.haveParamsToFit())

    def toggleChainFit(self, isChecked):
        """ Enable/disable chain fitting """
        self.is_chain_fitting = isChecked
        # show/hide the ordering tab
        if isChecked:
            self.tabFitting.insertTab(TAB_ORDERING, self.tabOrder, "Order")
        else:
            self.tabFitting.removeTab(TAB_ORDERING)

    def toggle2D(self, isChecked):
        """ Enable/disable the controls dependent on 1D/2D data instance """
        self.chkMagnetism.setEnabled(isChecked)
        self.is2D = isChecked
        # Reload the current model
        if self.kernel_module:
            self.onSelectModel()

    @classmethod
    def customModels(cls):
        """ Reads in file names in the custom plugin directory """
        return ModelUtilities._find_models()

    def initializeControls(self):
        """
        Set initial control enablement
        """
        self.cbFileNames.setVisible(False)
        self.cmdFit.setEnabled(False)
        self.cmdPlot.setEnabled(False)
        self.chkPolydispersity.setEnabled(True)
        self.chkPolydispersity.setCheckState(False)
        self.chk2DView.setEnabled(True)
        self.chk2DView.setCheckState(False)
        self.chkMagnetism.setEnabled(False)
        self.chkMagnetism.setCheckState(False)
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

    def initializeSignals(self):
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
        self.cmdMagneticDisplay.clicked.connect(self.onDisplayMagneticAngles)

        # Respond to change in parameters from the UI
        self._model_model.dataChanged.connect(self.onMainParamsChange)
        self._poly_model.dataChanged.connect(self.onPolyModelChange)
        self._magnet_model.dataChanged.connect(self.onMagnetModelChange)
        self.lstParams.selectionModel().selectionChanged.connect(self.onSelectionChanged)

        # Local signals
        self.batchFittingFinishedSignal.connect(self.batchFitComplete)
        self.fittingFinishedSignal.connect(self.fitComplete)
        self.Calc1DFinishedSignal.connect(self.complete1D)
        self.Calc2DFinishedSignal.connect(self.complete2D)

        # Signals from separate tabs asking for replot
        self.options_widget.plot_signal.connect(self.onOptionsUpdate)

        # Signals from other widgets
        self.communicate.customModelDirectoryChanged.connect(self.onCustomModelChange)
        self.smearing_widget.smearingChangedSignal.connect(self.onSmearingOptionsUpdate)

        # Communicator signal
        self.communicate.updateModelCategoriesSignal.connect(self.onCategoriesChanged)
        self.communicate.updateMaskedDataSignal.connect(self.onMaskedData)

    def modelName(self):
        """
        Returns model name, by default M<tab#>, e.g. M1, M2
        """
        return "M%i" % self.tab_id

    def nameForFittedData(self, name):
        """
        Generate name for the current fit
        """
        if self.is2D:
            name += "2d"
        name = "%s [%s]" % (self.modelName(), name)
        return name

    def showModelContextMenu(self, position):
        """
        Show context specific menu in the parameter table.
        When clicked on parameter(s): fitting/constraints options
        When clicked on white space: model description
        """
        rows = [s.row() for s in self.lstParams.selectionModel().selectedRows()
                if self.isCheckable(s.row())]
        menu = self.showModelDescription() if not rows else self.modelContextMenu(rows)
        try:
            menu.exec_(self.lstParams.viewport().mapToGlobal(position))
        except AttributeError as ex:
            logger.error("Error generating context menu: %s" % ex)
        return

    def modelContextMenu(self, rows):
        """
        Create context menu for the parameter selection
        """
        menu = QtWidgets.QMenu()
        num_rows = len(rows)
        if num_rows < 1:
            return menu
        # Select for fitting
        param_string = "parameter " if num_rows == 1 else "parameters "
        to_string = "to its current value" if num_rows == 1 else "to their current values"
        has_constraints = any([self.rowHasConstraint(i) for i in rows])
        has_real_constraints = any([self.rowHasActiveConstraint(i) for i in rows])

        self.actionSelect = QtWidgets.QAction(self)
        self.actionSelect.setObjectName("actionSelect")
        self.actionSelect.setText(QtCore.QCoreApplication.translate("self", "Select "+param_string+" for fitting"))
        # Unselect from fitting
        self.actionDeselect = QtWidgets.QAction(self)
        self.actionDeselect.setObjectName("actionDeselect")
        self.actionDeselect.setText(QtCore.QCoreApplication.translate("self", "De-select "+param_string+" from fitting"))

        self.actionConstrain = QtWidgets.QAction(self)
        self.actionConstrain.setObjectName("actionConstrain")
        self.actionConstrain.setText(QtCore.QCoreApplication.translate("self", "Constrain "+param_string + to_string))

        self.actionRemoveConstraint = QtWidgets.QAction(self)
        self.actionRemoveConstraint.setObjectName("actionRemoveConstrain")
        self.actionRemoveConstraint.setText(QtCore.QCoreApplication.translate("self", "Remove constraint"))

        self.actionEditConstraint = QtWidgets.QAction(self)
        self.actionEditConstraint.setObjectName("actionEditConstrain")
        self.actionEditConstraint.setText(QtCore.QCoreApplication.translate("self", "Edit constraint"))

        self.actionMultiConstrain = QtWidgets.QAction(self)
        self.actionMultiConstrain.setObjectName("actionMultiConstrain")
        self.actionMultiConstrain.setText(QtCore.QCoreApplication.translate("self", "Constrain selected parameters to their current values"))

        self.actionMutualMultiConstrain = QtWidgets.QAction(self)
        self.actionMutualMultiConstrain.setObjectName("actionMutualMultiConstrain")
        self.actionMutualMultiConstrain.setText(QtCore.QCoreApplication.translate("self", "Mutual constrain of selected parameters..."))

        menu.addAction(self.actionSelect)
        menu.addAction(self.actionDeselect)
        menu.addSeparator()

        if has_constraints:
            menu.addAction(self.actionRemoveConstraint)
            if num_rows == 1 and has_real_constraints:
                menu.addAction(self.actionEditConstraint)
            #if num_rows == 1:
            #    menu.addAction(self.actionEditConstraint)
        else:
            menu.addAction(self.actionConstrain)
            if num_rows == 2:
                menu.addAction(self.actionMutualMultiConstrain)

        # Define the callbacks
        self.actionConstrain.triggered.connect(self.addSimpleConstraint)
        self.actionRemoveConstraint.triggered.connect(self.deleteConstraint)
        self.actionEditConstraint.triggered.connect(self.editConstraint)
        self.actionMutualMultiConstrain.triggered.connect(self.showMultiConstraint)
        self.actionSelect.triggered.connect(self.selectParameters)
        self.actionDeselect.triggered.connect(self.deselectParameters)
        return menu

    def showMultiConstraint(self):
        """
        Show the constraint widget and receive the expression
        """
        selected_rows = self.lstParams.selectionModel().selectedRows()
        # There have to be only two rows selected. The caller takes care of that
        # but let's check the correctness.
        assert len(selected_rows) == 2

        params_list = [s.data() for s in selected_rows]
        # Create and display the widget for param1 and param2
        mc_widget = MultiConstraint(self, params=params_list)
        # Check if any of the parameters are polydisperse
        if not np.any([FittingUtilities.isParamPolydisperse(p, self.model_parameters, is2D=self.is2D) for p in params_list]):
            # no parameters are pd - reset the text to not show the warning
            mc_widget.lblWarning.setText("")
        if mc_widget.exec_() != QtWidgets.QDialog.Accepted:
            return

        constraint = Constraint()
        c_text = mc_widget.txtConstraint.text()

        # widget.params[0] is the parameter we're constraining
        constraint.param = mc_widget.params[0]
        # parameter should have the model name preamble
        model_name = self.kernel_module.name
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
        self.addConstraintToRow(constraint=constraint, row=row)

    def getRowFromName(self, name):
        """
        Given parameter name get the row number in self._model_model
        """
        for row in range(self._model_model.rowCount()):
            row_name = self._model_model.item(row).text()
            if row_name == name:
                return row
        return None

    def getParamNames(self):
        """
        Return list of all parameters for the current model
        """
        return [self._model_model.item(row).text()
                for row in range(self._model_model.rowCount())
                if self.isCheckable(row)]

    def modifyViewOnRow(self, row, font=None, brush=None):
        """
        Chage how the given row of the main model is shown
        """
        fields_enabled = False
        if font is None:
            font = QtGui.QFont()
            fields_enabled = True
        if brush is None:
            brush = QtGui.QBrush()
            fields_enabled = True
        self._model_model.blockSignals(True)
        # Modify font and foreground of affected rows
        for column in range(0, self._model_model.columnCount()):
            self._model_model.item(row, column).setForeground(brush)
            self._model_model.item(row, column).setFont(font)
            self._model_model.item(row, column).setEditable(fields_enabled)
        self._model_model.blockSignals(False)

    def addConstraintToRow(self, constraint=None, row=0):
        """
        Adds the constraint object to requested row
        """
        # Create a new item and add the Constraint object as a child
        assert isinstance(constraint, Constraint)
        assert 0 <= row <= self._model_model.rowCount()
        assert self.isCheckable(row)

        item = QtGui.QStandardItem()
        item.setData(constraint)
        self._model_model.item(row, 1).setChild(0, item)
        # Set min/max to the value constrained
        self.constraintAddedSignal.emit([row])
        # Show visual hints for the constraint
        font = QtGui.QFont()
        font.setItalic(True)
        brush = QtGui.QBrush(QtGui.QColor('blue'))
        self.modifyViewOnRow(row, font=font, brush=brush)
        self.communicate.statusBarUpdateSignal.emit('Constraint added')

    def addSimpleConstraint(self):
        """
        Adds a constraint on a single parameter.
        """
        min_col = self.lstParams.itemDelegate().param_min
        max_col = self.lstParams.itemDelegate().param_max
        for row in self.selectedParameters():
            assert(self.isCheckable(row))
            param = self._model_model.item(row, 0).text()
            value = self._model_model.item(row, 1).text()
            min_t = self._model_model.item(row, min_col).text()
            max_t = self._model_model.item(row, max_col).text()
            # Create a Constraint object
            constraint = Constraint(param=param, value=value, min=min_t, max=max_t)
            # Create a new item and add the Constraint object as a child
            item = QtGui.QStandardItem()
            item.setData(constraint)
            self._model_model.item(row, 1).setChild(0, item)
            # Assumed correctness from the validator
            value = float(value)
            # BUMPS calculates log(max-min) without any checks, so let's assign minor range
            min_v = value - (value/10000.0)
            max_v = value + (value/10000.0)
            # Set min/max to the value constrained
            self._model_model.item(row, min_col).setText(str(min_v))
            self._model_model.item(row, max_col).setText(str(max_v))
            self.constraintAddedSignal.emit([row])
            # Show visual hints for the constraint
            font = QtGui.QFont()
            font.setItalic(True)
            brush = QtGui.QBrush(QtGui.QColor('blue'))
            self.modifyViewOnRow(row, font=font, brush=brush)
        self.communicate.statusBarUpdateSignal.emit('Constraint added')

    def editConstraint(self):
        """
        Delete constraints from selected parameters.
        """
        params_list = [s.data() for s in self.lstParams.selectionModel().selectedRows()
                   if self.isCheckable(s.row())]
        assert len(params_list) == 1
        row = self.lstParams.selectionModel().selectedRows()[0].row()
        constraint = self.getConstraintForRow(row)
        # Create and display the widget for param1 and param2
        mc_widget = MultiConstraint(self, params=params_list, constraint=constraint)
        # Check if any of the parameters are polydisperse
        if not np.any([FittingUtilities.isParamPolydisperse(p, self.model_parameters, is2D=self.is2D) for p in params_list]):
            # no parameters are pd - reset the text to not show the warning
            mc_widget.lblWarning.setText("")
        if mc_widget.exec_() != QtWidgets.QDialog.Accepted:
            return

        constraint = Constraint()
        c_text = mc_widget.txtConstraint.text()

        # widget.params[0] is the parameter we're constraining
        constraint.param = mc_widget.params[0]
        # parameter should have the model name preamble
        model_name = self.kernel_module.name
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
        row = self.getRowFromName(constraint.param)

        # Create a new item and add the Constraint object as a child
        self.addConstraintToRow(constraint=constraint, row=row)

    def deleteConstraint(self):
        """
        Delete constraints from selected parameters.
        """
        params = [s.data() for s in self.lstParams.selectionModel().selectedRows()
                   if self.isCheckable(s.row())]
        for param in params:
            self.deleteConstraintOnParameter(param=param)

    def deleteConstraintOnParameter(self, param=None):
        """
        Delete the constraint on model parameter 'param'
        """
        min_col = self.lstParams.itemDelegate().param_min
        max_col = self.lstParams.itemDelegate().param_max
        for row in range(self._model_model.rowCount()):
            if not self.isCheckable(row):
                continue
            if not self.rowHasConstraint(row):
                continue
            # Get the Constraint object from of the model item
            item = self._model_model.item(row, 1)
            constraint = self.getConstraintForRow(row)
            if constraint is None:
                continue
            if not isinstance(constraint, Constraint):
                continue
            if param and constraint.param != param:
                continue
            # Now we got the right row. Delete the constraint and clean up
            # Retrieve old values and put them on the model
            if constraint.min is not None:
                self._model_model.item(row, min_col).setText(constraint.min)
            if constraint.max is not None:
                self._model_model.item(row, max_col).setText(constraint.max)
            # Remove constraint item
            item.removeRow(0)
            self.constraintAddedSignal.emit([row])
            self.modifyViewOnRow(row)

        self.communicate.statusBarUpdateSignal.emit('Constraint removed')

    def getConstraintForRow(self, row):
        """
        For the given row, return its constraint, if any (otherwise None)
        """
        if not self.isCheckable(row):
            return None
        item = self._model_model.item(row, 1)
        try:
            return item.child(0).data()
        except AttributeError:
            return None

    def allParamNames(self):
        """
        Returns a list of all parameter names defined on the current model
        """
        all_params = self.kernel_module._model_info.parameters.kernel_parameters
        all_param_names = [param.name for param in all_params]
        # Assure scale and background are always included
        if 'scale' not in all_param_names:
            all_param_names.append('scale')
        if 'background' not in all_param_names:
            all_param_names.append('background')
        return all_param_names

    def paramHasConstraint(self, param=None):
        """
        Finds out if the given parameter in the main model has a constraint child
        """
        if param is None: return False
        if param not in self.allParamNames(): return False

        for row in range(self._model_model.rowCount()):
            if self._model_model.item(row,0).text() != param: continue
            return self.rowHasConstraint(row)

        # nothing found
        return False

    def rowHasConstraint(self, row):
        """
        Finds out if row of the main model has a constraint child
        """
        if not self.isCheckable(row):
            return False
        item = self._model_model.item(row, 1)
        if not item.hasChildren():
            return False
        c = item.child(0).data()
        if isinstance(c, Constraint):
            return True
        return False

    def rowHasActiveConstraint(self, row):
        """
        Finds out if row of the main model has an active constraint child
        """
        if not self.isCheckable(row):
            return False
        item = self._model_model.item(row, 1)
        if not item.hasChildren():
            return False
        c = item.child(0).data()
        if isinstance(c, Constraint) and c.active:
            return True
        return False

    def rowHasActiveComplexConstraint(self, row):
        """
        Finds out if row of the main model has an active, nontrivial constraint child
        """
        if not self.isCheckable(row):
            return False
        item = self._model_model.item(row, 1)
        if not item.hasChildren():
            return False
        c = item.child(0).data()
        if isinstance(c, Constraint) and c.func and c.active:
            return True
        return False

    def selectParameters(self):
        """
        Selected parameter is chosen for fitting
        """
        status = QtCore.Qt.Checked
        self.setParameterSelection(status)

    def deselectParameters(self):
        """
        Selected parameters are removed for fitting
        """
        status = QtCore.Qt.Unchecked
        self.setParameterSelection(status)

    def selectedParameters(self):
        """ Returns list of selected (highlighted) parameters """
        return [s.row() for s in self.lstParams.selectionModel().selectedRows()
                if self.isCheckable(s.row())]

    def setParameterSelection(self, status=QtCore.Qt.Unchecked):
        """
        Selected parameters are chosen for fitting
        """
        # Convert to proper indices and set requested enablement
        for row in self.selectedParameters():
            self._model_model.item(row, 0).setCheckState(status)

    def getConstraintsForModel(self):
        """
        Return a list of tuples. Each tuple contains constraints mapped as
        ('constrained parameter', 'function to constrain')
        e.g. [('sld','5*sld_solvent')]
        """
        param_number = self._model_model.rowCount()
        params = [(self._model_model.item(s, 0).text(),
                    self._model_model.item(s, 1).child(0).data().func)
                    for s in range(param_number) if self.rowHasActiveConstraint(s)]
        return params

    def getComplexConstraintsForModel(self):
        """
        Return a list of tuples. Each tuple contains constraints mapped as
        ('constrained parameter', 'function to constrain')
        e.g. [('sld','5*M2.sld_solvent')].
        Only for constraints with defined VALUE
        """
        param_number = self._model_model.rowCount()
        params = [(self._model_model.item(s, 0).text(),
                    self._model_model.item(s, 1).child(0).data().func)
                    for s in range(param_number) if self.rowHasActiveComplexConstraint(s)]
        return params

    def getConstraintObjectsForModel(self):
        """
        Returns Constraint objects present on the whole model
        """
        param_number = self._model_model.rowCount()
        constraints = [self._model_model.item(s, 1).child(0).data()
                       for s in range(param_number) if self.rowHasConstraint(s)]

        return constraints

    def getConstraintsForFitting(self):
        """
        Return a list of constraints in format ready for use in fiting
        """
        # Get constraints
        constraints = self.getComplexConstraintsForModel()
        # See if there are any constraints across models
        multi_constraints = [cons for cons in constraints if self.isConstraintMultimodel(cons[1])]

        if multi_constraints:
            # Let users choose what to do
            msg = "The current fit contains constraints relying on other fit pages.\n"
            msg += "Parameters with those constraints are:\n" +\
                '\n'.join([cons[0] for cons in multi_constraints])
            msg += "\n\nWould you like to remove these constraints or cancel fitting?"
            msgbox = QtWidgets.QMessageBox(self)
            msgbox.setIcon(QtWidgets.QMessageBox.Warning)
            msgbox.setText(msg)
            msgbox.setWindowTitle("Existing Constraints")
            # custom buttons
            button_remove = QtWidgets.QPushButton("Remove")
            msgbox.addButton(button_remove, QtWidgets.QMessageBox.YesRole)
            button_cancel = QtWidgets.QPushButton("Cancel")
            msgbox.addButton(button_cancel, QtWidgets.QMessageBox.RejectRole)
            retval = msgbox.exec_()
            if retval == QtWidgets.QMessageBox.RejectRole:
                # cancel fit
                raise ValueError("Fitting cancelled")
            else:
                # remove constraint
                for cons in multi_constraints:
                    self.deleteConstraintOnParameter(param=cons[0])
                # re-read the constraints
                constraints = self.getComplexConstraintsForModel()

        return constraints

    def showModelDescription(self):
        """
        Creates a window with model description, when right clicked in the treeview
        """
        msg = 'Model description:\n'
        if self.kernel_module is not None:
            if str(self.kernel_module.description).rstrip().lstrip() == '':
                msg += "Sorry, no information is available for this model."
            else:
                msg += self.kernel_module.description + '\n'
        else:
            msg += "You must select a model to get information on this"

        menu = QtWidgets.QMenu()
        label = QtWidgets.QLabel(msg)
        action = QtWidgets.QWidgetAction(self)
        action.setDefaultWidget(label)
        menu.addAction(action)
        return menu

    def canHaveMagnetism(self):
        """
        Checks if the current model has magnetic scattering implemented
        """
        has_mag_params = False
        if self.kernel_module:
            has_mag_params = len(self.kernel_module.magnetic_params) > 0
        return self.is2D and has_mag_params

    def onSelectModel(self):
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

        # Assure the control is active
        if not self.cbModel.isEnabled():
            return
        # Empty combobox forced to be read
        if not model:
            return

        self.chkMagnetism.setEnabled(self.canHaveMagnetism())
        self.chkMagnetism.setEnabled(self.canHaveMagnetism())
        self.tabFitting.setTabEnabled(TAB_MAGNETISM, self.chkMagnetism.isChecked() and self.canHaveMagnetism())
        self._previous_model_index = self.cbModel.currentIndex()

        # Reset parameters to fit
        self.resetParametersToFit()
        self.has_error_column = False
        self.has_poly_error_column = False

        structure = None
        if self.cbStructureFactor.isEnabled():
            structure = str(self.cbStructureFactor.currentText())
        self.respondToModelStructure(model=model, structure_factor=structure)

    def onSelectBatchFilename(self, data_index):
        """
        Update the logic based on the selected file in batch fitting
        """
        self.data_index = data_index
        self.updateQRange()

    def onSelectStructureFactor(self):
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
        self.onCopyToClipboard("")

        # Reset parameters to fit
        self.resetParametersToFit()
        self.has_error_column = False
        self.has_poly_error_column = False

        self.respondToModelStructure(model=model, structure_factor=structure)
        # recast the original parameters into the model
        self.onParameterPaste()
        # revert to the original clipboard
        cb.setText(cb_text)

    def resetParametersToFit(self):
        """
        Clears the list of parameters to be fitted
        """
        self.main_params_to_fit = []
        self.poly_params_to_fit = []
        self.magnet_params_to_fit = []

    def onCustomModelChange(self):
        """
        Reload the custom model combobox
        """
        self.custom_models = self.customModels()
        self.readCustomCategoryInfo()
        self.onCategoriesChanged()

        # See if we need to update the combo in-place
        if self.cbCategory.currentText() != CATEGORY_CUSTOM: return

        current_text = self.cbModel.currentText()
        self.cbModel.blockSignals(True)
        self.cbModel.clear()
        self.cbModel.blockSignals(False)
        self.enableModelCombo()
        self.disableStructureCombo()
        # Retrieve the list of models
        model_list = self.master_category_dict[CATEGORY_CUSTOM]
        # Populate the models combobox
        self.cbModel.addItems(sorted([model for (model, _) in model_list]))
        new_index = self.cbModel.findText(current_text)
        if new_index != -1:
            self.cbModel.setCurrentIndex(self.cbModel.findText(current_text))

    def onSelectionChanged(self):
        """
        React to parameter selection
        """
        rows = self.lstParams.selectionModel().selectedRows()
        # Clean previous messages
        self.communicate.statusBarUpdateSignal.emit("")
        if len(rows) == 1:
            # Show constraint, if present
            row = rows[0].row()
            if not self.rowHasConstraint(row):
                return
            constr = self.getConstraintForRow(row)
            func = self.getConstraintForRow(row).func
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

    def replaceConstraintName(self, old_name, new_name=""):
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

    def isConstraintMultimodel(self, constraint):
        """
        Check if the constraint function text contains current model name
        """
        current_model_name = self.kernel_module.name
        if current_model_name in constraint:
            return False
        else:
            return True

    def updateData(self):
        """
        Helper function for recalculation of data used in plotting
        """
        # Update the chart
        if self.data_is_loaded:
            self.cmdPlot.setText("Show Plot")
            self.calculateQGridForModel()
        else:
            self.cmdPlot.setText("Calculate")
            # Create default datasets if no data passed
            self.createDefaultDataset()
            self.theory_item = None # ensure theory is recalc. before plot, see showTheoryPlot()

    def respondToModelStructure(self, model=None, structure_factor=None):
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

        # Update plot
        self.updateData()

        # Update state stack
        self.updateUndo()

        # Let others know
        self.newModelSignal.emit()

    def onSelectCategory(self):
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
            self.model_parameters = None
            self._model_model.clear()
            return
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
        self.cbModel.addItems(sorted([model for (model, _) in model_list]))
        self.cbModel.blockSignals(False)

    def onPolyModelChange(self, top, bottom):
        """
        Callback method for updating the main model and sasmodel
        parameters with the GUI values in the polydispersity view
        """
        item = self._poly_model.itemFromIndex(top)
        model_column = item.column()
        model_row = item.row()
        name_index = self._poly_model.index(model_row, 0)
        parameter_name = str(name_index.data()) # "distribution of sld" etc.
        if "istribution of" in parameter_name:
            # just the last word
            parameter_name = parameter_name.rsplit()[-1]

        delegate = self.lstPoly.itemDelegate()

        # Extract changed value.
        if model_column == delegate.poly_parameter:
            # Is the parameter checked for fitting?
            value = item.checkState()
            parameter_name_w = parameter_name + '.width'
            if value == QtCore.Qt.Checked:
                self.poly_params_to_fit.append(parameter_name_w)
            else:
                if parameter_name_w in self.poly_params_to_fit:
                    self.poly_params_to_fit.remove(parameter_name_w)
            self.cmdFit.setEnabled(self.haveParamsToFit())
            # force data update
            key = parameter_name + '.' + delegate.columnDict()[delegate.poly_pd]
            self.poly_params[key] = value
            self.updateData()

        elif model_column in [delegate.poly_min, delegate.poly_max]:
            try:
                value = GuiUtils.toDouble(item.text())
            except TypeError:
                # Can't be converted properly, bring back the old value and exit
                return

            current_details = self.kernel_module.details[parameter_name]
            if self.has_poly_error_column:
                # err column changes the indexing
                current_details[model_column-2] = value
            else:
                current_details[model_column-1] = value

        elif model_column == delegate.poly_function:
            # name of the function - just pass
            pass

        else:
            try:
                value = GuiUtils.toDouble(item.text())
            except TypeError:
                # Can't be converted properly, bring back the old value and exit
                return

            # Update the sasmodel
            # PD[ratio] -> width, npts -> npts, nsigs -> nsigmas
            if model_column not in delegate.columnDict():
                return
            key = parameter_name + '.' + delegate.columnDict()[model_column]
            self.poly_params[key] = value

            # Update plot
            self.updateData()

        # update in param model
        if model_column in [delegate.poly_pd, delegate.poly_error, delegate.poly_min, delegate.poly_max]:
            row = self.getRowFromName(parameter_name)
            param_item = self._model_model.item(row).child(0).child(0, model_column)
            if param_item is None:
                return
            self._model_model.blockSignals(True)
            param_item.setText(item.text())
            self._model_model.blockSignals(False)

    def onMagnetModelChange(self, top, bottom):
        """
        Callback method for updating the sasmodel magnetic parameters with the GUI values
        """
        item = self._magnet_model.itemFromIndex(top)
        model_column = item.column()
        model_row = item.row()
        name_index = self._magnet_model.index(model_row, 0)
        parameter_name = str(self._magnet_model.data(name_index))

        if model_column == 0:
            value = item.checkState()
            if value == QtCore.Qt.Checked:
                self.magnet_params_to_fit.append(parameter_name)
            else:
                if parameter_name in self.magnet_params_to_fit:
                    self.magnet_params_to_fit.remove(parameter_name)
            self.cmdFit.setEnabled(self.haveParamsToFit())
            # Update state stack
            self.updateUndo()
            return

        # Extract changed value.
        try:
            value = GuiUtils.toDouble(item.text())
        except TypeError:
            # Unparsable field
            return
        delegate = self.lstMagnetic.itemDelegate()

        if model_column > 1:
            if model_column == delegate.mag_min:
                pos = 1
            elif model_column == delegate.mag_max:
                pos = 2
            elif model_column == delegate.mag_unit:
                pos = 0
            else:
                raise AttributeError("Wrong column in magnetism table.")
            # min/max to be changed in self.kernel_module.details[parameter_name] = ['Ang', 0.0, inf]
            self.kernel_module.details[parameter_name][pos] = value
        else:
            self.magnet_params[parameter_name] = value
            #self.kernel_module.setParam(parameter_name) = value
            # Force the chart update when actual parameters changed
            self.recalculatePlotData()

        # Update state stack
        self.updateUndo()

    def onHelp(self):
        """
        Show the "Fitting" section of help
        """
        tree_location = "/user/qtgui/Perspectives/Fitting/"

        # Actual file will depend on the current tab
        tab_id = self.tabFitting.currentIndex()
        helpfile = "fitting.html"
        if tab_id == 0:
            # Look at the model and if set, pull out its help page
            if self.kernel_module is not None and hasattr(self.kernel_module, 'name'):
                # See if the help file is there
                # This breaks encapsulation a bit, though.
                full_path = GuiUtils.HELP_DIRECTORY_LOCATION
                sas_path = os.path.abspath(os.path.dirname(sys.argv[0]))
                location = sas_path + "/" + full_path
                location += "/user/models/" + self.kernel_module.id + ".html"
                if os.path.isfile(location):
                    # We have HTML for this model - show it
                    tree_location = "/user/models/"
                    helpfile = self.kernel_module.id + ".html"
            else:
                helpfile = "fitting_help.html"
        elif tab_id == 1:
            helpfile = "residuals_help.html"
        elif tab_id == 2:
            helpfile = "resolution.html"
        elif tab_id == 3:
            helpfile = "pd/polydispersity.html"
        elif tab_id == 4:
            helpfile = "magnetism/magnetism.html"
        help_location = tree_location + helpfile

        self.showHelp(help_location)

    def showHelp(self, url):
        """
        Calls parent's method for opening an HTML page
        """
        self.parent.showHelp(url)

    def onDisplayMagneticAngles(self):
        """
        Display a simple image showing direction of magnetic angles
        """
        self.magneticAnglesWidget.show()

    def onFit(self):
        """
        Perform fitting on the current data
        """
        if self.fit_started:
            self.stopFit()
            return

        # initialize fitter constants
        fit_id = 0
        handler = None
        batch_inputs = {}
        batch_outputs = {}
        #---------------------------------
        if LocalConfig.USING_TWISTED:
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
        self.kernel_module_copy = copy.deepcopy(self.kernel_module)

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

        if LocalConfig.USING_TWISTED:
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

    def stopFit(self):
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

    def updateFit(self):
        """
        """
        print("UPDATE FIT")
        pass

    def fitFailed(self, reason):
        """
        """
        self.enableInteractiveElements()
        msg = "Fitting failed with: "+ str(reason)
        self.communicate.statusBarUpdateSignal.emit(msg)

    def batchFittingCompleted(self, result):
        """
        Send the finish message from calculate threads to main thread
        """
        if result is None:
            result = tuple()
        self.batchFittingFinishedSignal.emit(result)

    def batchFitComplete(self, result):
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
            kernel_module = FittingUtilities.updateKernelWithResults(self.kernel_module, param_dict)
            # pull out current data
            data = self._logic[res_index].data

            # Switch indexes
            self.data_index = res_index
            # Recompute Q ranges
            if self.data_is_loaded:
                self.q_range_min, self.q_range_max, self.npts = self.logic.computeDataRange()

            # Recalculate theories
            method = self.complete1D if isinstance(self.data, Data1D) else self.complete2D
            self.calculateQGridForModelExt(data=data, model=kernel_module, completefn=method, use_threads=False)

        # Restore original kernel_module, so subsequent fits on the same model don't pick up the new params
        if self.kernel_module is not None:
            self.kernel_module = copy.deepcopy(self.kernel_module_copy)

    def paramDictFromResults(self, results):
        """
        Given the fit results structure, pull out optimized parameters and return them as nicely
        formatted dict
        """
        if results.fitness is None or \
            not np.isfinite(results.fitness) or \
            np.any(results.pvec is None) or \
            not np.all(np.isfinite(results.pvec)):
            msg = "Fitting did not converge!"
            self.communicate.statusBarUpdateSignal.emit(msg)
            msg += results.mesg
            logger.error(msg)
            return

        param_list = results.param_list # ['radius', 'radius.width']
        param_values = results.pvec     # array([ 0.36221662,  0.0146783 ])
        param_stderr = results.stderr   # array([ 1.71293015,  1.71294233])
        params_and_errors = list(zip(param_values, param_stderr))
        param_dict = dict(zip(param_list, params_and_errors))

        return param_dict

    def fittingCompleted(self, result):
        """
        Send the finish message from calculate threads to main thread
        """
        if result is None:
            result = tuple()
        self.fittingFinishedSignal.emit(result)

    def fitComplete(self, result):
        """
        Receive and display fitting results
        "result" is a tuple of actual result list and the fit time in seconds
        """
        #re-enable the Fit button
        self.enableInteractiveElements()

        if len(result) == 0:
            msg = "Fitting failed."
            self.communicate.statusBarUpdateSignal.emit(msg)
            return

        # Don't recalculate chi2 - it's in res.fitness already
        self.fitResults = True
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

        self.updatePolyModelFromList(param_dict)

        self.updateMagnetModelFromList(param_dict)

        # update charts
        self.onPlot()

        # Read only value - we can get away by just printing it here
        chi2_repr = GuiUtils.formatNumber(self.chi2, high=True)
        self.lblChi2Value.setText(chi2_repr)

    def prepareFitters(self, fitter=None, fit_id=0):
        """
        Prepare the Fitter object for use in fitting
        """
        # fitter = None -> single/batch fitting
        # fitter = Fit() -> simultaneous fitting

        # Data going in
        data = self.logic.data
        model = copy.deepcopy(self.kernel_module)
        qmin = self.q_range_min
        qmax = self.q_range_max

        params_to_fit = copy.deepcopy(self.main_params_to_fit)
        if self.chkPolydispersity.isChecked():
            params_to_fit += self.poly_params_to_fit
        if self.chkMagnetism.isChecked() and self.canHaveMagnetism():
            params_to_fit += self.magnet_params_to_fit
        if not params_to_fit:
            raise ValueError('Fitting requires at least one parameter to optimize.')

        # Get the constraints.
        constraints = self.getComplexConstraintsForModel()
        if fitter is None:
            # For single fits - check for inter-model constraints
            constraints = self.getConstraintsForFitting()

        smearer = self.smearing_widget.smearer()
        handler = None
        batch_inputs = {}
        batch_outputs = {}

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
            if fitter is None:
                # Assign id to the new fitter only
                fitter_single.fitter_id = [self.page_id]
            fit_id += 1
            fitters.append(fitter_single)

        return fitters, fit_id

    def iterateOverModel(self, func):
        """
        Take func and throw it inside the model row loop
        """
        for row_i in range(self._model_model.rowCount()):
            func(row_i)

    def updateModelFromList(self, param_dict):
        """
        Update the model with new parameters, create the errors column
        """
        assert isinstance(param_dict, dict)
        if not dict:
            return

        def updateFittedValues(row):
            # Utility function for main model update
            # internal so can use closure for param_dict
            param_name = str(self._model_model.item(row, 0).text())
            if not self.isCheckable(row) or param_name not in list(param_dict.keys()):
                return
            # modify the param value
            param_repr = GuiUtils.formatNumber(param_dict[param_name][0], high=True)
            self._model_model.item(row, 1).setText(param_repr)
            self.kernel_module.setParam(param_name, param_dict[param_name][0])
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

    def iterateOverPolyModel(self, func):
        """
        Take func and throw it inside the poly model row loop
        """
        for row_i in range(self._poly_model.rowCount()):
            func(row_i)

    def updatePolyModelFromList(self, param_dict):
        """
        Update the polydispersity model with new parameters, create the errors column
        """
        assert isinstance(param_dict, dict)
        if not dict:
            return

        def updateFittedValues(row_i):
            # Utility function for main model update
            # internal so can use closure for param_dict
            if row_i >= self._poly_model.rowCount():
                return
            param_name = str(self._poly_model.item(row_i, 0).text()).rsplit()[-1] + '.width'
            if param_name not in list(param_dict.keys()):
                return
            # modify the param value
            param_repr = GuiUtils.formatNumber(param_dict[param_name][0], high=True)
            self._poly_model.item(row_i, 1).setText(param_repr)
            self.kernel_module.setParam(param_name, param_dict[param_name][0])
            if self.has_poly_error_column:
                error_repr = GuiUtils.formatNumber(param_dict[param_name][1], high=True)
                self._poly_model.item(row_i, 2).setText(error_repr)

        def createErrorColumn(row_i):
            # Utility function for error column update
            if row_i >= self._poly_model.rowCount():
                return
            item = QtGui.QStandardItem()

            def createItem(param_name):
                if param_name in self.poly_params_to_fit:
                    error_repr = GuiUtils.formatNumber(param_dict[param_name][1], high=True)
                else:
                    error_repr = ""
                item.setText(error_repr)

            def poly_param():
                return str(self._poly_model.item(row_i, 0).text()).rsplit()[-1] + '.width'

            [createItem(param_name) for param_name in list(param_dict.keys()) if poly_param() == param_name]

            error_column.append(item)

        self.iterateOverPolyModel(updateFittedValues)

        if self.has_poly_error_column:
            self._poly_model.removeColumn(2)

        self.lstPoly.itemDelegate().addErrorColumn()
        error_column = []
        self.iterateOverPolyModel(createErrorColumn)

        # switch off reponse to model change
        self._poly_model.insertColumn(2, error_column)
        FittingUtilities.addErrorPolyHeadersToModel(self._poly_model)

        self.has_poly_error_column = True

    def iterateOverMagnetModel(self, func):
        """
        Take func and throw it inside the magnet model row loop
        """
        for row_i in range(self._magnet_model.rowCount()):
            func(row_i)

    def updateMagnetModelFromList(self, param_dict):
        """
        Update the magnetic model with new parameters, create the errors column
        """
        assert isinstance(param_dict, dict)
        if not dict:
            return
        if self._magnet_model.rowCount() == 0:
            return

        def updateFittedValues(row):
            # Utility function for main model update
            # internal so can use closure for param_dict
            if self._magnet_model.item(row, 0) is None:
                return
            param_name = str(self._magnet_model.item(row, 0).text())
            if param_name not in list(param_dict.keys()):
                return
            # modify the param value
            param_repr = GuiUtils.formatNumber(param_dict[param_name][0], high=True)
            self._magnet_model.item(row, 1).setText(param_repr)
            self.kernel_module.setParam(param_name, param_dict[param_name][0])
            if self.has_magnet_error_column:
                error_repr = GuiUtils.formatNumber(param_dict[param_name][1], high=True)
                self._magnet_model.item(row, 2).setText(error_repr)

        def createErrorColumn(row):
            # Utility function for error column update
            item = QtGui.QStandardItem()
            def createItem(param_name):
                if param_name in self.magnet_params_to_fit:
                    error_repr = GuiUtils.formatNumber(param_dict[param_name][1], high=True)
                else:
                    error_repr = ""
                item.setText(error_repr)
            def curr_param():
                return str(self._magnet_model.item(row, 0).text())

            [createItem(param_name) for param_name in list(param_dict.keys()) if curr_param() == param_name]

            error_column.append(item)

        self.iterateOverMagnetModel(updateFittedValues)

        if self.has_magnet_error_column:
            self._magnet_model.removeColumn(2)

        self.lstMagnetic.itemDelegate().addErrorColumn()
        error_column = []
        self.iterateOverMagnetModel(createErrorColumn)

        # switch off reponse to model change
        self._magnet_model.insertColumn(2, error_column)
        FittingUtilities.addErrorHeadersToModel(self._magnet_model)

        self.has_magnet_error_column = True

    def onPlot(self):
        """
        Plot the current set of data
        """
        # Regardless of previous state, this should now be `plot show` functionality only
        self.cmdPlot.setText("Show Plot")
        # Force data recalculation so existing charts are updated
        if not self.data_is_loaded:
            self.showTheoryPlot()
        else:
            self.showPlot()
        # This is an important processEvent.
        # This allows charts to be properly updated in order
        # of plots being applied.
        QtWidgets.QApplication.processEvents()
        self.recalculatePlotData() # recalc+plot theory again (2nd)

    def onSmearingOptionsUpdate(self):
        """
        React to changes in the smearing widget
        """
        # update display
        smearing, accuracy, smearing_min, smearing_max = self.smearing_widget.state()
        self.lblCurrentSmearing.setText(smearing)
        self.calculateQGridForModel()

    def recalculatePlotData(self):
        """
        Generate a new dataset for model
        """
        if not self.data_is_loaded:
            self.createDefaultDataset()
            self.smearing_widget.updateData(self.data)
        self.calculateQGridForModel()

    def showTheoryPlot(self):
        """
        Show the current theory plot in MPL
        """
        # Show the chart if ready
        if self.theory_item is None:
            self.recalculatePlotData()
        elif self.model_data:
            self._requestPlots(self.model_data.filename, self.theory_item.model())

    def showPlot(self):
        """
        Show the current plot in MPL
        """
        # Show the chart if ready
        data_to_show = self.data
        # Any models for this page
        current_index = self.all_data[self.data_index]
        item = self._requestPlots(self.data.filename, current_index.model())
        if item:
            # fit+data has not been shown - show just data
            self.communicate.plotRequestedSignal.emit([item, data_to_show], self.tab_id)

    def _requestPlots(self, item_name, item_model):
        """
        Emits plotRequestedSignal for all plots found in the given model under the provided item name.
        """
        fitpage_name = self.kernel_module.name
        plots = GuiUtils.plotsFromFilename(item_name, item_model)
        # Has the fitted data been shown?
        data_shown = False
        item = None
        for item, plot in plots.items():
            if fitpage_name in plot.name:
                data_shown = True
                self.communicate.plotRequestedSignal.emit([item, plot], self.tab_id)
        # return the last data item seen, if nothing was plotted; supposed to be just data)
        return None if data_shown else item

    def onOptionsUpdate(self):
        """
        Update local option values and replot
        """
        self.q_range_min, self.q_range_max, self.npts, self.log_points, self.weighting = \
            self.options_widget.state()
        # set Q range labels on the main tab
        self.lblMinRangeDef.setText(GuiUtils.formatNumber(self.q_range_min, high=True))
        self.lblMaxRangeDef.setText(GuiUtils.formatNumber(self.q_range_max, high=True))
        self.recalculatePlotData()

    def setDefaultStructureCombo(self):
        """
        Fill in the structure factors combo box with defaults
        """
        structure_factor_list = self.master_category_dict.pop(CATEGORY_STRUCTURE)
        factors = [factor[0] for factor in structure_factor_list]
        factors.insert(0, STRUCTURE_DEFAULT)
        self.cbStructureFactor.clear()
        self.cbStructureFactor.addItems(sorted(factors))

    def createDefaultDataset(self):
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
                                   num=self.npts, endpoint=True)
        self.logic.createDefault1dData(interval, self.tab_id)

    def readCategoryInfo(self):
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

    def readCustomCategoryInfo(self):
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

    def regenerateModelDict(self):
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

    def addBackgroundToModel(self, model):
        """
        Adds background parameter with default values to the model
        """
        assert isinstance(model, QtGui.QStandardItemModel)
        checked_list = ['background', '0.001', '-inf', 'inf', '1/cm']
        FittingUtilities.addCheckedListToModel(model, checked_list)
        last_row = model.rowCount()-1
        model.item(last_row, 0).setEditable(False)
        model.item(last_row, 4).setEditable(False)

    def addScaleToModel(self, model):
        """
        Adds scale parameter with default values to the model
        """
        assert isinstance(model, QtGui.QStandardItemModel)
        checked_list = ['scale', '1.0', '0.0', 'inf', '']
        FittingUtilities.addCheckedListToModel(model, checked_list)
        last_row = model.rowCount()-1
        model.item(last_row, 0).setEditable(False)
        model.item(last_row, 4).setEditable(False)

    def addWeightingToData(self, data):
        """
        Adds weighting contribution to fitting data
        """
        new_data = copy.deepcopy(data)
        # Send original data for weighting
        weight = FittingUtilities.getWeight(data=data, is2d=self.is2D, flag=self.weighting)
        if self.is2D:
            new_data.err_data = weight
        else:
            new_data.dy = weight

        return new_data

    def updateQRange(self):
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

    def SASModelToQModel(self, model_name, structure_factor=None):
        """
        Setting model parameters into table based on selected category
        """
        # Crete/overwrite model items
        self._model_model.clear()
        self._poly_model.clear()
        self._magnet_model.clear()

        if model_name is None:
            if structure_factor not in (None, "None"):
                # S(Q) on its own, treat the same as a form factor
                self.kernel_module = None
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
            self.poly_params = {}
            self.setPolyModel()
            # Add magnetic parameters to the model
            self.magnet_params = {}
            self.setMagneticModel()

        # Now we claim the model has been loaded
        self.model_is_loaded = True
        # Change the model name to a monicker
        self.kernel_module.name = self.modelName()
        # Update the smearing tab
        self.smearing_widget.updateKernelModel(kernel_model=self.kernel_module)

        # (Re)-create headers
        FittingUtilities.addHeadersToModel(self._model_model)
        self.lstParams.header().setFont(self.boldFont)

    def fromModelToQModel(self, model_name):
        """
        Setting model parameters into QStandardItemModel based on selected _model_
        """
        name = model_name
        kernel_module = None
        if self.cbCategory.currentText() == CATEGORY_CUSTOM:
            # custom kernel load requires full path
            name = os.path.join(ModelUtilities.find_plugins_dir(), model_name+".py")
        try:
            kernel_module = generate.load_kernel_module(name)
        except ModuleNotFoundError as ex:
            pass
        except FileNotFoundError as ex:
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

        if hasattr(kernel_module, 'parameters'):
            # built-in and custom models
            self.model_parameters = modelinfo.make_parameter_table(getattr(kernel_module, 'parameters', []))

        elif hasattr(kernel_module, 'model_info'):
            # for sum/multiply models
            self.model_parameters = kernel_module.model_info.parameters

        elif hasattr(kernel_module, 'Model') and hasattr(kernel_module.Model, "_model_info"):
            # this probably won't work if there's no model_info, but just in case
            self.model_parameters = kernel_module.Model._model_info.parameters
        else:
            # no parameters - default to blank table
            msg = "No parameters found in model '{}'.".format(model_name)
            logger.warning(msg)
            self.model_parameters = modelinfo.ParameterTable([])

        # Instantiate the current sasmodel
        self.kernel_module = self.models[model_name]()

        # Change the model name to a monicker
        self.kernel_module.name = self.modelName()

        # Explicitly add scale and background with default values
        temp_undo_state = self.undo_supported
        self.undo_supported = False
        self.addScaleToModel(self._model_model)
        self.addBackgroundToModel(self._model_model)
        self.undo_supported = temp_undo_state

        self.shell_names = self.shellNamesList()

        # Add heading row
        FittingUtilities.addHeadingRowToModel(self._model_model, model_name)

        # Update the QModel
        FittingUtilities.addParametersToModel(
                self.model_parameters,
                self.kernel_module,
                self.is2D,
                self._model_model,
                self.lstParams)

    def fromStructureFactorToQModel(self, structure_factor):
        """
        Setting model parameters into QStandardItemModel based on selected _structure factor_
        """
        if structure_factor is None or structure_factor=="None":
            return

        product_params = None
        kernel_module = self.models[structure_factor]()

        if self.kernel_module is None:
            self.kernel_module = kernel_module
            # Structure factor is the only selected model; build it and show all its params
            self.kernel_module.name = self.modelName()
            s_params = self.kernel_module._model_info.parameters
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

    def _volfraction_hack(self, s_kernel):
        """
        Only show volfraction once if it appears in both P and S models.
        Issues SV:1280, SV:1295, SM:219, SM:199, SM:101
        """
        from sasmodels.product import VOLFRAC_ID, RADIUS_ID, RADIUS_MODE_ID, STRUCTURE_MODE_ID

        product_params = None
        p_kernel = self.kernel_module
        # need to reset multiplicity to get the right product
        if p_kernel.is_multiplicity_model:
            p_kernel.multiplicity = p_kernel.multiplicity_info.number

        self.kernel_module = MultiplicationModel(p_kernel, s_kernel)
        # Modify the name to correspond to shown items
        self.kernel_module.name = self.modelName()

        # TODO: set model layout in sasmodels
        info = self.kernel_module._model_info
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
        if er_mode_id >= 0:
            extras.append(info.parameters.kernel_parameters[er_mode_id])

        s_params = modelinfo.ParameterTable(s_pars)
        product_params = modelinfo.ParameterTable(extras)

        return (s_params, product_params)

    def haveParamsToFit(self):
        """
        Finds out if there are any parameters ready to be fitted
        """
        if not self.logic.data_is_loaded:
            return False
        if self.main_params_to_fit:
            return True
        if self.chkPolydispersity.isChecked() and self.poly_params_to_fit:
            return True
        if self.chkMagnetism.isChecked() and self.canHaveMagnetism() and self.magnet_params_to_fit:
            return True
        return False

    def onMainParamsChange(self, top, bottom):
        """
        Callback method for updating the sasmodel parameters with the GUI values
        """
        item = self._model_model.itemFromIndex(top)

        model_column = item.column()

        if model_column == 0:
            self.checkboxSelected(item)
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
            if parameter_name != self.kernel_module.multiplicity_info.control:
                self.kernel_module.setParam(parameter_name, value)
        elif model_column == min_column:
            # min/max to be changed in self.kernel_module.details[parameter_name] = ['Ang', 0.0, inf]
            self.kernel_module.details[parameter_name][1] = value
        elif model_column == max_column:
            self.kernel_module.details[parameter_name][2] = value
        else:
            # don't update the chart
            return

        # TODO: magnetic params in self.kernel_module.details['M0:parameter_name'] = value
        # TODO: multishell params in self.kernel_module.details[??] = value

        # handle display of effective radius parameter according to radius_effective_mode; pass ER into model if
        # necessary
        self.processEffectiveRadius()

        # Force the chart update when actual parameters changed
        if model_column == 1:
            self.recalculatePlotData()

        # Update state stack
        self.updateUndo()

    def processEffectiveRadius(self):
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

    def setParamEditableByRow(self, row, editable=True):
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

    def isCheckable(self, row):
        return self._model_model.item(row, 0).isCheckable()

    def selectCheckbox(self, row):
        """
        Select the checkbox in given row.
        """
        assert 0<= row <= self._model_model.rowCount()
        index = self._model_model.index(row, 0)
        item = self._model_model.itemFromIndex(index)
        item.setCheckState(QtCore.Qt.Checked)

    def checkboxSelected(self, item):
        # Assure we're dealing with checkboxes
        if not item.isCheckable():
            return
        status = item.checkState()

        # If multiple rows selected - toggle all of them, filtering uncheckable
        # Convert to proper indices and set requested enablement
        self.setParameterSelection(status)

        # update the list of parameters to fit
        self.main_params_to_fit = self.checkedListFromModel(self._model_model)

    def checkedListFromModel(self, model):
        """
        Returns list of checked parameters for given model
        """
        def isChecked(row):
            return model.item(row, 0).checkState() == QtCore.Qt.Checked

        return [str(model.item(row_index, 0).text())
                for row_index in range(model.rowCount())
                if isChecked(row_index)]

    def createNewIndex(self, fitted_data):
        """
        Create a model or theory index with passed Data1D/Data2D
        """
        if self.data_is_loaded:
            if not fitted_data.name:
                name = self.nameForFittedData(self.data.filename)
                fitted_data.title = name
                fitted_data.name = name
                fitted_data.filename = name
                fitted_data.symbol = "Line"
            self.updateModelIndex(fitted_data)
        else:
            if not fitted_data.name:
                name = self.nameForFittedData(self.kernel_module.id)
            else:
                name = fitted_data.name
            fitted_data.title = name
            fitted_data.filename = name
            fitted_data.symbol = "Line"
            self.createTheoryIndex(fitted_data)
            # Switch to the theory tab for user's glee
            self.communicate.changeDataExplorerTabSignal.emit(1)

    def updateModelIndex(self, fitted_data):
        """
        Update a QStandardModelIndex containing model data
        """
        name = self.nameFromData(fitted_data)
        # Make this a line if no other defined
        if hasattr(fitted_data, 'symbol') and fitted_data.symbol is None:
            fitted_data.symbol = 'Line'
        # Notify the GUI manager so it can update the main model in DataExplorer
        GuiUtils.updateModelItemWithPlot(self.all_data[self.data_index], fitted_data, name)

    def createTheoryIndex(self, fitted_data):
        """
        Create a QStandardModelIndex containing model data
        """
        name = self.nameFromData(fitted_data)
        # Modify the item or add it if new
        theory_item = GuiUtils.createModelItemWithPlot(fitted_data, name=name)
        self.communicate.updateTheoryFromPerspectiveSignal.emit(theory_item)

    def setTheoryItem(self, item):
        """
        Reset the theory item based on the data explorer update
        """
        self.theory_item = item

    def nameFromData(self, fitted_data):
        """
        Return name for the dataset. Terribly impure function.
        """
        if fitted_data.name is None:
            name = self.nameForFittedData(self.logic.data.filename)
            fitted_data.title = name
            fitted_data.name = name
            fitted_data.filename = name
        else:
            name = fitted_data.name
        return name

    def methodCalculateForData(self):
        '''return the method for data calculation'''
        return Calc1D if isinstance(self.data, Data1D) else Calc2D

    def methodCompleteForData(self):
        '''return the method for result parsin on calc complete '''
        return self.completed1D if isinstance(self.data, Data1D) else self.completed2D

    def updateKernelModelWithExtraParams(self, model=None):
        """
        Updates kernel model 'model' with extra parameters from
        the polydisp and magnetism tab, if the tabs are enabled
        """
        if model is None: return
        if not hasattr(model, 'setParam'): return

        # add polydisperse parameters if asked
        if self.chkPolydispersity.isChecked() and self._poly_model.rowCount() > 0:
            for key, value in self.poly_params.items():
                model.setParam(key, value)
        # add magnetic params if asked
        if self.chkMagnetism.isChecked() and self.canHaveMagnetism() and self._magnet_model.rowCount() > 0:
            for key, value in self.magnet_params.items():
                model.setParam(key, value)

    def calculateQGridForModelExt(self, data=None, model=None, completefn=None, use_threads=True):
        """
        Wrapper for Calc1D/2D calls
        """
        if data is None:
            data = self.data
        if model is None:
            model = copy.deepcopy(self.kernel_module)
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
            if LocalConfig.USING_TWISTED:
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

    def calculateQGridForModel(self):
        """
        Prepare the fitting data object, based on current ModelModel
        """
        if self.kernel_module is None:
            return
        self.calculateQGridForModelExt()

    def calculateDataFailed(self, reason):
        """
        Thread returned error
        """
        # Bring the GUI to normal state
        self.enableInteractiveElements()
        print("Calculate Data failed with ", reason)

    def completed1D(self, return_data):
        self.Calc1DFinishedSignal.emit(return_data)

    def completed2D(self, return_data):
        self.Calc2DFinishedSignal.emit(return_data)

    def _appendPlotsPolyDisp(self, new_plots, return_data, fitted_data):
        """
        Internal helper for 1D and 2D for creating plots of the polydispersity distribution for
        parameters which have a polydispersity enabled.
        """
        for plot in FittingUtilities.plotPolydispersities(return_data.get('model', None)):
            data_id = fitted_data.id.split()
            plot.id = "{} [{}] {}".format(data_id[0], plot.name, " ".join(data_id[1:]))
            data_name = fitted_data.name.split()
            plot.name = " ".join([data_name[0], plot.name] + data_name[1:])
            self.createNewIndex(plot)
            new_plots.append(plot)

    def complete1D(self, return_data):
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
            fitted_data.xtransform="x"
            fitted_data.ytransform="y"

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

        if self.data_is_loaded:
            # delete any plots associated with the data that were not updated
            # (e.g. to remove beta(Q), S_eff(Q))
            GuiUtils.deleteRedundantPlots(self.all_data[self.data_index], new_plots)
            pass
        else:
            # delete theory items for the model, in order to get rid of any
            # redundant items, e.g. beta(Q), S_eff(Q)
            self.communicate.deleteIntermediateTheoryPlotsSignal.emit(self.kernel_module.id)

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

    def complete2D(self, return_data):
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

    def updateEffectiveRadius(self, return_data):
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
        ER_value = scalar_results.get("effective_radius") # note name of key
        if ER_value is None:
            return
        # ensure the model does not recompute when updating the value
        self._model_model.blockSignals(True)
        self._model_model.item(ER_row, 1).setText(str(ER_value))
        self._model_model.blockSignals(False)
        # ensure the view is updated immediately
        self._model_model.layoutChanged.emit()

    def calculateResiduals(self, fitted_data):
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
        residuals_plot.plot_role = Data1D.ROLE_RESIDUAL
        self.createNewIndex(residuals_plot)
        return residuals_plot

    def onCategoriesChanged(self):
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

    def calcException(self, etype, value, tb):
        """
        Thread threw an exception.
        """
        # Bring the GUI to normal state
        self.enableInteractiveElements()
        # TODO: remimplement thread cancellation
        logger.error("".join(traceback.format_exception(etype, value, tb)))

    def setTableProperties(self, table):
        """
        Setting table properties
        """
        # Table properties
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Expanding)
        table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        table.resizeColumnsToContents()

        # Header
        header = table.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        header.ResizeMode(QtWidgets.QHeaderView.Interactive)

        # Qt5: the following 2 lines crash - figure out why!
        # Resize column 0 and 7 to content
        #header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        #header.setSectionResizeMode(7, QtWidgets.QHeaderView.ResizeToContents)

    def setPolyModel(self):
        """
        Set polydispersity values
        """
        if not self.model_parameters:
            return
        self._poly_model.clear()

        parameters = self.model_parameters.form_volume_parameters
        if self.is2D:
            parameters += self.model_parameters.orientation_parameters

        [self.setPolyModelParameters(i, param) for i, param in \
            enumerate(parameters) if param.polydisperse]

        FittingUtilities.addPolyHeadersToModel(self._poly_model)

    def setPolyModelParameters(self, i, param):
        """
        Standard of multishell poly parameter driver
        """
        param_name = param.name
        # see it the parameter is multishell
        if '[' in param.name:
            # Skip empty shells
            if self.current_shell_displayed == 0:
                return
            else:
                # Create as many entries as current shells
                for ishell in range(1, self.current_shell_displayed+1):
                    # Remove [n] and add the shell numeral
                    name = param_name[0:param_name.index('[')] + str(ishell)
                    self.addNameToPolyModel(i, name)
        else:
            # Just create a simple param entry
            self.addNameToPolyModel(i, param_name)

    def addNameToPolyModel(self, i, param_name):
        """
        Creates a checked row in the poly model with param_name
        """
        # Polydisp. values from the sasmodel
        param_wname = param_name + '.width'
        width = self.kernel_module.getParam(param_wname)
        npts = self.kernel_module.getParam(param_name + '.npts')
        nsigs = self.kernel_module.getParam(param_name + '.nsigmas')
        _, min, max = self.kernel_module.details[param_wname]

        # Update local param dict
        self.poly_params[param_wname] = width
        self.poly_params[param_name + '.npts'] = npts
        self.poly_params[param_name + '.nsigmas'] = nsigs

        # Construct a row with polydisp. related variable.
        # This will get added to the polydisp. model
        # Note: last argument needs extra space padding for decent display of the control
        checked_list = ["Distribution of " + param_name, str(width),
                        str(min), str(max),
                        str(npts), str(nsigs), "gaussian      ",'']
        FittingUtilities.addCheckedListToModel(self._poly_model, checked_list)

        # All possible polydisp. functions as strings in combobox
        func = QtWidgets.QComboBox()
        func.addItems([str(name_disp) for name_disp in POLYDISPERSITY_MODELS.keys()])
        # Set the default index
        func.setCurrentIndex(func.findText(DEFAULT_POLYDISP_FUNCTION))
        ind = self._poly_model.index(i,self.lstPoly.itemDelegate().poly_function)
        self.lstPoly.setIndexWidget(ind, func)
        func.currentIndexChanged.connect(lambda: self.onPolyComboIndexChange(str(func.currentText()), i))

    def onPolyFilenameChange(self, row_index):
        """
        Respond to filename_updated signal from the delegate
        """
        # For the given row, invoke the "array" combo handler
        array_caption = 'array'

        # Get the combo box reference
        ind = self._poly_model.index(row_index, self.lstPoly.itemDelegate().poly_function)
        widget = self.lstPoly.indexWidget(ind)

        # Update the combo box so it displays "array"
        widget.blockSignals(True)
        widget.setCurrentIndex(self.lstPoly.itemDelegate().POLYDISPERSE_FUNCTIONS.index(array_caption))
        widget.blockSignals(False)

        # Invoke the file reader
        self.onPolyComboIndexChange(array_caption, row_index)

    def onPolyComboIndexChange(self, combo_string, row_index):
        """
        Modify polydisp. defaults on function choice
        """
        # Get npts/nsigs for current selection
        param = self.model_parameters.form_volume_parameters[row_index]
        file_index = self._poly_model.index(row_index, self.lstPoly.itemDelegate().poly_function)
        combo_box = self.lstPoly.indexWidget(file_index)
        try:
            self.disp_model = POLYDISPERSITY_MODELS[combo_string]()
        except IndexError:
            logger.error("Error in setting the dispersion model. Reverting to Gaussian.")
            self.disp_model = POLYDISPERSITY_MODELS['gaussian']()

        def updateFunctionCaption(row):
            # Utility function for update of polydispersity function name in the main model
            if not self.isCheckable(row):
                return
            param_name = self._model_model.item(row, 0).text()
            if param_name !=  param.name:
                return
            # Modify the param value
            self._model_model.blockSignals(True)
            if self.has_error_column:
                # err column changes the indexing
                self._model_model.item(row, 0).child(0).child(0,5).setText(combo_string)
            else:
                self._model_model.item(row, 0).child(0).child(0,4).setText(combo_string)
            self._model_model.blockSignals(False)

        if combo_string == 'array':
            try:
                # assure the combo is at the right index
                combo_box.blockSignals(True)
                combo_box.setCurrentIndex(combo_box.findText(combo_string))
                combo_box.blockSignals(False)
                # Load the file
                self.loadPolydispArray(row_index)
                # Update main model for display
                self.iterateOverModel(updateFunctionCaption)
                self.kernel_module.set_dispersion(param.name, self.disp_model)
                # uncheck the parameter
                self._poly_model.item(row_index, 0).setCheckState(QtCore.Qt.Unchecked)
                # disable the row
                lo = self.lstPoly.itemDelegate().poly_parameter
                hi = self.lstPoly.itemDelegate().poly_function
                self._poly_model.blockSignals(True)
                [self._poly_model.item(row_index, i).setEnabled(False) for i in range(lo, hi)]
                self._poly_model.blockSignals(False)
                return
            except IOError:
                combo_box.setCurrentIndex(self.orig_poly_index)
                # Pass for cancel/bad read
                pass
        else:
            self.kernel_module.set_dispersion(param.name, self.disp_model)

        # Enable the row in case it was disabled by Array
        self._poly_model.blockSignals(True)
        max_range = self.lstPoly.itemDelegate().poly_filename
        [self._poly_model.item(row_index, i).setEnabled(True) for i in range(7)]
        file_index = self._poly_model.index(row_index, self.lstPoly.itemDelegate().poly_filename)
        self._poly_model.setData(file_index, "")
        self._poly_model.blockSignals(False)

        npts_index = self._poly_model.index(row_index, self.lstPoly.itemDelegate().poly_npts)
        nsigs_index = self._poly_model.index(row_index, self.lstPoly.itemDelegate().poly_nsigs)

        npts = POLYDISPERSITY_MODELS[str(combo_string)].default['npts']
        nsigs = POLYDISPERSITY_MODELS[str(combo_string)].default['nsigmas']

        self._poly_model.setData(npts_index, npts)
        self._poly_model.setData(nsigs_index, nsigs)

        self.iterateOverModel(updateFunctionCaption)
        if combo_box is not None:
            self.orig_poly_index = combo_box.currentIndex()

    def loadPolydispArray(self, row_index):
        """
        Show the load file dialog and loads requested data into state
        """
        datafile = QtWidgets.QFileDialog.getOpenFileName(
            self, "Choose a weight file", "", "All files (*.*)", None,
            QtWidgets.QFileDialog.DontUseNativeDialog)[0]

        if not datafile:
            logger.info("No weight data chosen.")
            raise IOError

        values = []
        weights = []
        def appendData(data_tuple):
            """
            Fish out floats from a tuple of strings
            """
            try:
                values.append(float(data_tuple[0]))
                weights.append(float(data_tuple[1]))
            except (ValueError, IndexError):
                # just pass through if line with bad data
                return

        with open(datafile, 'r') as column_file:
            column_data = [line.rstrip().split() for line in column_file.readlines()]
            [appendData(line) for line in column_data]

        # If everything went well - update the sasmodel values
        self.disp_model.set_weights(np.array(values), np.array(weights))
        # + update the cell with filename
        fname = os.path.basename(str(datafile))
        fname_index = self._poly_model.index(row_index, self.lstPoly.itemDelegate().poly_filename)
        self._poly_model.setData(fname_index, fname)

    def onColumnWidthUpdate(self, index, old_size, new_size):
        """
        Simple state update of the current column widths in the  param list
        """
        self.lstParamHeaderSizes[index] = new_size

    def setMagneticModel(self):
        """
        Set magnetism values on model
        """
        if not self.model_parameters:
            return
        self._magnet_model.clear()
        # default initial value
        m0 = 0.5
        for param in self.model_parameters.call_parameters:
            if param.type != 'magnetic': continue
            if "M0" in param.name:
                m0 += 0.5
                value = m0
            else:
                value = param.default
            self.addCheckedMagneticListToModel(param, value)

        FittingUtilities.addHeadersToModel(self._magnet_model)

    def shellNamesList(self):
        """
        Returns list of names of all multi-shell parameters
        E.g. for sld[n], radius[n], n=1..3 it will return
        [sld1, sld2, sld3, radius1, radius2, radius3]
        """
        multi_names = [p.name[:p.name.index('[')] for p in self.model_parameters.iq_parameters if '[' in p.name]
        top_index = self.kernel_module.multiplicity_info.number
        shell_names = []
        for i in range(1, top_index+1):
            for name in multi_names:
                shell_names.append(name+str(i))
        return shell_names

    def addCheckedMagneticListToModel(self, param, value):
        """
        Wrapper for model update with a subset of magnetic parameters
        """
        try:
            basename, _ = param.name.rsplit('_', 1)
        except ValueError:
            basename = param.name
        if basename in self.shell_names:
            try:
                shell_index = int(basename[-2:])
            except ValueError:
                shell_index = int(basename[-1:])

            if shell_index > self.current_shell_displayed:
                return

        checked_list = [param.name,
                        str(value),
                        str(param.limits[0]),
                        str(param.limits[1]),
                        param.units]

        self.magnet_params[param.name] = value

        FittingUtilities.addCheckedListToModel(self._magnet_model, checked_list)

    def enableStructureFactorControl(self, structure_factor):
        """
        Add structure factors to the list of parameters
        """
        if self.kernel_module.is_form_factor or structure_factor == 'None':
            self.enableStructureCombo()
        else:
            self.disableStructureCombo()

    def addExtraShells(self):
        """
        Add a combobox for multiple shell display
        """
        param_name, param_length = FittingUtilities.getMultiplicity(self.model_parameters)

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

        # cell 4: SLD button
        item5 = QtGui.QStandardItem()
        button = QtWidgets.QPushButton()
        button.setText("Show SLD Profile")

        self._model_model.appendRow([item1, item2, item3, item4, item5])

        # Beautify the row:  span columns 2-4
        shell_row = self._model_model.rowCount()
        shell_index = self._model_model.index(shell_row-1, 1)
        button_index = self._model_model.index(shell_row-1, 4)

        self.lstParams.setIndexWidget(shell_index, func)
        self.lstParams.setIndexWidget(button_index, button)
        self._n_shells_row = shell_row - 1

        # Get the default number of shells for the model
        kernel_pars = self.kernel_module._model_info.parameters.kernel_parameters
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
        except IndexError as ex:
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

        # Respond to button press
        button.clicked.connect(self.onShowSLDProfile)

        # Available range of shells displayed in the combobox
        func.addItems([str(i) for i in range(shell_min, shell_max+1)])

        # Respond to index change
        func.currentTextChanged.connect(self.modifyShellsInList)

        # Add default number of shells to the model
        func.setCurrentText(str(default_shell_count))
        self.modifyShellsInList(str(default_shell_count))

    def modifyShellsInList(self, text):
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
        self.kernel_module.multiplicity = index
        if remove_rows > 1:
            self._model_model.removeRows(first_row, remove_rows)

        new_rows = FittingUtilities.addShellsToModel(
                self.model_parameters,
                self._model_model,
                index,
                first_row,
                self.lstParams)

        self._num_shell_params = len(new_rows)
        self.current_shell_displayed = index

        # Param values for existing shells were reset to default; force all changes into kernel module
        for row in new_rows:
            par = row[0].text()
            val = GuiUtils.toDouble(row[1].text())
            self.kernel_module.setParam(par, val)

        # Change 'n' in the parameter model; also causes recalculation
        self._model_model.item(self._n_shells_row, 1).setText(str(index))

        # Update relevant models
        self.setPolyModel()
        if self.canHaveMagnetism():
            self.setMagneticModel()

    def onShowSLDProfile(self):
        """
        Show a quick plot of SLD profile
        """
        # get profile data
        try:
            x, y = self.kernel_module.getProfile()
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
        profile_data._xaxis = "R(\AA)"
        profile_data._yaxis = "SLD(10^{-6}\AA^{-2})"

        plotter = PlotterWidget(self, quickplot=True)
        plotter.data = profile_data
        plotter.showLegend = True
        plotter.plot(hide_error=True, marker='-')

        self.plot_widget = QtWidgets.QWidget()
        self.plot_widget.setWindowTitle("Scattering Length Density Profile")
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(plotter)
        self.plot_widget.setLayout(layout)
        self.plot_widget.show()

    def setInteractiveElements(self, enabled=True):
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

    def enableInteractiveElements(self):
        """
        Set buttion caption on fitting/calculate finish
        Enable the param table(s)
        """
        # Notify the user that fitting is available
        self.cmdFit.setStyleSheet('QPushButton {color: black;}')
        self.cmdFit.setText("Fit")
        self.fit_started = False
        self.setInteractiveElements(True)

    def disableInteractiveElements(self):
        """
        Set buttion caption on fitting/calculate start
        Disable the param table(s)
        """
        # Notify the user that fitting is being run
        # Allow for stopping the job
        self.cmdFit.setStyleSheet('QPushButton {color: red;}')
        self.cmdFit.setText('Stop fit')
        self.setInteractiveElements(False)

    def disableInteractiveElementsOnCalculate(self):
        """
        Set buttion caption on fitting/calculate start
        Disable the param table(s)
        """
        # Notify the user that fitting is being run
        # Allow for stopping the job
        self.cmdFit.setStyleSheet('QPushButton {color: red;}')
        self.cmdFit.setText('Running...')
        self.setInteractiveElements(False)

    def readFitPage(self, fp):
        """
        Read in state from a fitpage object and update GUI
        """
        assert isinstance(fp, FitPage)
        # Main tab info
        self.logic.data.filename = fp.filename
        self.data_is_loaded = fp.data_is_loaded
        self.chkPolydispersity.setCheckState(fp.is_polydisperse)
        self.chkMagnetism.setCheckState(fp.is_magnetic)
        self.chk2DView.setCheckState(fp.is2D)

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
        self._poly_model = fp.poly_model
        self._magnet_model = fp.magnetism_model

        # Resolution tab
        smearing = fp.smearing_options[fp.SMEARING_OPTION]
        accuracy = fp.smearing_options[fp.SMEARING_ACCURACY]
        smearing_min = fp.smearing_options[fp.SMEARING_MIN]
        smearing_max = fp.smearing_options[fp.SMEARING_MAX]
        self.smearing_widget.setState(smearing, accuracy, smearing_min, smearing_max)

        # TODO: add polidyspersity and magnetism

    def saveToFitPage(self, fp):
        """
        Write current state to the given fitpage
        """
        assert isinstance(fp, FitPage)

        # Main tab info
        fp.filename = self.logic.data.filename
        fp.data_is_loaded = self.data_is_loaded
        fp.is_polydisperse = self.chkPolydispersity.isChecked()
        fp.is_magnetic = self.chkMagnetism.isChecked()
        fp.is2D = self.chk2DView.isChecked()
        fp.data = self.data

        # Use current models - they contain all the required parameters
        fp.model_model = self._model_model
        fp.poly_model = self._poly_model
        fp.magnetism_model = self._magnet_model

        if self.cbCategory.currentIndex() != 0:
            fp.current_category = str(self.cbCategory.currentText())
            fp.current_model = str(self.cbModel.currentText())

        if self.cbStructureFactor.isEnabled() and self.cbStructureFactor.currentIndex() != 0:
            fp.current_factor = str(self.cbStructureFactor.currentText())
        else:
            fp.current_factor = ''

        fp.chi2 = self.chi2
        fp.main_params_to_fit = self.main_params_to_fit
        fp.poly_params_to_fit = self.poly_params_to_fit
        fp.magnet_params_to_fit = self.magnet_params_to_fit
        fp.kernel_module = self.kernel_module

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

        # TODO: add polidyspersity and magnetism

    def updateUndo(self):
        """
        Create a new state page and add it to the stack
        """
        if self.undo_supported:
            self.pushFitPage(self.currentState())

    def currentState(self):
        """
        Return fit page with current state
        """
        new_page = FitPage()
        self.saveToFitPage(new_page)

        return new_page

    def pushFitPage(self, new_page):
        """
        Add a new fit page object with current state
        """
        self.page_stack.append(new_page)

    def popFitPage(self):
        """
        Remove top fit page from stack
        """
        if self.page_stack:
            self.page_stack.pop()

    def getReport(self):
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
        if self.chkPolydispersity.isChecked() and self._poly_model.rowCount() > 0:
            poly_params = FittingUtilities.getStandardParam(self._poly_model)
        if self.chkMagnetism.isChecked() and self.canHaveMagnetism() and self._magnet_model.rowCount() > 0:
            magnet_params = FittingUtilities.getStandardParam(self._magnet_model)
        report_logic = ReportPageLogic(self,
                                       kernel_module=self.kernel_module,
                                       data=self.data,
                                       index=index,
                                       params=params+poly_params+magnet_params)

        return report_logic.reportList()

    def loadPageStateCallback(self,state=None, datainfo=None, format=None):
        """
        This is a callback method called from the CANSAS reader.
        We need the instance of this reader only for writing out a file,
        so there's nothing here.
        Until Load Analysis is implemented, that is.
        """
        pass

    def loadPageState(self, pagestate=None):
        """
        Load the PageState object and update the current widget
        """
        filepath = self.loadAnalysisFile()
        if filepath is None or filepath == "":
            return

        with open(filepath, 'r') as statefile:
            #column_data = [line.rstrip().split() for line in statefile.readlines()]
            lines = statefile.readlines()

        # convert into list of lists
        pass

    def loadAnalysisFile(self):
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

    def onCopyToClipboard(self, format=None):
        """
        Copy current fitting parameters into the clipboard
        using requested formatting:
        plain, excel, latex
        """
        param_list = self.getFitParameters()
        if format=="":
            param_list = self.getFitPage()
            param_list += self.getFitModel()
            formatted_output = FittingUtilities.formatParameters(param_list)
        elif format == "Excel":
            formatted_output = FittingUtilities.formatParametersExcel(param_list[1:])
        elif format == "Latex":
            formatted_output = FittingUtilities.formatParametersLatex(param_list[1:])
        elif format == "Save":
            Text_output = FittingUtilities.formatParameters(param_list, False)
            Excel_output = FittingUtilities.formatParametersExcel(param_list[1:])
            Latex_output = FittingUtilities.formatParametersLatex(param_list[1:])
        else:
            raise AttributeError("Bad parameter output format specifier.")

        # Dump formatted_output to the clipboard


        if format == "Save":
            save_dialog = QtWidgets.QFileDialog()
            save_dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
            kwargs = {
                'parent': self,
                'caption': 'Save Project',
                'filter': 'Text (*.txt);;Excel (*.xls);;Latex (*.log)',
                'options': QtWidgets.QFileDialog.DontUseNativeDialog
            }
            file_path = save_dialog.getSaveFileName(**kwargs)
            filename = file_path[0]

            if file_path[1] == 'Text (*.txt)':
                Type_output = Text_output
                filename = '.'.join((filename, 'txt'))
            elif file_path[1] == 'Excel (*.xls)':
                Type_output = Excel_output
                filename = '.'.join((filename, 'xls'))
            elif file_path[1] == 'Latex (*.log)':
                Type_output = Latex_output
                filename = '.'.join((filename, 'log'))

            file_open = open(filename, 'w')
            with file_open:
                file_open.write(Type_output)
        else:
            cb = QtWidgets.QApplication.clipboard()
            cb.setText(formatted_output)


    def getFitModel(self):
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

    def getFitPage(self):
        """
        serializes full state of this fit page
        """
        # run a loop over all parameters and pull out
        # first - regular params
        param_list = self.getFitParameters()

        param_list.append(['is_data', str(self.data_is_loaded)])
        data_ids = []
        filenames = []
        if self.is_batch_fitting:
            for item in self.all_data:
                # need item->data->data_id
                data = GuiUtils.dataFromItem(item)
                data_ids.append(data.id)
                filenames.append(data.filename)
        else:
            if self.data_is_loaded:
                data_ids = [str(self.logic.data.id)]
                filenames = [str(self.logic.data.filename)]
        param_list.append(['tab_index', str(self.tab_id)])
        param_list.append(['is_batch_fitting', str(self.is_batch_fitting)])
        param_list.append(['data_name', filenames])
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

    def getFitParameters(self):
        """
        serializes current parameters
        """
        param_list = []
        if self.kernel_module is None:
            return param_list

        param_list.append(['model_name', str(self.cbModel.currentText())])

        def gatherParams(row):
            """
            Create list of main parameters based on _model_model
            """
            param_name = str(self._model_model.item(row, 0).text())

            # Assure this is a parameter - must contain a checkbox
            if not self._model_model.item(row, 0).isCheckable():
                # maybe it is a combobox item (multiplicity)
                try:
                    index = self._model_model.index(row, 1)
                    widget = self.lstParams.indexWidget(index)
                    if widget is None:
                        return
                    if isinstance(widget, QtWidgets.QComboBox):
                        # find the index of the combobox
                        current_index = widget.currentIndex()
                        param_list.append([param_name, 'None', str(current_index)])
                except Exception as ex:
                    pass
                return

            param_checked = str(self._model_model.item(row, 0).checkState() == QtCore.Qt.Checked)
            # Value of the parameter. In some cases this is the text of the combobox choice.
            param_value = str(self._model_model.item(row, 1).text())
            param_error = None
            param_min = None
            param_max = None
            column_offset = 0
            if self.has_error_column:
                column_offset = 1
                param_error = str(self._model_model.item(row, 1+column_offset).text())
            try:
                param_min = str(self._model_model.item(row, 2+column_offset).text())
                param_max = str(self._model_model.item(row, 3+column_offset).text())
            except:
                pass
            # Do we have any constraints on this parameter?
            constraint = self.getConstraintForRow(row)
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
            param_name = str(self._poly_model.item(row, 0).text()).split()[-1]
            param_checked = str(self._poly_model.item(row, 0).checkState() == QtCore.Qt.Checked)
            param_value = str(self._poly_model.item(row, 1).text())
            param_error = None
            column_offset = 0
            if self.has_poly_error_column:
                column_offset = 1
                param_error = str(self._poly_model.item(row, 1+column_offset).text())
            param_min   = str(self._poly_model.item(row, 2+column_offset).text())
            param_max   = str(self._poly_model.item(row, 3+column_offset).text())
            param_npts  = str(self._poly_model.item(row, 4+column_offset).text())
            param_nsigs = str(self._poly_model.item(row, 5+column_offset).text())
            param_fun   = str(self._poly_model.item(row, 6+column_offset).text()).rstrip()
            index = self._poly_model.index(row, 6+column_offset)
            widget = self.lstPoly.indexWidget(index)
            if widget is not None and isinstance(widget, QtWidgets.QComboBox):
                param_fun = widget.currentText()
            # width
            name = param_name+".width"
            param_list.append([name, param_checked, param_value, param_error,
                               param_min, param_max, param_npts, param_nsigs, param_fun])

        def gatherMagnetParams(row):
            """
            Create list of magnetic parameters based on _magnet_model
            """
            param_name = str(self._magnet_model.item(row, 0).text())
            param_checked = str(self._magnet_model.item(row, 0).checkState() == QtCore.Qt.Checked)
            param_value = str(self._magnet_model.item(row, 1).text())
            param_error = None
            column_offset = 0
            if self.has_magnet_error_column:
                column_offset = 1
                param_error = str(self._magnet_model.item(row, 1+column_offset).text())
            param_min = str(self._magnet_model.item(row, 2+column_offset).text())
            param_max = str(self._magnet_model.item(row, 3+column_offset).text())
            param_list.append([param_name, param_checked, param_value,
                               param_error, param_min, param_max])

        self.iterateOverModel(gatherParams)
        if self.chkPolydispersity.isChecked():
            self.iterateOverPolyModel(gatherPolyParams)
        if self.chkMagnetism.isChecked() and self.canHaveMagnetism():
            self.iterateOverMagnetModel(gatherMagnetParams)

        if self.kernel_module.is_multiplicity_model:
            param_list.append(['multiplicity', str(self.kernel_module.multiplicity)])

        return param_list

    def onParameterPaste(self):
        """
        Use the clipboard to update fit state
        """
        # Check if the clipboard contains right stuff
        cb = QtWidgets.QApplication.clipboard()
        cb_text = cb.text()

        lines = cb_text.split(':')
        if lines[0] != 'sasview_parameter_values':
            return False

        # put the text into dictionary
        line_dict = {}
        for line in lines[1:]:
            content = line.split(',')
            if len(content) > 1:
                line_dict[content[0]] = content[1:]

        self.updatePageWithParameters(line_dict)

    def createPageForParameters(self, line_dict):
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

    def updatePageWithParameters(self, line_dict):
        """
        Update FitPage with parameters in line_dict
        """
        if 'model_name' not in line_dict.keys():
            return
        model = line_dict['model_name'][0]
        context = {}

        if 'multiplicity' in line_dict.keys():
            multip = int(line_dict['multiplicity'][0], 0)
            # reset the model with multiplicity, so further updates are saved
            if self.kernel_module.is_multiplicity_model:
                self.kernel_module.multiplicity=multip
                self.updateMultiplicityCombo(multip)

        if 'tab_name' in line_dict.keys() and self.kernel_module is not None:
            self.kernel_module.name = line_dict['tab_name'][0]
        if 'polydisperse_params' in line_dict.keys():
            self.chkPolydispersity.setChecked(line_dict['polydisperse_params'][0]=='True')
        if 'magnetic_params' in line_dict.keys():
            self.chkMagnetism.setChecked(line_dict['magnetic_params'][0]=='True')
        if 'chainfit_params' in line_dict.keys():
            self.chkChainFit.setChecked(line_dict['chainfit_params'][0]=='True')
        if '2D_params' in line_dict.keys():
            self.chk2DView.setChecked(line_dict['2D_params'][0]=='True')

        # Create the context dictionary for parameters
        context['model_name'] = model
        for key, value in line_dict.items():
            if len(value) > 2:
                context[key] = value

        if str(self.cbModel.currentText()) != str(context['model_name']):
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

        if 'smearing' in line_dict.keys():
            try:
                index = int(line_dict['smearing'][0])
                self.smearing_widget.cbSmearing.setCurrentIndex(index)
            except ValueError:
                pass
        if 'smearing_min' in line_dict.keys():
            try:
                self.smearing_widget.dq_l = float(line_dict['smearing_min'][0])
            except ValueError:
                pass
        if 'smearing_max' in line_dict.keys():
            try:
                self.smearing_widget.dq_r = float(line_dict['smearing_max'][0])
            except ValueError:
                pass

        if 'q_range_max' in line_dict.keys():
            try:
                self.q_range_min = float(line_dict['q_range_min'][0])
                self.q_range_max = float(line_dict['q_range_max'][0])
            except ValueError:
                pass
        self.options_widget.updateQRange(self.q_range_min, self.q_range_max, self.npts)
        try:
            button_id = int(line_dict['weighting'][0])
            for button in self.options_widget.weightingGroup.buttons():
                if abs(self.options_widget.weightingGroup.id(button)) == button_id+2:
                    button.setChecked(True)
                    break
        except ValueError:
            pass

        self.updateFullModel(context)
        self.updateFullPolyModel(context)
        self.updateFullMagnetModel(context)

    def updateMultiplicityCombo(self, multip):
        """
        Find and update the multiplicity combobox
        """
        index = self._model_model.index(self._n_shells_row, 1)
        widget = self.lstParams.indexWidget(index)
        if widget is not None and isinstance(widget, QtWidgets.QComboBox):
            widget.setCurrentIndex(widget.findText(str(multip)))
        self.current_shell_displayed = multip

    def updateFullModel(self, param_dict):
        """
        Update the model with new parameters
        """
        assert isinstance(param_dict, dict)
        if not dict:
            return

        def updateFittedValues(row):
            # Utility function for main model update
            # internal so can use closure for param_dict
            param_name = str(self._model_model.item(row, 0).text())
            if param_name not in list(param_dict.keys()):
                return
            # Special case of combo box in the cell (multiplicity)
            param_line = param_dict[param_name]
            if len(param_line) == 1:
                # modify the shells value
                try:
                    combo_index = int(param_line[0])
                except ValueError:
                    # quietly pass
                    return
                index = self._model_model.index(row, 1)
                widget = self.lstParams.indexWidget(index)
                if widget is not None and isinstance(widget, QtWidgets.QComboBox):
                    #widget.setCurrentIndex(combo_index)
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
            except:
                pass

            # constraints
            cons = param_dict[param_name][4+ioffset]
            if cons is not None and len(cons)==5:
                value = cons[0]
                param = cons[1]
                value_ex = cons[2]
                validate = cons[3]
                function = cons[4]
                constraint = Constraint()
                constraint.value = value
                constraint.func = function
                constraint.param = param
                constraint.value_ex = value_ex
                constraint.validate = validate
                self.addConstraintToRow(constraint=constraint, row=row)

            self.setFocus()

        self.iterateOverModel(updateFittedValues)

    def updateFullPolyModel(self, param_dict):
        """
        Update the polydispersity model with new parameters, create the errors column
        """
        assert isinstance(param_dict, dict)
        if not dict:
            return

        def updateFittedValues(row):
            # Utility function for main model update
            # internal so can use closure for param_dict
            if row >= self._poly_model.rowCount():
                return
            param_name = str(self._poly_model.item(row, 0).text()).rsplit()[-1] + '.width'
            if param_name not in list(param_dict.keys()):
                return
            # checkbox state
            param_checked = QtCore.Qt.Checked if param_dict[param_name][0] == "True" else QtCore.Qt.Unchecked
            self._poly_model.item(row,0).setCheckState(param_checked)

            # modify the param value
            param_repr = GuiUtils.formatNumber(param_dict[param_name][1], high=True)
            self._poly_model.item(row, 1).setText(param_repr)

            # Potentially the error column
            ioffset = 0
            joffset = 0
            if len(param_dict[param_name])>7:
                ioffset = 1
            if self.has_poly_error_column:
                joffset = 1
            # min
            param_repr = GuiUtils.formatNumber(param_dict[param_name][2+ioffset], high=True)
            self._poly_model.item(row, 2+joffset).setText(param_repr)
            # max
            param_repr = GuiUtils.formatNumber(param_dict[param_name][3+ioffset], high=True)
            self._poly_model.item(row, 3+joffset).setText(param_repr)
            # Npts
            param_repr = GuiUtils.formatNumber(param_dict[param_name][4+ioffset], high=True)
            self._poly_model.item(row, 4+joffset).setText(param_repr)
            # Nsigs
            param_repr = GuiUtils.formatNumber(param_dict[param_name][5+ioffset], high=True)
            self._poly_model.item(row, 5+joffset).setText(param_repr)

            self.setFocus()

        self.iterateOverPolyModel(updateFittedValues)

    def updateFullMagnetModel(self, param_dict):
        """
        Update the magnetism model with new parameters, create the errors column
        """
        assert isinstance(param_dict, dict)
        if not dict:
            return

        def updateFittedValues(row):
            # Utility function for main model update
            # internal so can use closure for param_dict
            if row >= self._magnet_model.rowCount():
                return
            param_name = str(self._magnet_model.item(row, 0).text()).rsplit()[-1]
            if param_name not in list(param_dict.keys()):
                return
            # checkbox state
            param_checked = QtCore.Qt.Checked if param_dict[param_name][0] == "True" else QtCore.Qt.Unchecked
            self._magnet_model.item(row,0).setCheckState(param_checked)

            # modify the param value
            param_repr = GuiUtils.formatNumber(param_dict[param_name][1], high=True)
            self._magnet_model.item(row, 1).setText(param_repr)

            # Potentially the error column
            ioffset = 0
            joffset = 0
            if len(param_dict[param_name])>4:
                ioffset = 1
            if self.has_magnet_error_column:
                joffset = 1
            # min
            param_repr = GuiUtils.formatNumber(param_dict[param_name][2+ioffset], high=True)
            self._magnet_model.item(row, 2+joffset).setText(param_repr)
            # max
            param_repr = GuiUtils.formatNumber(param_dict[param_name][3+ioffset], high=True)
            self._magnet_model.item(row, 3+joffset).setText(param_repr)

        self.iterateOverMagnetModel(updateFittedValues)

    def onMaskedData(self):
        """
        A mask has been applied to current data.
        Update the Q ranges.
        """
        self.updateQRange()
        self.updateData()

    def getCurrentFitState(self, state=None):
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

        p = self.model_parameters
        # save checkbutton state and txtcrtl values
        state.parameters = FittingUtilities.getStandardParam(self._model_model)
        state.orientation_params_disp = FittingUtilities.getOrientationParam(self.kernel_module)
