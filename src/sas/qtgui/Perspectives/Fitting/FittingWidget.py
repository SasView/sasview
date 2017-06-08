import json
import os
from collections import defaultdict
from itertools import izip

import logging
import traceback
from twisted.internet import threads
import numpy as np

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4 import QtWebKit

from sasmodels import generate
from sasmodels import modelinfo
from sasmodels.sasview_model import load_standard_models
from sasmodels.weights import MODELS as POLYDISPERSITY_MODELS

from sas.sascalc.fit.BumpsFitting import BumpsFit as Fit

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Utilities.CategoryInstaller import CategoryInstaller
from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Plotting.PlotterData import Data2D

from sas.qtgui.Perspectives.Fitting.UI.FittingWidgetUI import Ui_FittingWidgetUI
from sas.qtgui.Perspectives.Fitting.FitThread import FitThread
from sas.qtgui.Perspectives.Fitting.ModelThread import Calc1D
from sas.qtgui.Perspectives.Fitting.ModelThread import Calc2D
from sas.qtgui.Perspectives.Fitting.FittingLogic import FittingLogic
from sas.qtgui.Perspectives.Fitting import FittingUtilities
from sas.qtgui.Perspectives.Fitting.SmearingWidget import SmearingWidget
from sas.qtgui.Perspectives.Fitting.OptionsWidget import OptionsWidget
from sas.qtgui.Perspectives.Fitting.FitPage import FitPage
from sas.qtgui.Perspectives.Fitting.ViewDelegate import ModelViewDelegate
from sas.qtgui.Perspectives.Fitting.ViewDelegate import PolyViewDelegate

TAB_MAGNETISM = 4
TAB_POLY = 3
CATEGORY_DEFAULT = "Choose category..."
CATEGORY_STRUCTURE = "Structure Factor"
STRUCTURE_DEFAULT = "None"

DEFAULT_POLYDISP_FUNCTION = 'gaussian'

# Mapping between column index and relevant parameter name extension
POLY_COL_NAME = 0
POLY_COL_WIDTH = 1
POLY_COL_MIN = 2
POLY_COL_MAX = 3
POLY_COL_NPTS = 4
POLY_COL_NSIGMAS = 5
POLY_COL_FUNCTION = 6
POLY_COLUMN_DICT = {
    POLY_COL_WIDTH:   'width',
    POLY_COL_MIN:     'min',
    POLY_COL_MAX:     'max',
    POLY_COL_NPTS:    'npts',
    POLY_COL_NSIGMAS: 'nsigmas'}

class FittingWidget(QtGui.QWidget, Ui_FittingWidgetUI):
    """
    Main widget for selecting form and structure factor models
    """
    def __init__(self, parent=None, data=None, tab_id=1):

        super(FittingWidget, self).__init__()

        # Necessary globals
        self.parent = parent

        # Which tab is this widget displayed in?
        self.tab_id = tab_id

        # Main Data[12]D holder
        self.logic = FittingLogic(data=data)

        # Globals
        self.initializeGlobals()

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
        self.helpView = QtWebKit.QWebView()

        self._index = None
        if data is not None:
            self.data = data

    def close(self):
        """
        Remember to kill off things on exit
        """
        self.helpView.close()
        del self.helpView

    @property
    def data(self):
        return self.logic.data

    @data.setter
    def data(self, value):
        """ data setter """
        assert isinstance(value, QtGui.QStandardItem)
        # _index contains the QIndex with data
        self._index = value

        # Update logics with data items
        self.logic.data = GuiUtils.dataFromItem(value)

        # Overwrite data type descriptor
        self.is2D = True if isinstance(self.logic.data, Data2D) else False

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

        # Data for chosen model
        self.model_data = None

        # Which shell is being currently displayed?
        self.current_shell_displayed = 0
        self.has_error_column = False
        self.has_poly_error_column = False

        # signal communicator
        self.communicate = self.parent.communicate

    def initializeWidgets(self):
        """
        Initialize widgets for tabs
        """
        # Options widget
        layout = QtGui.QGridLayout()
        self.options_widget = OptionsWidget(self, self.logic)
        layout.addWidget(self.options_widget)
        self.tabOptions.setLayout(layout)

        # Smearing widget
        layout = QtGui.QGridLayout()
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

    def initializeModels(self):
        """
        Set up models and views
        """
        # Set the main models
        # We can't use a single model here, due to restrictions on flattening
        # the model tree with subclassed QAbstractProxyModel...
        self._model_model = QtGui.QStandardItemModel()
        self._poly_model = QtGui.QStandardItemModel()
        self._magnet_model = QtGui.QStandardItemModel()

        # Param model displayed in param list
        self.lstParams.setModel(self._model_model)
        self.readCategoryInfo()
        self.model_parameters = None

        # Delegates for custom editing and display
        self.lstParams.setItemDelegate(ModelViewDelegate(self))

        self.lstParams.setAlternatingRowColors(True)
        stylesheet = """
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
        self.lstParams.customContextMenuRequested.connect(self.showModelDescription)

        # Poly model displayed in poly list
        self.lstPoly.setModel(self._poly_model)
        self.setPolyModel()
        self.setTableProperties(self.lstPoly)
        # Delegates for custom editing and display
        self.lstPoly.setItemDelegate(PolyViewDelegate(self))
        # Polydispersity function combo response
        self.lstPoly.itemDelegate().combo_updated.connect(self.onPolyComboIndexChange)

        # Magnetism model displayed in magnetism list
        self.lstMagnetic.setModel(self._magnet_model)
        self.setMagneticModel()
        self.setTableProperties(self.lstMagnetic)

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
        self.chkMagnetism.setEnabled(True)
        # Similarly on other tabs
        self.options_widget.setEnablementOnDataLoad()

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

    def toggle2D(self, isChecked):
        """ Enable/disable the controls dependent on 1D/2D data instance """
        self.chkMagnetism.setEnabled(isChecked)
        self.is2D = isChecked
        # Reload the current model
        if self.kernel_module:
            self.onSelectModel()

    def initializeControls(self):
        """
        Set initial control enablement
        """
        self.cmdFit.setEnabled(False)
        self.cmdPlot.setEnabled(False)
        self.options_widget.cmdComputePoints.setVisible(False) # probably redundant
        self.chkPolydispersity.setEnabled(True)
        self.chkPolydispersity.setCheckState(False)
        self.chk2DView.setEnabled(True)
        self.chk2DView.setCheckState(False)
        self.chkMagnetism.setEnabled(False)
        self.chkMagnetism.setCheckState(False)
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
        # Checkboxes
        self.chk2DView.toggled.connect(self.toggle2D)
        self.chkPolydispersity.toggled.connect(self.togglePoly)
        self.chkMagnetism.toggled.connect(self.toggleMagnetism)
        # Buttons
        self.cmdFit.clicked.connect(self.onFit)
        self.cmdPlot.clicked.connect(self.onPlot)
        self.cmdHelp.clicked.connect(self.onHelp)

        # Respond to change in parameters from the UI
        self._model_model.itemChanged.connect(self.updateParamsFromModel)
        self._poly_model.itemChanged.connect(self.onPolyModelChange)

        # TODO after the poly_model prototype accepted
        #self._magnet_model.itemChanged.connect(self.onMagneticModelChange)

        # Signals from separate tabs asking for replot
        self.options_widget.plot_signal.connect(self.onOptionsUpdate)

    def showModelDescription(self, position):
        """
        Shows a window with model description, when right clicked in the treeview
        """
        msg = 'Model description:\n'
        if self.kernel_module is not None:
            if str(self.kernel_module.description).rstrip().lstrip() == '':
                msg += "Sorry, no information is available for this model."
            else:
                msg += self.kernel_module.description + '\n'
        else:
            msg += "You must select a model to get information on this"

        menu = QtGui.QMenu()
        label = QtGui.QLabel(msg)
        action = QtGui.QWidgetAction(self)
        action.setDefaultWidget(label)
        menu.addAction(action)
        menu.exec_(self.lstParams.viewport().mapToGlobal(position))

    def onSelectModel(self):
        """
        Respond to select Model from list event
        """
        model = str(self.cbModel.currentText())

        # Reset structure factor
        self.cbStructureFactor.setCurrentIndex(0)

        # Reset parameters to fit
        self.parameters_to_fit = None
        self.has_error_column = False
        self.has_poly_error_column = False

        self.respondToModelStructure(model=model, structure_factor=None)

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

    def respondToModelStructure(self, model=None, structure_factor=None):
        # Set enablement on calculate/plot
        self.cmdPlot.setEnabled(True)

        # kernel parameters -> model_model
        self.SASModelToQModel(model, structure_factor)

        if self.data_is_loaded:
            self.cmdPlot.setText("Show Plot")
            self.calculateQGridForModel()
        else:
            self.cmdPlot.setText("Calculate")
            # Create default datasets if no data passed
            self.createDefaultDataset()

        # Update state stack
        self.updateUndo()

    def onSelectCategory(self):
        """
        Select Category from list
        """
        category = str(self.cbCategory.currentText())
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
        parameter_name = str(name_index.data().toString()).lower() # "distribution of sld" etc.
        if "distribution of" in parameter_name:
            # just the last word
            parameter_name = parameter_name.rsplit()[-1]

        # Extract changed value.
        if model_column == POLY_COL_NAME:
            # Is the parameter checked for fitting?
            value = item.checkState()
            parameter_name = parameter_name+'.width'
            if value == QtCore.Qt.Checked:
                self.parameters_to_fit.append(parameter_name)
            else:
                if parameter_name in self.parameters_to_fit:
                    self.parameters_to_fit.remove(parameter_name)
            return
        elif model_column in [POLY_COL_MIN, POLY_COL_MAX]:
            try:
                value = float(item.text())
            except ValueError:
                # Can't be converted properly, bring back the old value and exit
                return

            property_name = str(self._poly_model.headerData(model_column, 1).toPyObject()).lower() # Value, min, max, etc.
            # print "%s(%s) => %d" % (parameter_name, property_name, value)
            current_details = self.kernel_module.details[parameter_name]
            current_details[model_column-1] = value
        else:
            try:
                value = float(item.text())
            except ValueError:
                # Can't be converted properly, bring back the old value and exit
                return

            property_name = str(self._poly_model.headerData(model_column, 1).toPyObject()).lower() # Value, min, max, etc.
            # print "%s(%s) => %d" % (parameter_name, property_name, value)

            # Update the sasmodel
            # PD[ratio] -> width, npts -> npts, nsigs -> nsigmas
            self.kernel_module.setParam(parameter_name + '.' + POLY_COLUMN_DICT[model_column], value)

        # Reload the main model - may not be required if no variable is shown in main view
        #model = str(self.cbModel.currentText())
        #self.SASModelToQModel(model)

        pass # debug anchor

    def onHelp(self):
        """
        Show the "Fitting" section of help
        """
        tree_location = self.parent.HELP_DIRECTORY_LOCATION +\
            "/user/sasgui/perspectives/fitting/fitting_help.html"
        self.helpView.load(QtCore.QUrl(tree_location))
        self.helpView.show()

    def onFit(self):
        """
        Perform fitting on the current data
        """
        fitter = Fit()

        # Data going in
        data = self.logic.data
        model = self.kernel_module
        qmin = self.q_range_min
        qmax = self.q_range_max
        params_to_fit = self.parameters_to_fit

        # Potential weights added directly to data
        self.addWeightingToData(data)

        # Potential smearing added
        # Remember that smearing_min/max can be None ->
        # deal with it until Python gets discriminated unions
        smearing, accuracy, smearing_min, smearing_max = self.smearing_widget.state()

        # These should be updating somehow?
        fit_id = 0
        constraints = []
        smearer = None
        page_id = [210]
        handler = None
        batch_inputs = {}
        batch_outputs = {}
        list_page_id = [page_id]
        #---------------------------------

        # Parameterize the fitter
        fitter.set_model(model, fit_id, params_to_fit, data=data,
                         constraints=constraints)

        fitter.set_data(data=data, id=fit_id, smearer=smearer, qmin=qmin,
                        qmax=qmax)
        fitter.select_problem_for_fit(id=fit_id, value=1)

        fitter.fitter_id = page_id

        # Create the fitting thread, based on the fitter
        calc_fit = FitThread(handler=handler,
                             fn=[fitter],
                             batch_inputs=batch_inputs,
                             batch_outputs=batch_outputs,
                             page_id=list_page_id,
                             updatefn=self.updateFit,
                             completefn=None)

        # start the trhrhread
        calc_thread = threads.deferToThread(calc_fit.compute)
        calc_thread.addCallback(self.fitComplete)
        calc_thread.addErrback(self.fitFailed)

        #disable the Fit button
        self.cmdFit.setText('Calculating...')
        self.communicate.statusBarUpdateSignal.emit('Fitting started...')
        self.cmdFit.setEnabled(False)

    def updateFit(self):
        """
        """
        print "UPDATE FIT"
        pass

    def fitFailed(self, reason):
        """
        """
        print "FIT FAILED: ", reason
        pass

    def fitComplete(self, result):
        """
        Receive and display fitting results
        "result" is a tuple of actual result list and the fit time in seconds
        """
        #re-enable the Fit button
        self.cmdFit.setText("Fit")
        self.cmdFit.setEnabled(True)

        assert result is not None

        res_list = result[0]
        res = res_list[0]
        if res.fitness is None or \
            not np.isfinite(res.fitness) or \
            np.any(res.pvec is None) or \
            not np.all(np.isfinite(res.pvec)):
            msg = "Fitting did not converge!!!"
            self.communicate.statusBarUpdateSignal.emit(msg)
            logging.error(msg)
            return

        elapsed = result[1]
        msg = "Fitting completed successfully in: %s s.\n" % GuiUtils.formatNumber(elapsed)
        self.communicate.statusBarUpdateSignal.emit(msg)

        self.chi2 = res.fitness
        param_list = res.param_list # ['radius', 'radius.width']
        param_values = res.pvec     # array([ 0.36221662,  0.0146783 ])
        param_stderr = res.stderr   # array([ 1.71293015,  1.71294233])
        params_and_errors = zip(param_values, param_stderr)
        param_dict = dict(izip(param_list, params_and_errors))

        # Dictionary of fitted parameter: value, error
        # e.g. param_dic = {"sld":(1.703, 0.0034), "length":(33.455, -0.0983)}
        self.updateModelFromList(param_dict)

        self.updatePolyModelFromList(param_dict)

        # update charts
        self.onPlot()

        # Read only value - we can get away by just printing it here
        chi2_repr = GuiUtils.formatNumber(self.chi2, high=True)
        self.lblChi2Value.setText(chi2_repr)

    def iterateOverModel(self, func):
        """
        Take func and throw it inside the model row loop
        """
        for row_i in xrange(self._model_model.rowCount()):
            func(row_i)

    def updateModelFromList(self, param_dict):
        """
        Update the model with new parameters, create the errors column
        """
        assert isinstance(param_dict, dict)
        if not dict:
            return

        def updateFittedValues(row_i):
            # Utility function for main model update
            # internal so can use closure for param_dict
            param_name = str(self._model_model.item(row_i, 0).text())
            if param_name not in param_dict.keys():
                return
            # modify the param value
            param_repr = GuiUtils.formatNumber(param_dict[param_name][0], high=True)
            self._model_model.item(row_i, 1).setText(param_repr)
            if self.has_error_column:
                error_repr = GuiUtils.formatNumber(param_dict[param_name][1], high=True)
                self._model_model.item(row_i, 2).setText(error_repr)

        def createErrorColumn(row_i):
            # Utility function for error column update
            item = QtGui.QStandardItem()
            for param_name in param_dict.keys():
                if str(self._model_model.item(row_i, 0).text()) != param_name:
                    continue
                error_repr = GuiUtils.formatNumber(param_dict[param_name][1], high=True)
                item.setText(error_repr)
            error_column.append(item)

        # block signals temporarily, so we don't end up
        # updating charts with every single model change on the end of fitting
        self._model_model.blockSignals(True)
        self.iterateOverModel(updateFittedValues)
        self._model_model.blockSignals(False)

        if self.has_error_column:
            return

        error_column = []
        self.iterateOverModel(createErrorColumn)

        # switch off reponse to model change
        self._model_model.blockSignals(True)
        self._model_model.insertColumn(2, error_column)
        self._model_model.blockSignals(False)
        FittingUtilities.addErrorHeadersToModel(self._model_model)
        # Adjust the table cells width.
        # TODO: find a way to dynamically adjust column width while resized expanding
        self.lstParams.resizeColumnToContents(0)
        self.lstParams.resizeColumnToContents(4)
        self.lstParams.resizeColumnToContents(5)
        self.lstParams.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Expanding)

        self.has_error_column = True

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
            if param_name not in param_dict.keys():
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
            for param_name in param_dict.keys():
                if str(self._poly_model.item(row_i, 0).text()).rsplit()[-1] + '.width' != param_name:
                    continue
                error_repr = GuiUtils.formatNumber(param_dict[param_name][1], high=True)
                item.setText(error_repr)
            error_column.append(item)

        # block signals temporarily, so we don't end up
        # updating charts with every single model change on the end of fitting
        self._poly_model.blockSignals(True)
        self.iterateOverModel(updateFittedValues)
        self._poly_model.blockSignals(False)

        #return

        if self.has_poly_error_column:
            return

        # Duck type delegate variables
        self.lstPoly.itemDelegate().POLY_MIN = 3
        self.lstPoly.itemDelegate().POLY_MAX = 4
        self.lstPoly.itemDelegate().POLY_NPTS = 5
        self.lstPoly.itemDelegate().POLY_NSIGS = 6
        self.lstPoly.itemDelegate().POLY_FUNCTION = 7

        error_column = []
        self.iterateOverModel(createErrorColumn)

        # switch off reponse to model change
        self._poly_model.blockSignals(True)
        self._poly_model.insertColumn(2, error_column)
        self._poly_model.blockSignals(False)
        FittingUtilities.addErrorPolyHeadersToModel(self._poly_model)

        self.has_poly_error_column = True

    def onPlot(self):
        """
        Plot the current set of data
        """
        # Regardless of previous state, this should now be `plot show` functionality only
        self.cmdPlot.setText("Show Plot")
        if not self.data_is_loaded:
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
        self.lstParams.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Expanding)

        # Now we claim the model has been loaded
        self.model_is_loaded = True

        # (Re)-create headers
        FittingUtilities.addHeadersToModel(self._model_model)
        self.lstParams.header().setFont(self.boldFont)

        # Update Q Ranges
        self.updateQRange()

    def fromModelToQModel(self, model_name):
        """
        Setting model parameters into QStandardItemModel based on selected _model_
        """
        kernel_module = generate.load_kernel_module(model_name)
        self.model_parameters = modelinfo.make_parameter_table(getattr(kernel_module, 'parameters', []))

        # Instantiate the current sasmodel
        self.kernel_module = self.models[model_name]()

        # Explicitly add scale and background with default values
        temp_undo_state = self.undo_supported
        self.undo_supported = False
        self.addScaleToModel(self._model_model)
        self.addBackgroundToModel(self._model_model)
        self.undo_supported = temp_undo_state

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

        new_rows = FittingUtilities.addSimpleParametersToModel(structure_parameters, self.is2D)
        for row in new_rows:
            self._model_model.appendRow(row)
        # Update the counter used for multishell display
        self._last_model_row = self._model_model.rowCount()

    def updateParamsFromModel(self, item):
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

        # Extract changed value. Assumes proper validation by QValidator/Delegate
        try:
            value = float(item.text())
        except ValueError:
            # Unparsable field
            return
        parameter_name = str(self._model_model.data(name_index).toPyObject()) # sld, background etc.
        property_index = self._model_model.headerData(1, model_column).toInt()[0]-1 # Value, min, max, etc.

        # Update the parameter value - note: this supports +/-inf as well
        self.kernel_module.params[parameter_name] = value

        # min/max to be changed in self.kernel_module.details[parameter_name] = ['Ang', 0.0, inf]
        self.kernel_module.details[parameter_name][property_index] = value

        # TODO: magnetic params in self.kernel_module.details['M0:parameter_name'] = value
        # TODO: multishell params in self.kernel_module.details[??] = value

        # Force the chart update when actual parameters changed
        if model_column == 1:
            self.recalculatePlotData()

        # Update state stack
        self.updateUndo()

    def checkboxSelected(self, item):
        # Assure we're dealing with checkboxes
        if not item.isCheckable():
            return
        status = item.checkState()

        def isCheckable(row):
            return self._model_model.item(row, 0).isCheckable()

        # If multiple rows selected - toggle all of them, filtering uncheckable
        rows = [s.row() for s in self.lstParams.selectionModel().selectedRows() if isCheckable(s.row())]

        # Switch off signaling from the model to avoid recursion
        self._model_model.blockSignals(True)
        # Convert to proper indices and set requested enablement
        [self._model_model.item(row, 0).setCheckState(status) for row in rows]
        self._model_model.blockSignals(False)

        # update the list of parameters to fit
        main_params = self.checkedListFromModel(self._model_model)
        poly_params = self.checkedListFromModel(self._poly_model)
        # Retrieve poly params names
        poly_params = [param.rsplit()[-1] + '.width' for param in poly_params]
        # TODO : add magnetic params

        self.parameters_to_fit = main_params + poly_params

    def checkedListFromModel(self, model):
        """
        Returns list of checked parameters for given model
        """
        def isChecked(row):
            return model.item(row, 0).checkState() == QtCore.Qt.Checked

        return [str(model.item(row_index, 0).text())
                for row_index in xrange(model.rowCount())
                if isChecked(row_index)]

    def nameForFittedData(self, name):
        """
        Generate name for the current fit
        """
        if self.is2D:
            name += "2d"
        name = "M%i [%s]" % (self.tab_id, name)
        return name

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
        GuiUtils.updateModelItemWithPlot(self._index, QtCore.QVariant(fitted_data), name)

    def createTheoryIndex(self, fitted_data):
        """
        Create a QStandardModelIndex containing model data
        """
        name = self.nameFromData(fitted_data)
        # Notify the GUI manager so it can create the theory model in DataExplorer
        new_item = GuiUtils.createModelItemWithPlot(QtCore.QVariant(fitted_data), name=name)
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
        print "Calculate Data failed with ", reason

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
        self.communicate.plotUpdateSignal.emit([residuals_plot])

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
        table.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Expanding)
        table.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        table.resizeColumnsToContents()

        # Header
        header = table.horizontalHeader()
        header.setResizeMode(QtGui.QHeaderView.ResizeToContents)

        header.ResizeMode(QtGui.QHeaderView.Interactive)
        # Resize column 0 and 6 to content
        header.setResizeMode(0, QtGui.QHeaderView.ResizeToContents)
        header.setResizeMode(6, QtGui.QHeaderView.ResizeToContents)

    def setPolyModel(self):
        """
        Set polydispersity values
        """
        if not self.model_parameters:
            return
        self._poly_model.clear()

        [self.setPolyModelParameters(row, param) for row, param in \
            enumerate(self.model_parameters.form_volume_parameters) if param.polydisperse]
        FittingUtilities.addPolyHeadersToModel(self._poly_model)

    def setPolyModelParameters(self, row, param):
        """
        Creates a checked row of for a polydisperse parameter
        """
        # Not suitable for multishell
        if '[' in param.name:
            return
        # Values from the sasmodel
        width = self.kernel_module.getParam(param.name+'.width')
        npts = self.kernel_module.getParam(param.name+'.npts')
        nsigs = self.kernel_module.getParam(param.name+'.nsigmas')
        # Potential multishell params
        checked_list = ["Distribution of "+param.name, str(width),
                        str(param.limits[0]), str(param.limits[1]),
                        str(npts), str(nsigs), "gaussian      "]
        FittingUtilities.addCheckedListToModel(self._poly_model, checked_list)

        # All possible polydisp. functions as strings in combobox
        func = QtGui.QComboBox()
        func.addItems([str(name_disp) for name_disp in POLYDISPERSITY_MODELS.iterkeys()])
        # Default index
        func.setCurrentIndex(func.findText(DEFAULT_POLYDISP_FUNCTION))
        # Index in the view
        #func_index = self.lstPoly.model().index(row, 6)

    def onPolyComboIndexChange(self, combo_string, row_index):
        """
        Modify polydisp. defaults on function choice
        """
        # get npts/nsigs for current selection
        param = self.model_parameters.form_volume_parameters[row_index]

        if combo_string == 'array':
            try:
                self.loadPolydispArray()
            except (ValueError, IOError):
                # Don't do anything if file lookup failed
                return
            # disable the row
            [self._poly_model.item(row_index, i).setEnabled(False) for i in xrange(6)]
            return

        # Enable the row in case it was disabled by Array
        #[self._poly_model.item(row_index, i).setEnabled(True) for i in xrange(6)]

        npts_index = self._poly_model.index(row_index, POLY_COL_NPTS)
        nsigs_index = self._poly_model.index(row_index, POLY_COL_NSIGMAS)

        npts = POLYDISPERSITY_MODELS[str(combo_string)].default['npts']
        nsigs = POLYDISPERSITY_MODELS[str(combo_string)].default['nsigmas']

        self._poly_model.setData(npts_index, QtCore.QVariant(npts))
        self._poly_model.setData(nsigs_index, QtCore.QVariant(nsigs))

    def loadPolydispArray(self):
        """
        Show the load file dialog and loads requested data into state
        """
        datafile = QtGui.QFileDialog.getOpenFileName(
            self, "Choose a weight file", "", "All files (*.*)")
        if not datafile:
            logging.info("No weight data chosen.")
            return
        values = []
        weights = []
        with open(datafile, 'r') as column_file:
            column_data = [line.rstrip().split() for line in column_file.readlines()]
            for line in column_data:
                try:
                    values.append(float(line[0]))
                    weights.append(float(line[1]))
                except (ValueError, IndexError):
                    # just pass through if line with bad data
                    pass

        self.disp_model = POLYDISPERSITY_MODELS['array']()
        self.disp_model.set_weights(np.array(values), np.array(weights))

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

    def addCheckedMagneticListToModel(self, param, model):
        """
        Wrapper for model update with a subset of magnetic parameters
        """
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

        func = QtGui.QComboBox()
        # Available range of shells displayed in the combobox
        func.addItems([str(i) for i in xrange(param_length+1)])

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

