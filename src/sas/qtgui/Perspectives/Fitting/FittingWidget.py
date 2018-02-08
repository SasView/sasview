import json
import os
from collections import defaultdict


import logging
import traceback
from twisted.internet import threads
import numpy as np
import webbrowser

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from sasmodels import product
from sasmodels import generate
from sasmodels import modelinfo
from sasmodels.sasview_model import load_standard_models
from sasmodels.weights import MODELS as POLYDISPERSITY_MODELS

from sas.sascalc.fit.BumpsFitting import BumpsFit as Fit

import sas.qtgui.Utilities.GuiUtils as GuiUtils
import sas.qtgui.Utilities.LocalConfig as LocalConfig
from sas.qtgui.Utilities.GridPanel import BatchOutputPanel
from sas.qtgui.Utilities.CategoryInstaller import CategoryInstaller
from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Plotting.PlotterData import Data2D

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


TAB_MAGNETISM = 4
TAB_POLY = 3
CATEGORY_DEFAULT = "Choose category..."
CATEGORY_STRUCTURE = "Structure Factor"
CATEGORY_CUSTOM = "Plugin Models"
STRUCTURE_DEFAULT = "None"

DEFAULT_POLYDISP_FUNCTION = 'gaussian'


class ToolTippedItemModel(QtGui.QStandardItemModel):
    """
    Subclass from QStandardItemModel to allow displaying tooltips in
    QTableView model.
    """
    def __init__(self, parent=None):
        QtGui.QStandardItemModel.__init__(self,parent)

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

    def __init__(self, parent=None, data=None, tab_id=1):

        super(FittingWidget, self).__init__()

        # Necessary globals
        self.parent = parent

        # Which tab is this widget displayed in?
        self.tab_id = tab_id

        # Main Data[12]D holder
        self.logic = FittingLogic()

        # Globals
        self.initializeGlobals()

        # Set up desired logging level
        logging.disable(LocalConfig.DISABLE_LOGGING)

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

        # Connect signals to controls
        self.initializeSignals()

        # Initial control state
        self.initializeControls()

        # Display HTML content
        #self.setupHelp()

        # New font to display angstrom symbol
        new_font = 'font-family: -apple-system, "Helvetica Neue", "Ubuntu";'
        self.label_17.setStyleSheet(new_font)
        self.label_19.setStyleSheet(new_font)

        self._index = None
        if data is not None:
            self.data = data

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
        # _index contains the QIndex with data
        self._index = value[0]

        # Keep reference to all datasets for batch
        self.all_data = value

        # Update logics with data items
        # Logics.data contains only a single Data1D/Data2D object
        self.logic.data = GuiUtils.dataFromItem(value[0])

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
        # Current SasModel in view
        self.kernel_module = None
        # Current SasModel view dimension
        self.is2D = False
        # Current SasModel is multishell
        self.model_has_shells = False
        # Utility variable to enable unselectable option in category combobox
        self._previous_category_index = 0
        # Utility variable for multishell display
        self._last_model_row = 0
        # Dictionary of {model name: model class} for the current category
        self.models = {}
        # Parameters to fit
        self.parameters_to_fit = None
        # Fit options
        self.q_range_min = 0.005
        self.q_range_max = 0.1
        self.npts = 25
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
        self.orig_poly_index = 3

        # Page id for fitting
        # To keep with previous SasView values, use 200 as the start offset
        self.page_id = 200 + self.tab_id

        # Data for chosen model
        self.model_data = None

        # Which shell is being currently displayed?
        self.current_shell_displayed = 0
        # List of all shell-unique parameters
        self.shell_names = []

        # Error column presence in parameter display
        self.has_error_column = False
        self.has_poly_error_column = False
        self.has_magnet_error_column = False

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
        pixmap = QtGui.QPixmap(GuiUtils.IMAGES_DIRECTORY_LOCATION + '/M_angles_pic.bmp')
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

    def initializeCategoryCombo(self):
        """
        Model category combo setup
        """
        category_list = sorted(self.master_category_dict.keys())
        self.cbCategory.addItem(CATEGORY_DEFAULT)
        self.cbCategory.addItems(category_list)
        self.cbCategory.addItem(CATEGORY_STRUCTURE)
        self.cbCategory.setCurrentIndex(0)

    def setEnablementOnDataLoad(self):
        """
        Enable/disable various UI elements based on data loaded
        """
        # Tag along functionality
        self.label.setText("Data loaded from: ")
        self.lblFilename.setText(self.logic.data.filename)
        self.updateQRange()
        # Switch off Data2D control
        self.chk2DView.setEnabled(False)
        self.chk2DView.setVisible(False)
        self.chkMagnetism.setEnabled(self.is2D)
        self.tabFitting.setTabEnabled(TAB_MAGNETISM, self.is2D)
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
        self.smearing_widget.updateSmearing(self.data)

    def acceptsData(self):
        """ Tells the caller this widget can accept new dataset """
        return not self.data_is_loaded

    def disableModelCombo(self):
        """ Disable the combobox """
        self.cbModel.setEnabled(False)
        self.lblModel.setEnabled(False)

    def enableModelCombo(self):
        """ Enable the combobox """
        self.cbModel.setEnabled(True)
        self.lblModel.setEnabled(True)

    def disableStructureCombo(self):
        """ Disable the combobox """
        self.cbStructureFactor.setEnabled(False)
        self.lblStructure.setEnabled(False)

    def enableStructureCombo(self):
        """ Enable the combobox """
        self.cbStructureFactor.setEnabled(True)
        self.lblStructure.setEnabled(True)

    def togglePoly(self, isChecked):
        """ Enable/disable the polydispersity tab """
        self.tabFitting.setTabEnabled(TAB_POLY, isChecked)

    def toggleMagnetism(self, isChecked):
        """ Enable/disable the magnetism tab """
        self.tabFitting.setTabEnabled(TAB_MAGNETISM, isChecked)

    def toggleChainFit(self, isChecked):
        """ Enable/disable chain fitting """
        self.is_chain_fitting = isChecked

    def toggle2D(self, isChecked):
        """ Enable/disable the controls dependent on 1D/2D data instance """
        self.chkMagnetism.setEnabled(isChecked)
        self.is2D = isChecked
        # Reload the current model
        if self.kernel_module:
            self.onSelectModel()

    def customModels(self):
        """ Reads in file names in the custom plugin directory """
        return ModelUtilities._find_models()

    def initializeControls(self):
        """
        Set initial control enablement
        """
        self.cbFileNames.setVisible(False)
        self.cmdFit.setEnabled(False)
        self.cmdPlot.setEnabled(False)
        self.options_widget.cmdComputePoints.setVisible(False) # probably redundant
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
        self.smearing_widget.updateSmearing(self.data)
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
        self._model_model.itemChanged.connect(self.onMainParamsChange)
        #self.constraintAddedSignal.connect(self.modifyViewOnConstraint)
        self._poly_model.itemChanged.connect(self.onPolyModelChange)
        self._magnet_model.itemChanged.connect(self.onMagnetModelChange)
        self.lstParams.selectionModel().selectionChanged.connect(self.onSelectionChanged)

        # Local signals
        self.batchFittingFinishedSignal.connect(self.batchFitComplete)
        self.fittingFinishedSignal.connect(self.fitComplete)

        # Signals from separate tabs asking for replot
        self.options_widget.plot_signal.connect(self.onOptionsUpdate)

        # Signals from other widgets
        self.communicate.customModelDirectoryChanged.connect(self.onCustomModelChange)

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
        rows = [s.row() for s in self.lstParams.selectionModel().selectedRows()]
        menu = self.showModelDescription() if not rows else self.modelContextMenu(rows)
        try:
            menu.exec_(self.lstParams.viewport().mapToGlobal(position))
        except AttributeError as ex:
            logging.error("Error generating context menu: %s" % ex)
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
        param_string = "parameter " if num_rows==1 else "parameters "
        to_string = "to its current value" if num_rows==1 else "to their current values"
        has_constraints = any([self.rowHasConstraint(i) for i in rows])

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
            #if num_rows == 1:
            #    menu.addAction(self.actionEditConstraint)
        else:
            menu.addAction(self.actionConstrain)
            if num_rows == 2:
                menu.addAction(self.actionMutualMultiConstrain)

        # Define the callbacks
        self.actionConstrain.triggered.connect(self.addSimpleConstraint)
        self.actionRemoveConstraint.triggered.connect(self.deleteConstraint)
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
        assert(len(selected_rows)==2)

        params_list = [s.data() for s in selected_rows]
        # Create and display the widget for param1 and param2
        mc_widget = MultiConstraint(self, params=params_list)
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
        # Which row is the constrained parameter in?
        row = self.getRowFromName(constraint.param)

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
        return [self._model_model.item(row).text() for row in range(self._model_model.rowCount())]

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
        assert(isinstance(constraint, Constraint))
        assert(0<=row<=self._model_model.rowCount())

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

    def deleteConstraint(self):
        """
        Delete constraints from selected parameters.
        """
        params =  [s.data() for s in self.lstParams.selectionModel().selectedRows()
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
        For the given row, return its constraint, if any
        """
        try:
            item = self._model_model.item(row, 1)
            return item.child(0).data()
        except AttributeError:
            # return none when no constraints
            return None

    def rowHasConstraint(self, row):
        """
        Finds out if row of the main model has a constraint child
        """
        item = self._model_model.item(row,1)
        if item.hasChildren():
            c = item.child(0).data()
            if isinstance(c, Constraint):
                return True
        return False

    def rowHasActiveConstraint(self, row):
        """
        Finds out if row of the main model has an active constraint child
        """
        item = self._model_model.item(row,1)
        if item.hasChildren():
            c = item.child(0).data()
            if isinstance(c, Constraint) and c.active:
                return True
        return False

    def rowHasActiveComplexConstraint(self, row):
        """
        Finds out if row of the main model has an active, nontrivial constraint child
        """
        item = self._model_model.item(row,1)
        if item.hasChildren():
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

    def onSelectModel(self):
        """
        Respond to select Model from list event
        """
        model = self.cbModel.currentText()

        # empty combobox forced to be read
        if not model:
            return
        # Reset structure factor
        self.cbStructureFactor.setCurrentIndex(0)

        # Reset parameters to fit
        self.parameters_to_fit = None
        self.has_error_column = False
        self.has_poly_error_column = False

        self.respondToModelStructure(model=model, structure_factor=None)

    def onSelectBatchFilename(self, data_index):
        """
        Update the logic based on the selected file in batch fitting
        """
        self._index = self.all_data[data_index]
        self.logic.data = GuiUtils.dataFromItem(self.all_data[data_index])
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
        self.respondToModelStructure(model=model, structure_factor=structure)

    def onCustomModelChange(self):
        """
        Reload the custom model combobox
        """
        self.custom_models = self.customModels()
        self.readCustomCategoryInfo()
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
            if self.rowHasConstraint(row):
                func = self.getConstraintForRow(row).func
                if func is not None:
                    self.communicate.statusBarUpdateSignal.emit("Active constrain: "+func)

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

    def respondToModelStructure(self, model=None, structure_factor=None):
        # Set enablement on calculate/plot
        self.cmdPlot.setEnabled(True)

        # kernel parameters -> model_model
        self.SASModelToQModel(model, structure_factor)

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
            self._model_model.clear()
            return
            
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
        self.cbModel.addItems(sorted([model for (model, _) in model_list]))

    def onPolyModelChange(self, item):
        """
        Callback method for updating the main model and sasmodel
        parameters with the GUI values in the polydispersity view
        """
        model_column = item.column()
        model_row = item.row()
        name_index = self._poly_model.index(model_row, 0)
        parameter_name = str(name_index.data()).lower() # "distribution of sld" etc.
        if "distribution of" in parameter_name:
            # just the last word
            parameter_name = parameter_name.rsplit()[-1]

        # Extract changed value.
        if model_column == self.lstPoly.itemDelegate().poly_parameter:
            # Is the parameter checked for fitting?
            value = item.checkState()
            parameter_name = parameter_name + '.width'
            if value == QtCore.Qt.Checked:
                self.parameters_to_fit.append(parameter_name)
            else:
                if parameter_name in self.parameters_to_fit:
                    self.parameters_to_fit.remove(parameter_name)
            self.cmdFit.setEnabled(self.parameters_to_fit != [] and self.logic.data_is_loaded)
            return
        elif model_column in [self.lstPoly.itemDelegate().poly_min, self.lstPoly.itemDelegate().poly_max]:
            try:
                value = GuiUtils.toDouble(item.text())
            except TypeError:
                # Can't be converted properly, bring back the old value and exit
                return

            current_details = self.kernel_module.details[parameter_name]
            current_details[model_column-1] = value
        elif model_column == self.lstPoly.itemDelegate().poly_function:
            # name of the function - just pass
            return
        else:
            try:
                value = GuiUtils.toDouble(item.text())
            except TypeError:
                # Can't be converted properly, bring back the old value and exit
                return

            # Update the sasmodel
            # PD[ratio] -> width, npts -> npts, nsigs -> nsigmas
            self.kernel_module.setParam(parameter_name + '.' + \
                                        self.lstPoly.itemDelegate().columnDict()[model_column], value)

            # Update plot
            self.updateData()

    def onMagnetModelChange(self, item):
        """
        Callback method for updating the sasmodel magnetic parameters with the GUI values
        """
        model_column = item.column()
        model_row = item.row()
        name_index = self._magnet_model.index(model_row, 0)
        parameter_name = str(self._magnet_model.data(name_index))

        if model_column == 0:
            value = item.checkState()
            if value == QtCore.Qt.Checked:
                self.parameters_to_fit.append(parameter_name)
            else:
                if parameter_name in self.parameters_to_fit:
                    self.parameters_to_fit.remove(parameter_name)
            self.cmdFit.setEnabled(self.parameters_to_fit != [] and self.logic.data_is_loaded)
            # Update state stack
            self.updateUndo()
            return

        # Extract changed value.
        try:
            value = GuiUtils.toDouble(item.text())
        except TypeError:
            # Unparsable field
            return

        property_index = self._magnet_model.headerData(1, model_column)-1 # Value, min, max, etc.

        # Update the parameter value - note: this supports +/-inf as well
        self.kernel_module.params[parameter_name] = value

        # min/max to be changed in self.kernel_module.details[parameter_name] = ['Ang', 0.0, inf]
        self.kernel_module.details[parameter_name][property_index] = value

        # Force the chart update when actual parameters changed
        if model_column == 1:
            self.recalculatePlotData()

        # Update state stack
        self.updateUndo()

    def onHelp(self):
        """
        Show the "Fitting" section of help
        """
        tree_location = "/user/sasgui/perspectives/fitting/"

        # Actual file will depend on the current tab
        tab_id = self.tabFitting.currentIndex()
        helpfile = "fitting.html"
        if tab_id == 0:
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

        # Create the fitting thread, based on the fitter
        completefn = self.batchFittingCompleted if self.is_batch_fitting else self.fittingCompleted

        calc_fit = FitThread(handler=handler,
                            fn=fitters,
                            batch_inputs=batch_inputs,
                            batch_outputs=batch_outputs,
                            page_id=[[self.page_id]],
                            updatefn=updater,
                            completefn=completefn,
                            reset_flag=self.is_chain_fitting)

        if LocalConfig.USING_TWISTED:
            # start the trhrhread with twisted
            calc_thread = threads.deferToThread(calc_fit.compute)
            calc_thread.addCallback(completefn)
            calc_thread.addErrback(self.fitFailed)
        else:
            # Use the old python threads + Queue
            calc_fit.queue()
            calc_fit.ready(2.5)

        self.communicate.statusBarUpdateSignal.emit('Fitting started...')
        # Disable some elements
        self.setFittingStarted()

    def updateFit(self):
        """
        """
        print("UPDATE FIT")
        pass

    def fitFailed(self, reason):
        """
        """
        print("FIT FAILED: ", reason)
        pass

    def batchFittingCompleted(self, result):
        """
        Send the finish message from calculate threads to main thread
        """
        self.batchFittingFinishedSignal.emit(result)

    def batchFitComplete(self, result):
        """
        Receive and display batch fitting results
        """
        #re-enable the Fit button
        self.setFittingStopped()
        # Show the grid panel
        self.grid_window = BatchOutputPanel(parent=self, output_data=result[0])
        self.grid_window.show()

    def fittingCompleted(self, result):
        """
        Send the finish message from calculate threads to main thread
        """
        self.fittingFinishedSignal.emit(result)

    def fitComplete(self, result):
        """
        Receive and display fitting results
        "result" is a tuple of actual result list and the fit time in seconds
        """
        #re-enable the Fit button
        self.setFittingStopped()

        if result is None:
            msg = "Fitting failed."
            self.communicate.statusBarUpdateSignal.emit(msg)
            return

        res_list = result[0][0]
        res = res_list[0]
        if res.fitness is None or \
            not np.isfinite(res.fitness) or \
            np.any(res.pvec is None) or \
            not np.all(np.isfinite(res.pvec)):
            msg = "Fitting did not converge!"
            self.communicate.statusBarUpdateSignal.emit(msg)
            msg += res.mesg
            logging.error(msg)
            return

        elapsed = result[1]
        msg = "Fitting completed successfully in: %s s.\n" % GuiUtils.formatNumber(elapsed)
        self.communicate.statusBarUpdateSignal.emit(msg)

        self.chi2 = res.fitness
        param_list = res.param_list # ['radius', 'radius.width']
        param_values = res.pvec     # array([ 0.36221662,  0.0146783 ])
        param_stderr = res.stderr   # array([ 1.71293015,  1.71294233])
        params_and_errors = list(zip(param_values, param_stderr))
        param_dict = dict(zip(param_list, params_and_errors))

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
        model = self.kernel_module
        qmin = self.q_range_min
        qmax = self.q_range_max
        params_to_fit = self.parameters_to_fit
        if (not params_to_fit):
            raise ValueError('Fitting requires at least one parameter to optimize.')

        # Potential weights added directly to data
        self.addWeightingToData(data)

        # Potential smearing added
        # Remember that smearing_min/max can be None ->
        # deal with it until Python gets discriminated unions
        smearing, accuracy, smearing_min, smearing_max = self.smearing_widget.state()

        constraints = self.getConstraintsForFitting()

        smearer = None
        handler = None
        batch_inputs = {}
        batch_outputs = {}

        fitters = []
        for fit_index in self.all_data:
            fitter_single = Fit() if fitter is None else fitter
            data = GuiUtils.dataFromItem(fit_index)
            try:
                fitter_single.set_model(model, fit_id, params_to_fit, data=data,
                             constraints=constraints)
            except ValueError as ex:
                raise ValueError("Setting model parameters failed with: %s" % ex)

            qmin, qmax, _ = self.logic.computeRangeFromData(data)
            fitter_single.set_data(data=data, id=fit_id, smearer=smearer, qmin=qmin,
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
            if param_name not in list(param_dict.keys()):
                return
            # modify the param value
            param_repr = GuiUtils.formatNumber(param_dict[param_name][0], high=True)
            self._model_model.item(row, 1).setText(param_repr)
            if self.has_error_column:
                error_repr = GuiUtils.formatNumber(param_dict[param_name][1], high=True)
                self._model_model.item(row, 2).setText(error_repr)

        def updatePolyValues(row):
            # Utility function for updateof polydispersity part of the main model
            param_name = str(self._model_model.item(row, 0).text())+'.width'
            if param_name not in list(param_dict.keys()):
                return
            # modify the param value
            param_repr = GuiUtils.formatNumber(param_dict[param_name][0], high=True)
            self._model_model.item(row, 0).child(0).child(0,1).setText(param_repr)

        def createErrorColumn(row):
            # Utility function for error column update
            item = QtGui.QStandardItem()
            def createItem(param_name):
                error_repr = GuiUtils.formatNumber(param_dict[param_name][1], high=True)
                item.setText(error_repr)
            def curr_param():
                return str(self._model_model.item(row, 0).text())

            [createItem(param_name) for param_name in list(param_dict.keys()) if curr_param() == param_name]

            error_column.append(item)

        # block signals temporarily, so we don't end up
        # updating charts with every single model change on the end of fitting
        self._model_model.blockSignals(True)
        self.iterateOverModel(updateFittedValues)
        self.iterateOverModel(updatePolyValues)
        self._model_model.blockSignals(False)

        if self.has_error_column:
            return

        error_column = []
        self.lstParams.itemDelegate().addErrorColumn()
        self.iterateOverModel(createErrorColumn)

        # switch off reponse to model change
        self._model_model.insertColumn(2, error_column)
        FittingUtilities.addErrorHeadersToModel(self._model_model)
        # Adjust the table cells width.
        # TODO: find a way to dynamically adjust column width while resized expanding
        self.lstParams.resizeColumnToContents(0)
        self.lstParams.resizeColumnToContents(4)
        self.lstParams.resizeColumnToContents(5)
        self.lstParams.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Expanding)

        self.has_error_column = True

    def updatePolyModelFromList(self, param_dict):
        """
        Update the polydispersity model with new parameters, create the errors column
        """
        assert isinstance(param_dict, dict)
        if not dict:
            return

        def iterateOverPolyModel(func):
            """
            Take func and throw it inside the poly model row loop
            """
            for row_i in range(self._poly_model.rowCount()):
                func(row_i)

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
            if self.has_poly_error_column:
                error_repr = GuiUtils.formatNumber(param_dict[param_name][1], high=True)
                self._poly_model.item(row_i, 2).setText(error_repr)


        def createErrorColumn(row_i):
            # Utility function for error column update
            if row_i >= self._poly_model.rowCount():
                return
            item = QtGui.QStandardItem()

            def createItem(param_name):
                error_repr = GuiUtils.formatNumber(param_dict[param_name][1], high=True)
                item.setText(error_repr)

            def poly_param():
                return str(self._poly_model.item(row_i, 0).text()).rsplit()[-1] + '.width'

            [createItem(param_name) for param_name in list(param_dict.keys()) if poly_param() == param_name]

            error_column.append(item)

        # block signals temporarily, so we don't end up
        # updating charts with every single model change on the end of fitting
        self._poly_model.blockSignals(True)
        iterateOverPolyModel(updateFittedValues)
        self._poly_model.blockSignals(False)

        if self.has_poly_error_column:
            return

        self.lstPoly.itemDelegate().addErrorColumn()
        error_column = []
        iterateOverPolyModel(createErrorColumn)

        # switch off reponse to model change
        self._poly_model.blockSignals(True)
        self._poly_model.insertColumn(2, error_column)
        self._poly_model.blockSignals(False)
        FittingUtilities.addErrorPolyHeadersToModel(self._poly_model)

        self.has_poly_error_column = True

    def updateMagnetModelFromList(self, param_dict):
        """
        Update the magnetic model with new parameters, create the errors column
        """
        assert isinstance(param_dict, dict)
        if not dict:
            return
        if self._magnet_model.rowCount() == 0:
            return

        def iterateOverMagnetModel(func):
            """
            Take func and throw it inside the magnet model row loop
            """
            for row_i in range(self._model_model.rowCount()):
                func(row_i)

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
            if self.has_magnet_error_column:
                error_repr = GuiUtils.formatNumber(param_dict[param_name][1], high=True)
                self._magnet_model.item(row, 2).setText(error_repr)

        def createErrorColumn(row):
            # Utility function for error column update
            item = QtGui.QStandardItem()
            def createItem(param_name):
                error_repr = GuiUtils.formatNumber(param_dict[param_name][1], high=True)
                item.setText(error_repr)
            def curr_param():
                return str(self._magnet_model.item(row, 0).text())

            [createItem(param_name) for param_name in list(param_dict.keys()) if curr_param() == param_name]

            error_column.append(item)

        # block signals temporarily, so we don't end up
        # updating charts with every single model change on the end of fitting
        self._magnet_model.blockSignals(True)
        iterateOverMagnetModel(updateFittedValues)
        self._magnet_model.blockSignals(False)

        if self.has_magnet_error_column:
            return

        self.lstMagnetic.itemDelegate().addErrorColumn()
        error_column = []
        iterateOverMagnetModel(createErrorColumn)

        # switch off reponse to model change
        self._magnet_model.blockSignals(True)
        self._magnet_model.insertColumn(2, error_column)
        self._magnet_model.blockSignals(False)
        FittingUtilities.addErrorHeadersToModel(self._magnet_model)

        self.has_magnet_error_column = True

    def onPlot(self):
        """
        Plot the current set of data
        """
        # Regardless of previous state, this should now be `plot show` functionality only
        self.cmdPlot.setText("Show Plot")
        # Force data recalculation so existing charts are updated
        self.recalculatePlotData()
        self.showPlot()

    def recalculatePlotData(self):
        """
        Generate a new dataset for model
        """
        if not self.data_is_loaded:
            self.createDefaultDataset()
        self.calculateQGridForModel()

    def showPlot(self):
        """
        Show the current plot in MPL
        """
        # Show the chart if ready
        data_to_show = self.data if self.data_is_loaded else self.model_data
        if data_to_show is not None:
            self.communicate.plotRequestedSignal.emit([data_to_show])

    def onOptionsUpdate(self):
        """
        Update local option values and replot
        """
        self.q_range_min, self.q_range_max, self.npts, self.log_points, self.weighting = \
            self.options_widget.state()
        # set Q range labels on the main tab
        self.lblMinRangeDef.setText(str(self.q_range_min))
        self.lblMaxRangeDef.setText(str(self.q_range_max))
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
        # Send original data for weighting
        weight = FittingUtilities.getWeight(data=data, is2d=self.is2D, flag=self.weighting)
        update_module = data.err_data if self.is2D else data.dy
        # Overwrite relevant values in data
        update_module = weight

    def updateQRange(self):
        """
        Updates Q Range display
        """
        if self.data_is_loaded:
            self.q_range_min, self.q_range_max, self.npts = self.logic.computeDataRange()
        # set Q range labels on the main tab
        self.lblMinRangeDef.setText(str(self.q_range_min))
        self.lblMaxRangeDef.setText(str(self.q_range_max))
        # set Q range labels on the options tab
        self.options_widget.updateQRange(self.q_range_min, self.q_range_max, self.npts)

    def SASModelToQModel(self, model_name, structure_factor=None):
        """
        Setting model parameters into table based on selected category
        """
        # Crete/overwrite model items
        self._model_model.clear()

        # First, add parameters from the main model
        if model_name is not None:
            self.fromModelToQModel(model_name)

        # Then, add structure factor derived parameters
        if structure_factor is not None and structure_factor != "None":
            if model_name is None:
                # Instantiate the current sasmodel for SF-only models
                self.kernel_module = self.models[structure_factor]()
            self.fromStructureFactorToQModel(structure_factor)
        else:
            # Allow the SF combobox visibility for the given sasmodel
            self.enableStructureFactorControl(structure_factor)

        # Then, add multishells
        if model_name is not None:
            # Multishell models need additional treatment
            self.addExtraShells()

        # Add polydispersity to the model
        self.setPolyModel()
        # Add magnetic parameters to the model
        self.setMagneticModel()

        # Adjust the table cells width
        self.lstParams.resizeColumnToContents(0)
        self.lstParams.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Expanding)

        # Now we claim the model has been loaded
        self.model_is_loaded = True
        # Change the model name to a monicker
        self.kernel_module.name = self.modelName()

        # (Re)-create headers
        FittingUtilities.addHeadersToModel(self._model_model)
        self.lstParams.header().setFont(self.boldFont)

        # Update Q Ranges
        self.updateQRange()

    def fromModelToQModel(self, model_name):
        """
        Setting model parameters into QStandardItemModel based on selected _model_
        """
        name = model_name
        if self.cbCategory.currentText() == CATEGORY_CUSTOM:
            # custom kernel load requires full path
            name = os.path.join(ModelUtilities.find_plugins_dir(), model_name+".py")
        kernel_module = generate.load_kernel_module(name)
        self.model_parameters = modelinfo.make_parameter_table(getattr(kernel_module, 'parameters', []))

        # Instantiate the current sasmodel
        self.kernel_module = self.models[model_name]()

        # Explicitly add scale and background with default values
        temp_undo_state = self.undo_supported
        self.undo_supported = False
        self.addScaleToModel(self._model_model)
        self.addBackgroundToModel(self._model_model)
        self.undo_supported = temp_undo_state

        self.shell_names = self.shellNamesList()

        # Update the QModel
        new_rows = FittingUtilities.addParametersToModel(self.model_parameters, self.kernel_module, self.is2D)

        for row in new_rows:
            self._model_model.appendRow(row)
        # Update the counter used for multishell display
        self._last_model_row = self._model_model.rowCount()

    def fromStructureFactorToQModel(self, structure_factor):
        """
        Setting model parameters into QStandardItemModel based on selected _structure factor_
        """
        structure_module = generate.load_kernel_module(structure_factor)
        structure_parameters = modelinfo.make_parameter_table(getattr(structure_module, 'parameters', []))
        structure_kernel = self.models[structure_factor]()

        self.kernel_module._model_info = product.make_product_info(self.kernel_module._model_info, structure_kernel._model_info)

        new_rows = FittingUtilities.addSimpleParametersToModel(structure_parameters, self.is2D)
        for row in new_rows:
            self._model_model.appendRow(row)
        # Update the counter used for multishell display
        self._last_model_row = self._model_model.rowCount()

    def onMainParamsChange(self, item):
        """
        Callback method for updating the sasmodel parameters with the GUI values
        """
        model_column = item.column()

        if model_column == 0:
            self.checkboxSelected(item)
            self.cmdFit.setEnabled(self.parameters_to_fit != [] and self.logic.data_is_loaded)
            # Update state stack
            self.updateUndo()
            return

        model_row = item.row()
        name_index = self._model_model.index(model_row, 0)

        # Extract changed value.
        try:
            value = GuiUtils.toDouble(item.text())
        except TypeError:
            # Unparsable field
            return

        parameter_name = str(self._model_model.data(name_index)) # sld, background etc.

        # Update the parameter value - note: this supports +/-inf as well
        self.kernel_module.params[parameter_name] = value

        # Update the parameter value - note: this supports +/-inf as well
        param_column = self.lstParams.itemDelegate().param_value
        min_column = self.lstParams.itemDelegate().param_min
        max_column = self.lstParams.itemDelegate().param_max
        if model_column == param_column:
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

        # Force the chart update when actual parameters changed
        if model_column == 1:
            self.recalculatePlotData()

        # Update state stack
        self.updateUndo()

    def isCheckable(self, row):
        return self._model_model.item(row, 0).isCheckable()

    def checkboxSelected(self, item):
        # Assure we're dealing with checkboxes
        if not item.isCheckable():
            return
        status = item.checkState()

        # If multiple rows selected - toggle all of them, filtering uncheckable
        # Switch off signaling from the model to avoid recursion
        self._model_model.blockSignals(True)
        # Convert to proper indices and set requested enablement
        self.setParameterSelection(status)
        #[self._model_model.item(row, 0).setCheckState(status) for row in self.selectedParameters()]
        self._model_model.blockSignals(False)

        # update the list of parameters to fit
        main_params = self.checkedListFromModel(self._model_model)
        poly_params = self.checkedListFromModel(self._poly_model)
        magnet_params = self.checkedListFromModel(self._magnet_model)

        # Retrieve poly params names
        poly_params = [param.rsplit()[-1] + '.width' for param in poly_params]

        self.parameters_to_fit = main_params + poly_params + magnet_params

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
            name = self.nameForFittedData(self.kernel_module.name)
            fitted_data.title = name
            fitted_data.name = name
            fitted_data.filename = name
            fitted_data.symbol = "Line"
            self.createTheoryIndex(fitted_data)

    def updateModelIndex(self, fitted_data):
        """
        Update a QStandardModelIndex containing model data
        """
        name = self.nameFromData(fitted_data)
        # Make this a line if no other defined
        if hasattr(fitted_data, 'symbol') and fitted_data.symbol is None:
            fitted_data.symbol = 'Line'
        # Notify the GUI manager so it can update the main model in DataExplorer
        GuiUtils.updateModelItemWithPlot(self._index, fitted_data, name)

    def createTheoryIndex(self, fitted_data):
        """
        Create a QStandardModelIndex containing model data
        """
        name = self.nameFromData(fitted_data)
        # Notify the GUI manager so it can create the theory model in DataExplorer
        new_item = GuiUtils.createModelItemWithPlot(fitted_data, name=name)
        self.communicate.updateTheoryFromPerspectiveSignal.emit(new_item)

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
        return self.complete1D if isinstance(self.data, Data1D) else self.complete2D

    def calculateQGridForModel(self):
        """
        Prepare the fitting data object, based on current ModelModel
        """
        if self.kernel_module is None:
            return
        # Awful API to a backend method.
        method = self.methodCalculateForData()(data=self.data,
                                               model=self.kernel_module,
                                               page_id=0,
                                               qmin=self.q_range_min,
                                               qmax=self.q_range_max,
                                               smearer=None,
                                               state=None,
                                               weight=None,
                                               fid=None,
                                               toggle_mode_on=False,
                                               completefn=None,
                                               update_chisqr=True,
                                               exception_handler=self.calcException,
                                               source=None)

        calc_thread = threads.deferToThread(method.compute)
        calc_thread.addCallback(self.methodCompleteForData())
        calc_thread.addErrback(self.calculateDataFailed)

    def calculateDataFailed(self, reason):
        """
        Thread returned error
        """
        print("Calculate Data failed with ", reason)

    def complete1D(self, return_data):
        """
        Plot the current 1D data
        """
        fitted_data = self.logic.new1DPlot(return_data, self.tab_id)
        self.calculateResiduals(fitted_data)
        self.model_data = fitted_data

    def complete2D(self, return_data):
        """
        Plot the current 2D data
        """
        fitted_data = self.logic.new2DPlot(return_data)
        self.calculateResiduals(fitted_data)
        self.model_data = fitted_data

    def calculateResiduals(self, fitted_data):
        """
        Calculate and print Chi2 and display chart of residuals
        """
        # Create a new index for holding data
        fitted_data.symbol = "Line"

        # Modify fitted_data with weighting
        self.addWeightingToData(fitted_data)

        self.createNewIndex(fitted_data)
        # Calculate difference between return_data and logic.data
        self.chi2 = FittingUtilities.calculateChi2(fitted_data, self.logic.data)
        # Update the control
        chi2_repr = "---" if self.chi2 is None else GuiUtils.formatNumber(self.chi2, high=True)
        self.lblChi2Value.setText(chi2_repr)

        self.communicate.plotUpdateSignal.emit([fitted_data])

        # Plot residuals if actual data
        if not self.data_is_loaded:
            return

        residuals_plot = FittingUtilities.plotResiduals(self.data, fitted_data)
        residuals_plot.id = "Residual " + residuals_plot.id
        self.createNewIndex(residuals_plot)
        #self.communicate.plotUpdateSignal.emit([residuals_plot])

    def calcException(self, etype, value, tb):
        """
        Thread threw an exception.
        """
        # TODO: remimplement thread cancellation
        logging.error("".join(traceback.format_exception(etype, value, tb)))

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

        [self.setPolyModelParameters(i, param) for i, param in \
            enumerate(self.model_parameters.form_volume_parameters) if param.polydisperse]
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
        width = self.kernel_module.getParam(param_name + '.width')
        npts = self.kernel_module.getParam(param_name + '.npts')
        nsigs = self.kernel_module.getParam(param_name + '.nsigmas')
        _, min, max = self.kernel_module.details[param_name]

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

        def updateFunctionCaption(row):
            # Utility function for update of polydispersity function name in the main model
            param_name = str(self._model_model.item(row, 0).text())
            if param_name !=  param.name:
                return
            # Modify the param value
            self._model_model.item(row, 0).child(0).child(0,4).setText(combo_string)

        if combo_string == 'array':
            try:
                self.loadPolydispArray(row_index)
                # Update main model for display
                self.iterateOverModel(updateFunctionCaption)
                # disable the row
                lo = self.lstPoly.itemDelegate().poly_pd
                hi = self.lstPoly.itemDelegate().poly_function
                [self._poly_model.item(row_index, i).setEnabled(False) for i in range(lo, hi)]
                return
            except IOError:
                combo_box.setCurrentIndex(self.orig_poly_index)
                # Pass for cancel/bad read
                pass

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
        self.orig_poly_index = combo_box.currentIndex()

    def loadPolydispArray(self, row_index):
        """
        Show the load file dialog and loads requested data into state
        """
        datafile = QtWidgets.QFileDialog.getOpenFileName(
            self, "Choose a weight file", "", "All files (*.*)", None,
            QtWidgets.QFileDialog.DontUseNativeDialog)[0]

        if not datafile:
            logging.info("No weight data chosen.")
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
        self.disp_model = POLYDISPERSITY_MODELS['array']()
        self.disp_model.set_weights(np.array(values), np.array(weights))
        # + update the cell with filename
        fname = os.path.basename(str(datafile))
        fname_index = self._poly_model.index(row_index, self.lstPoly.itemDelegate().poly_filename)
        self._poly_model.setData(fname_index, fname)

    def setMagneticModel(self):
        """
        Set magnetism values on model
        """
        if not self.model_parameters:
            return
        self._magnet_model.clear()
        [self.addCheckedMagneticListToModel(param, self._magnet_model) for param in \
            self.model_parameters.call_parameters if param.type == 'magnetic']
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

    def addCheckedMagneticListToModel(self, param, model):
        """
        Wrapper for model update with a subset of magnetic parameters
        """
        if param.name[param.name.index(':')+1:] in self.shell_names:
            # check if two-digit shell number
            try:
                shell_index = int(param.name[-2:])
            except ValueError:
                shell_index = int(param.name[-1:])

            if shell_index > self.current_shell_displayed:
                return

        checked_list = [param.name,
                        str(param.default),
                        str(param.limits[0]),
                        str(param.limits[1]),
                        param.units]

        FittingUtilities.addCheckedListToModel(model, checked_list)

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
        # Available range of shells displayed in the combobox
        func.addItems([str(i) for i in range(param_length+1)])

        # Respond to index change
        func.currentIndexChanged.connect(self.modifyShellsInList)

        # cell 2: combobox
        item2 = QtGui.QStandardItem()
        self._model_model.appendRow([item1, item2])

        # Beautify the row:  span columns 2-4
        shell_row = self._model_model.rowCount()
        shell_index = self._model_model.index(shell_row-1, 1)

        self.lstParams.setIndexWidget(shell_index, func)
        self._last_model_row = self._model_model.rowCount()

        # Set the index to the state-kept value
        func.setCurrentIndex(self.current_shell_displayed
                             if self.current_shell_displayed < func.count() else 0)

    def modifyShellsInList(self, index):
        """
        Add/remove additional multishell parameters
        """
        # Find row location of the combobox
        last_row = self._last_model_row
        remove_rows = self._model_model.rowCount() - last_row

        if remove_rows > 1:
            self._model_model.removeRows(last_row, remove_rows)

        FittingUtilities.addShellsToModel(self.model_parameters, self._model_model, index)
        self.current_shell_displayed = index

        # Update relevant models
        self.setPolyModel()
        self.setMagneticModel()

    def setFittingStarted(self):
        """
        Set item enablement on fitting start
        """
        #disable the Fit button
        self.cmdFit.setText('Running...')
        self.cmdFit.setEnabled(False)

    def setFittingStopped(self):
        """
        Set item enablement on fitting stop
        """
        #enable the Fit button
        self.cmdFit.setText("Fit")
        self.cmdFit.setEnabled(True)

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
        fp.parameters_to_fit = self.parameters_to_fit
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

