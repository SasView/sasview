import sys
import json
import os
import numpy
from collections import defaultdict
from itertools import izip

import logging
import traceback
from twisted.internet import threads

from PyQt4 import QtGui
from PyQt4 import QtCore

from sasmodels import generate
from sasmodels import modelinfo
from sasmodels.sasview_model import load_standard_models
from sas.sascalc.fit.BumpsFitting import BumpsFit as Fit
from sas.sasgui.perspectives.fitting.fit_thread import FitThread

from sas.sasgui.guiframe.CategoryInstaller import CategoryInstaller
from sas.sasgui.guiframe.dataFitting import Data1D
from sas.sasgui.guiframe.dataFitting import Data2D
import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.sasgui.perspectives.fitting.model_thread import Calc1D
from sas.sasgui.perspectives.fitting.model_thread import Calc2D

from UI.FittingWidgetUI import Ui_FittingWidgetUI
from sas.qtgui.Perspectives.Fitting.FittingLogic import FittingLogic
from sas.qtgui.Perspectives.Fitting import FittingUtilities

TAB_MAGNETISM = 4
TAB_POLY = 3
CATEGORY_DEFAULT = "Choose category..."
CATEGORY_STRUCTURE = "Structure Factor"
STRUCTURE_DEFAULT = "None"
QMIN_DEFAULT = 0.0005
QMAX_DEFAULT = 0.5
NPTS_DEFAULT = 50

class FittingWidget(QtGui.QWidget, Ui_FittingWidgetUI):
    """
    Main widget for selecting form and structure factor models
    """
    def __init__(self, parent=None, data=None, id=1):

        super(FittingWidget, self).__init__()

        # Necessary globals
        self.parent = parent
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

        # Which tab is this widget displayed in?
        self.tab_id = id

        # Which shell is being currently displayed?
        self.current_shell_displayed = 0
        self.has_error_column = False

        # Range parameters
        self.q_range_min = QMIN_DEFAULT
        self.q_range_max = QMAX_DEFAULT
        self.npts = NPTS_DEFAULT

        # Main Data[12]D holder
        self.logic = FittingLogic(data=data)

        # Main GUI setup up
        self.setupUi(self)
        self.setWindowTitle("Fitting")
        self.communicate = self.parent.communicate

        # Define bold font for use in various controls
        self.boldFont=QtGui.QFont()
        self.boldFont.setBold(True)

        # Set data label
        self.label.setFont(self.boldFont)
        self.label.setText("No data loaded")
        self.lblFilename.setText("")

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
        self.lstParams.setAlternatingRowColors(True)

        # Poly model displayed in poly list
        self.lstPoly.setModel(self._poly_model)
        self.setPolyModel()
        self.setTableProperties(self.lstPoly)

        # Magnetism model displayed in magnetism list
        self.lstMagnetic.setModel(self._magnet_model)
        self.setMagneticModel()
        self.setTableProperties(self.lstMagnetic)

        # Defaults for the structure factors
        self.setDefaultStructureCombo()

        # Make structure factor and model CBs disabled
        self.disableModelCombo()
        self.disableStructureCombo()

        # Generate the category list for display
        category_list = sorted(self.master_category_dict.keys())
        self.cbCategory.addItem(CATEGORY_DEFAULT)
        self.cbCategory.addItems(category_list)
        self.cbCategory.addItem(CATEGORY_STRUCTURE)
        self.cbCategory.setCurrentIndex(0)

        # Connect signals to controls
        self.initializeSignals()

        # Initial control state
        self.initializeControls()

        self._index = None
        if data is not None:
            self.data = data

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

        self.data_is_loaded = True
        # Tag along functionality
        self.label.setText("Data loaded from: ")
        self.lblFilename.setText(self.logic.data.filename)
        self.updateQRange()
        self.cmdFit.setEnabled(True)
        self.boxWeighting.setEnabled(True)
        self.cmdMaskEdit.setEnabled(True)
        # Switch off txtNpts related controls
        self.txtNpts.setEnabled(False)
        self.txtNptsFit.setEnabled(False)
        self.chkLogData.setEnabled(False)

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
        self.onSelectModel()

    def toggleLogData(self, isChecked):
        """ Toggles between log and linear data sets """
        pass

    def initializeControls(self):
        """
        Set initial control enablement
        """
        self.cmdFit.setEnabled(False)
        self.cmdPlot.setEnabled(True)
        self.cmdComputePoints.setVisible(False) # probably redundant
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
        # group boxes
        self.boxWeighting.setEnabled(False)
        self.cmdMaskEdit.setEnabled(False)

    def initializeSignals(self):
        """
        Connect GUI element signals
        """
        # Comboboxes
        self.cbStructureFactor.currentIndexChanged.connect(self.onSelectStructureFactor)
        self.cbCategory.currentIndexChanged.connect(self.onSelectCategory)
        self.cbModel.currentIndexChanged.connect(self.onSelectModel)
        self.cbSmearing.currentIndexChanged.connect(self.onSelectSmearing)
        # Checkboxes
        self.chk2DView.toggled.connect(self.toggle2D)
        self.chkPolydispersity.toggled.connect(self.togglePoly)
        self.chkMagnetism.toggled.connect(self.toggleMagnetism)
        self.chkLogData.toggled.connect(self.toggleLogData)
        # Buttons
        self.cmdFit.clicked.connect(self.onFit)
        self.cmdPlot.clicked.connect(self.onPlot)
        self.cmdMaskEdit.clicked.connect(self.onMaskEdit)
        self.cmdReset.clicked.connect(self.onReset)
        # Line edits
        self.txtNpts.editingFinished.connect(self.onNpts)
        self.txtMinRange.editingFinished.connect(self.onMinRange)
        self.txtMaxRange.editingFinished.connect(self.onMaxRange)
        self.txtSmearUp.editingFinished.connect(self.onSmearUp)
        self.txtSmearDown.editingFinished.connect(self.onSmearDown)

        # Respond to change in parameters from the UI
        self._model_model.itemChanged.connect(self.updateParamsFromModel)
        self._poly_model.itemChanged.connect(self.onPolyModelChange)
        # TODO after the poly_model prototype accepted
        #self._magnet_model.itemChanged.connect(self.onMagneticModelChange)

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

        # SasModel -> QModel
        self.SASModelToQModel(model)

        if self.data_is_loaded:
            self.calculateQGridForModel()
        else:
            # Create default datasets if no data passed
            self.createDefaultDataset()

    def onSelectStructureFactor(self):
        """
        Select Structure Factor from list
        """
        model = str(self.cbModel.currentText())
        category = str(self.cbCategory.currentText())
        structure = str(self.cbStructureFactor.currentText())
        if category == CATEGORY_STRUCTURE:
            model = None
        self.SASModelToQModel(model, structure_factor=structure)

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
        models = []
        # Populate the models combobox
        self.cbModel.addItems(sorted([model for (model, _) in model_list]))

    def onSelectSmearing(self):
        """
        Select Smearing type from list
        """
        pass

    def onSmearUp(self):
        """
        Update state based on entered smear value
        """
        pass

    def onSmearDown(self):
        """
        Update state based on entered smear value
        """
        pass

    def onPolyModelChange(self, item):
        """
        Callback method for updating the main model and sasmodel
        parameters with the GUI values in the polydispersity view
        """
        model_column = item.column()
        model_row = item.row()
        name_index = self._poly_model.index(model_row, 0)
        # Extract changed value. Assumes proper validation by QValidator/Delegate
        # Checkbox in column 0
        if model_column == 0:
            value = item.checkState()
        else:
            try:
                value = float(item.text())
            except ValueError:
                # Can't be converted properly, bring back the old value and exit
                return

        parameter_name = str(self._poly_model.data(name_index).toPyObject()) # "distribution of sld" etc.
        if "Distribution of" in parameter_name:
            parameter_name = parameter_name[16:]
        property_name = str(self._poly_model.headerData(model_column, 1).toPyObject()) # Value, min, max, etc.
        # print "%s(%s) => %d" % (parameter_name, property_name, value)

        # Update the sasmodel
        #self.kernel_module.params[parameter_name] = value

        # Reload the main model - may not be required if no variable is shown in main view
        #model = str(self.cbModel.currentText())
        #self.SASModelToQModel(model)

        pass # debug anchor

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

        #disable the Fit button
        self.cmdFit.setText('Calculating...')
        self.communicate.statusBarUpdateSignal.emit('Fitting started...')
        self.cmdFit.setEnabled(False)

    def updateFit(self):
        """
        """
        print "UPDATE FIT"
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
            not numpy.isfinite(res.fitness) or \
            numpy.any(res.pvec == None) or \
            not numpy.all(numpy.isfinite(res.pvec)):
            msg = "Fitting did not converge!!!"
            self.communicate.statusBarUpdateSignal.emit(msg)
            logging.error(msg)
            return

        elapsed = result[1]
        msg = "Fitting completed successfully in: %s s.\n" % GuiUtils.formatNumber(elapsed)
        self.communicate.statusBarUpdateSignal.emit(msg)

        fitness = res.fitness
        param_list = res.param_list
        param_values = res.pvec
        param_stderr = res.stderr
        params_and_errors = zip(param_values, param_stderr)
        param_dict = dict(izip(param_list, params_and_errors))

        # Dictionary of fitted parameter: value, error
        # e.g. param_dic = {"sld":(1.703, 0.0034), "length":(33.455, -0.0983)}
        self.updateModelFromList(param_dict)

        # update charts
        self.onPlot()

        # Read only value - we can get away by just printing it here
        chi2_repr = GuiUtils.formatNumber(fitness, high=True)
        self.lblChi2Value.setText(chi2_repr)

    def iterateOverModel(self, func):
        """
        Take func and throw it inside the model row loop
        """
        #assert isinstance(func, function)
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

        self.iterateOverModel(updateFittedValues)

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

    def onPlot(self):
        """
        Plot the current set of data
        """
        if self.data is None :
            self.createDefaultDataset()
        self.calculateQGridForModel()

    def onNpts(self):
        """
        Callback for number of points line edit update
        """
        # assumes type/value correctness achieved with QValidator
        try:
            self.npts = int(self.txtNpts.text())
        except ValueError:
            # TODO
            # This will return the old value to model/view and return
            # notifying the user about format available.
            pass
        # Force redisplay
        if self.model_is_loaded:
            self.onPlot()

    def onMinRange(self):
        """
        Callback for minimum range of points line edit update
        """
        # assumes type/value correctness achieved with QValidator
        try:
            self.q_range_min = float(self.txtMinRange.text())
        except ValueError:
            # TODO
            # This will return the old value to model/view and return
            # notifying the user about format available.
            return
        # set Q range labels on the main tab
        #self.lblMinRangeDef.setText(str(self.q_range_min))
        if self.model_is_loaded:
            self.onPlot()

    def onMaxRange(self):
        """
        Callback for maximum range of points line edit update
        """
        # assumes type/value correctness achieved with QValidator
        try:
            self.q_range_max = float(self.txtMaxRange.text())
        except:
            pass
        # set Q range labels on the main tab
        self.lblMaxRangeDef.setText(str(self.q_range_max))
        if self.model_is_loaded:
            self.onPlot()

    def onMaskEdit(self):
        """
        Callback for running the mask editor
        """
        pass

    def onReset(self):
        """
        Callback for resetting qmin/qmax
        """
        pass

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
            qmax = self.q_range_max/numpy.sqrt(2)
            qstep = self.npts
            self.logic.createDefault2dData(qmax, qstep, self.tab_id)
        else:
            interval = numpy.linspace(start=self.q_range_min, stop=self.q_range_max,
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

    def addScaleToModel(self, model):
        """
        Adds scale parameter with default values to the model
        """
        assert isinstance(model, QtGui.QStandardItemModel)
        checked_list = ['scale', '1.0', '0.0', 'inf', '']
        FittingUtilities.addCheckedListToModel(model, checked_list)

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
        self.txtMaxRange.setText(str(self.q_range_max))
        self.txtMinRange.setText(str(self.q_range_min))
        self.txtNpts.setText(str(self.npts))
        self.txtNptsFit.setText(str(self.npts))

    def SASModelToQModel(self, model_name, structure_factor=None):
        """
        Setting model parameters into table based on selected category
        """
        # TODO - modify for structure factor-only choice

        # Crete/overwrite model items
        self._model_model.clear()

        kernel_module = generate.load_kernel_module(model_name)
        self.model_parameters = modelinfo.make_parameter_table(getattr(kernel_module, 'parameters', []))

        # Instantiate the current sasmodel
        self.kernel_module = self.models[model_name]()

        # Explicitly add scale and background with default values
        self.addScaleToModel(self._model_model)
        self.addBackgroundToModel(self._model_model)

        # Update the QModel
        new_rows = FittingUtilities.addParametersToModel(self.model_parameters, self.is2D)
        for row in new_rows:
            self._model_model.appendRow(row)
        # Update the counter used for multishell display
        self._last_model_row = self._model_model.rowCount()

        FittingUtilities.addHeadersToModel(self._model_model)

        # Add structure factor
        if structure_factor is not None and structure_factor != "None":
            structure_module = generate.load_kernel_module(structure_factor)
            structure_parameters = modelinfo.make_parameter_table(getattr(structure_module, 'parameters', []))
            new_rows = FittingUtilities.addSimpleParametersToModel(structure_parameters, self.is2D)
            for row in new_rows:
                self._model_model.appendRow(row)
            # Update the counter used for multishell display
            self._last_model_row = self._model_model.rowCount()
        else:
            self.addStructureFactor()

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

        # Update Q Ranges
        self.updateQRange()

    def updateParamsFromModel(self, item):
        """
        Callback method for updating the sasmodel parameters with the GUI values
        """
        model_column = item.column()

        if model_column == 0:
            self.checkboxSelected(item)
            return

        model_row = item.row()
        name_index = self._model_model.index(model_row, 0)

        # Extract changed value. Assumes proper validation by QValidator/Delegate
        value = float(item.text())
        parameter_name = str(self._model_model.data(name_index).toPyObject()) # sld, background etc.
        property_name = str(self._model_model.headerData(1, model_column).toPyObject()) # Value, min, max, etc.

        self.kernel_module.params[parameter_name] = value

        # min/max to be changed in self.kernel_module.details[parameter_name] = ['Ang', 0.0, inf]
        # magnetic params in self.kernel_module.details['M0:parameter_name'] = value
        # multishell params in self.kernel_module.details[??] = value

        # Force the chart update when actual parameters changed
        if model_column == 1:
            self.onPlot()

    def checkboxSelected(self, item):
        # Assure we're dealing with checkboxes
        if not item.isCheckable():
            return
        status = item.checkState()

        def isChecked(row):
            return self._model_model.item(row, 0).checkState() == QtCore.Qt.Checked

        def isCheckable(row):
            return self._model_model.item(row, 0).isCheckable()

        # If multiple rows selected - toggle all of them, filtering uncheckable
        rows = [s.row() for s in self.lstParams.selectionModel().selectedRows() if isCheckable(s.row())]

        # Switch off signaling from the model to avoid recursion
        self._model_model.blockSignals(True)
        # Convert to proper indices and set requested enablement
        items = [self._model_model.item(row, 0).setCheckState(status) for row in rows]
        self._model_model.blockSignals(False)

        # update the list of parameters to fit
        self.parameters_to_fit = [str(self._model_model.item(row_index, 0).text())
                                  for row_index in xrange(self._model_model.rowCount())
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
        if fitted_data.name is None:
            name = self.nameForFittedData(self.logic.data.filename)
            fitted_data.title = name
            fitted_data.name = name
        else:
            name = fitted_data.name
        # Make this a line if no other defined
        if hasattr(fitted_data, 'symbol') and fitted_data.symbol is None:
            fitted_data.symbol = 'Line'
        # Notify the GUI manager so it can update the main model in DataExplorer
        GuiUtils.updateModelItemWithPlot(self._index, QtCore.QVariant(fitted_data), name)

    def createTheoryIndex(self, fitted_data):
        """
        Create a QStandardModelIndex containing model data
        """
        if fitted_data.name is None:
            name = self.nameForFittedData(self.kernel_module.name)
            fitted_data.title = name
            fitted_data.name = name
            fitted_data.filename = name
        else:
            name = fitted_data.name
        # Notify the GUI manager so it can create the theory model in DataExplorer
        new_item = GuiUtils.createModelItemWithPlot(QtCore.QVariant(fitted_data), name=name)
        self.communicate.updateTheoryFromPerspectiveSignal.emit(new_item)

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

    def complete1D(self, return_data):
        """
        Plot the current 1D data
        """
        fitted_plot = self.logic.new1DPlot(return_data, self.tab_id)
        self.calculateResiduals(fitted_plot)

    def complete2D(self, return_data):
        """
        Plot the current 2D data
        """
        fitted_data = self.logic.new2DPlot(return_data)
        self.calculateResiduals(fitted_data)

    def calculateResiduals(self, fitted_data):
        """
        Calculate and print Chi2 and display chart of residuals
        """
        # Create a new index for holding data
        fitted_data.symbol = "Line"
        self.createNewIndex(fitted_data)
        # Calculate difference between return_data and logic.data
        chi2 = FittingUtilities.calculateChi2(fitted_data, self.logic.data)
        # Update the control
        chi2_repr = "---" if chi2 is None else GuiUtils.formatNumber(chi2, high=True)
        self.lblChi2Value.setText(chi2_repr)

        # Plot residuals if actual data
        if self.data_is_loaded:
            residuals_plot = FittingUtilities.plotResiduals(self.data, fitted_data)
            residuals_plot.id = "Residual " + residuals_plot.id
            self.createNewIndex(residuals_plot)
            self.communicate.plotUpdateSignal.emit([residuals_plot])

        self.communicate.plotUpdateSignal.emit([fitted_data])

    def calcException(self, etype, value, tb):
        """
        Something horrible happened in the deferred.
        """
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
        for row, param in enumerate(self.model_parameters.form_volume_parameters):
            # Counters should not be included
            if not param.polydisperse:
                continue

            # Potential multishell params
            checked_list = ["Distribution of "+param.name, str(param.default),
                            str(param.limits[0]), str(param.limits[1]),
                            "35", "3", ""]
            FittingUtilities.addCheckedListToModel(self._poly_model, checked_list)

            #TODO: Need to find cleaner way to input functions
            func = QtGui.QComboBox()
            func.addItems(['rectangle', 'array', 'lognormal', 'gaussian', 'schulz',])
            func_index = self.lstPoly.model().index(row, 6)
            self.lstPoly.setIndexWidget(func_index, func)

        FittingUtilities.addPolyHeadersToModel(self._poly_model)

    def setMagneticModel(self):
        """
        Set magnetism values on model
        """
        if not self.model_parameters:
            return
        self._magnet_model.clear()
        for param in self.model_parameters.call_parameters:
            if param.type != "magnetic":
                continue
            checked_list = [param.name,
                            str(param.default),
                            str(param.limits[0]),
                            str(param.limits[1]),
                            param.units]
            FittingUtilities.addCheckedListToModel(self._magnet_model, checked_list)

        FittingUtilities.addHeadersToModel(self._magnet_model)

    def addStructureFactor(self):
        """
        Add structure factors to the list of parameters
        """
        if self.kernel_module.is_form_factor:
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

