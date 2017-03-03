import sys
import json
import  os
from collections import defaultdict

from PyQt4 import QtGui
from PyQt4 import QtCore

from UI.FittingWidgetUI import Ui_FittingWidgetUI

from sasmodels import generate
from sasmodels import modelinfo
from sas.sasgui.guiframe.CategoryInstaller import CategoryInstaller

TAB_MAGNETISM = 4
TAB_POLY = 3
CATEGORY_DEFAULT="Choose category..."

class FittingWidget(QtGui.QWidget, Ui_FittingWidgetUI):
    """
    Main widget for selecting form and structure factor models
    """
    def __init__(self, manager=None, parent=None, data=None):
        """

        :param manager:
        :param parent:
        :return:
        """
        super(FittingWidget, self).__init__()

        # Necessary globals
        self.model_is_loaded = False
        self._data = data
        self.is2D = False
        self.model_has_shells = False
        self.data_assigned = False
        self._previous_category_index = 0
        self._last_model_row = 0

        # Main GUI setup up
        self.setupUi(self)
        self.setWindowTitle("Fitting")

        # Set the main models
        self._model_model = QtGui.QStandardItemModel()
        self._poly_model = QtGui.QStandardItemModel()
        self._magnet_model = QtGui.QStandardItemModel()
        # Proxy model for custom views on the main _model_model
        self.proxyModel = QtGui.QSortFilterProxyModel()

        # Param model displayed in param list
        self.lstParams.setModel(self._model_model)
        self._readCategoryInfo()
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

        # Defaults for the strcutre factors
        self.setDefaultStructureCombo()

        # make structure factor and model CBs disabled
        self.disableModelCombo()
        self.disableStructureCombo()

        # Generate the category list for display
        category_list = sorted(self.master_category_dict.keys())
        self.cbCategory.addItem(CATEGORY_DEFAULT)
        self.cbCategory.addItems(category_list)
        self.cbCategory.addItem("Structure Factor")
        self.cbCategory.setCurrentIndex(0)

        # Connect signals to controls
        self.initializeSignals()

        # Initial control state
        self.initializeControls()

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        """ data setter """
        self._data = value
        self.data_assigned = True
        # TODO: update ranges, chi2 etc

    def acceptsData(self):
        """ Tells the caller this widget can accept new dataset """
        return not self.data_assigned

    def disableModelCombo(self):
        self.cbModel.setEnabled(False)
        self.label_3.setEnabled(False)

    def enableModelCombo(self):
        self.cbModel.setEnabled(True)
        self.label_3.setEnabled(True)

    def disableStructureCombo(self):
        self.cbStructureFactor.setEnabled(False)
        self.label_4.setEnabled(False)

    def enableStructureCombo(self):
        self.cbStructureFactor.setEnabled(True)
        self.label_4.setEnabled(True)

    def initializeControls(self):
        """
        Set initial control enablement
        """
        self.cmdFit.setEnabled(False)
        self.cmdPlot.setEnabled(True)
        self.chkPolydispersity.setEnabled(True)
        self.chkPolydispersity.setCheckState(False)
        self.chk2DView.setEnabled(True)
        self.chk2DView.setCheckState(False)
        self.chkMagnetism.setEnabled(False)
        self.chkMagnetism.setCheckState(False)
        # tabs
        self.tabFitting.setTabEnabled(TAB_POLY, False)
        self.tabFitting.setTabEnabled(TAB_MAGNETISM, False)
        # set initial labels
        self.lblMinRangeDef.setText("---")
        self.lblMaxRangeDef.setText("---")
        self.lblChi2Value.setText("---")

    def initializeSignals(self):
        """
        Connect GUI element signals
        """
        self.cbStructureFactor.currentIndexChanged.connect(self.selectStructureFactor)
        self.cbCategory.currentIndexChanged.connect(self.selectCategory)
        self.cbModel.currentIndexChanged.connect(self.selectModel)
        self.chk2DView.toggled.connect(self.toggle2D)
        self.chkPolydispersity.toggled.connect(self.togglePoly)
        self.chkMagnetism.toggled.connect(self.toggleMagnetism)

    def setDefaultStructureCombo(self):
        # Fill in the structure factors combo box with defaults
        structure_factor_list = self.master_category_dict.pop('Structure Factor')
        structure_factors = []
        self.cbStructureFactor.clear()
        for (structure_factor, _) in structure_factor_list:
            structure_factors.append(structure_factor)
        self.cbStructureFactor.addItems(sorted(structure_factors))

    def selectCategory(self):
        """
        Select Category from list
        :return:
        """
        category = self.cbCategory.currentText()
        # Check if the user chose "Choose category entry"
        if str(category) == CATEGORY_DEFAULT:
            # if the previous category was not the default, keep it.
            # Otherwise, just return
            if self._previous_category_index != 0:
                self.cbCategory.setCurrentIndex(self._previous_category_index)
            return

        if category == "Structure Factor":
            self.disableModelCombo()
            self.enableStructureCombo()
            return

        self.cbModel.blockSignals(True)
        self.cbModel.clear()
        self.cbModel.blockSignals(False)
        self.enableModelCombo()
        self.disableStructureCombo()

        self._previous_category_index = self.cbCategory.currentIndex()
        model_list = self.master_category_dict[str(category)]
        models = []
        for (model, _) in model_list:
            models.append(model)
        self.cbModel.addItems(sorted(models))

    def selectModel(self):
        """
        Select Model from list
        :return:
        """
        model = self.cbModel.currentText()
        self.setModelModel(model)

    def selectStructureFactor(self):
        """
        Select Structure Factor from list
        :param:
        :return:
        """
        model = self.cbStructureFactor.currentText()
        self.setModelModel(model)

    def _readCategoryInfo(self):
        """
        Reads the categories in from file
        """
        self.master_category_dict = defaultdict(list)
        self.by_model_dict = defaultdict(list)
        self.model_enabled_dict = defaultdict(bool)

        try:
            categorization_file = CategoryInstaller.get_user_file()
            if not os.path.isfile(categorization_file):
                categorization_file = CategoryInstaller.get_default_file()
            cat_file = open(categorization_file, 'rb')
            self.master_category_dict = json.load(cat_file)
            self._regenerate_model_dict()
            cat_file.close()
        except IOError:
            raise
            print 'Problem reading in category file.'
            print 'We even looked for it, made sure it was there.'
            print 'An existential crisis if there ever was one.'

    def _regenerate_model_dict(self):
        """
        regenerates self.by_model_dict which has each model name as the
        key and the list of categories belonging to that model
        along with the enabled mapping
        """
        self.by_model_dict = defaultdict(list)
        for category in self.master_category_dict:
            for (model, enabled) in self.master_category_dict[category]:
                self.by_model_dict[model].append(category)
                self.model_enabled_dict[model] = enabled

    def getIterParams(self, model):
        """
        Returns a list of all multi-shell parameters in 'model'
        """
        iter_params = list(filter(lambda par: "[" in par.name, model.iq_parameters))

        return iter_params

    def getMultiplicity(self, model):
        """
        Finds out if 'model' has multishell parameters.
        If so, returns the name of the counter parameter and the number of shells
        """
        iter_param = ""
        iter_length = 0

        iter_params = self.getIterParams(model)
        # pull out the iterator parameter name and length
        if iter_params:
            iter_length = iter_params[0].length
            iter_param = iter_params[0].length_control
        return (iter_param, iter_length)

    def addBackgroundToModel(self, model):
        """
        Adds background parameter with default values to the model
        """
        assert(isinstance(model, QtGui.QStandardItemModel))

        checked_list = ['background', '0.001', '-inf', 'inf', '1/cm']
        self.addCheckedListToModel(model, checked_list)

    def addScaleToModel(self, model):
        """
        Adds scale parameter with default values to the model
        """
        assert(isinstance(model, QtGui.QStandardItemModel))

        checked_list = ['scale', '1.0', '0.0', 'inf', '']
        self.addCheckedListToModel(model, checked_list)

    def addCheckedListToModel(self, model, param_list):
        assert(isinstance(model, QtGui.QStandardItemModel))
        item_list = [QtGui.QStandardItem(item) for item in param_list]
        item_list[0].setCheckable(True)
        model.appendRow(item_list)

    def addHeadersToModel(self, model):
        """
        Adds predefined headers to the model
        """
        model.setHeaderData(0, QtCore.Qt.Horizontal, QtCore.QVariant("Parameter"))
        model.setHeaderData(1, QtCore.Qt.Horizontal, QtCore.QVariant("Value"))
        model.setHeaderData(2, QtCore.Qt.Horizontal, QtCore.QVariant("Min"))
        model.setHeaderData(3, QtCore.Qt.Horizontal, QtCore.QVariant("Max"))
        model.setHeaderData(4, QtCore.Qt.Horizontal, QtCore.QVariant("[Units]"))

    def addPolyHeadersToModel(self, model):
        """
        Adds predefined headers to the model
        """
        model.setHeaderData(0, QtCore.Qt.Horizontal, QtCore.QVariant("Parameter"))
        model.setHeaderData(1, QtCore.Qt.Horizontal, QtCore.QVariant("PD[ratio]"))
        model.setHeaderData(2, QtCore.Qt.Horizontal, QtCore.QVariant("Min"))
        model.setHeaderData(3, QtCore.Qt.Horizontal, QtCore.QVariant("Max"))
        model.setHeaderData(4, QtCore.Qt.Horizontal, QtCore.QVariant("Npts"))
        model.setHeaderData(5, QtCore.Qt.Horizontal, QtCore.QVariant("Nsigs"))
        model.setHeaderData(6, QtCore.Qt.Horizontal, QtCore.QVariant("Function"))

    def setModelModel(self, model_name):
        """
        Setting model parameters into table based on selected
        :param model_name:
        :return:
        """
        # Crete/overwrite model items
        self._model_model.clear()
        model_name = str(model_name)
        kernel_module = generate.load_kernel_module(model_name)
        self.model_parameters = modelinfo.make_parameter_table(getattr(kernel_module, 'parameters', []))

        #TODO: scale and background are implicit in sasmodels and needs to be added
        self.addScaleToModel(self._model_model)
        self.addBackgroundToModel(self._model_model)

        self.addParametersToModel(self.model_parameters, self._model_model)

        self.addHeadersToModel(self._model_model)

        self.addExtraShells()

        self.setPolyModel()
        self.setMagneticModel()
        self.model_is_loaded = True

    def addParametersToModel(self, parameters, model):
        """
        Update local ModelModel with sasmodel parameters
        """
        multishell_parameters = self.getIterParams(parameters)
        multishell_param_name, _ = self.getMultiplicity(parameters)

        #TODO: iq_parameters are used here. If orientation paramateres or magnetic are needed
        # kernel_paramters should be used instead
        for param in parameters.iq_parameters:
            # don't include shell parameters
            if param.name == multishell_param_name:
                continue
            # Modify parameter name from <param>[n] to <param>1
            item_name = param.name
            if param in multishell_parameters:
                item_name = self.replaceShellName(param.name, 1)

            item1 = QtGui.QStandardItem(item_name)
            item1.setCheckable(True)
            # check for polydisp params
            if param.polydisperse:
                poly_item = QtGui.QStandardItem("Polydispersity")
                item1_1 = QtGui.QStandardItem("Distribution")
                # Find param in volume_params
                for p in parameters.form_volume_parameters:
                    if p.name == param.name:
                        item1_2 = QtGui.QStandardItem(str(p.default))
                        item1_3 = QtGui.QStandardItem(str(p.limits[0]))
                        item1_4 = QtGui.QStandardItem(str(p.limits[1]))
                        item1_5 = QtGui.QStandardItem(p.units)
                        poly_item.appendRow([item1_1, item1_2, item1_3, item1_4, item1_5])
                        break

                item1.appendRow([poly_item])

            item2 = QtGui.QStandardItem(str(param.default))
            item3 = QtGui.QStandardItem(str(param.limits[0]))
            item4 = QtGui.QStandardItem(str(param.limits[1]))
            item5 = QtGui.QStandardItem(param.units)
            model.appendRow([item1, item2, item3, item4, item5])

        self._last_model_row = self._model_model.rowCount()

    def modelToFittingParameters(self):
        """
        Prepare the fitting data object, based on current ModelModel
        """
        pass

    def replaceShellName(self, param_name, value):
        """
        Updates parameter name from <param_name>[n_shell] to <param_name>value
        """
        assert('[' in param_name)
        return param_name[:param_name.index('[')]+str(value)

    def setTableProperties(self, table):
        """
        Setting table properties
        :param table:
        :return:
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
        header.setResizeMode(0, QtGui.QHeaderView.ResizeToContents)
        header.setResizeMode(6, QtGui.QHeaderView.ResizeToContents)

    def setPolyModel(self):
        """
        Set polydispersity values
        """
        ### TODO: apply proper proxy model filtering from the main _model_model

        if not self.model_parameters:
            return
        self._poly_model.clear()
        for row, param in enumerate(self.model_parameters.form_volume_parameters):
            # Counters should not be included
            if not param.polydisperse:
                continue

            # Potential multishell params
            #length_control = param.length_control
            #if length_control in param.name:

            checked_list = ["Distribution of "+param.name, str(param.default),
                            str(param.limits[0]),str(param.limits[1]),
                            "35", "3", ""]
            self.addCheckedListToModel(self._poly_model, checked_list)

            #TODO: Need to find cleaner way to input functions
            func = QtGui.QComboBox()
            func.addItems(['rectangle','array','lognormal','gaussian','schulz',])
            func_index = self.lstPoly.model().index(row,6)
            self.lstPoly.setIndexWidget(func_index,func)

        self.addPolyHeadersToModel(self._poly_model)

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
            self.addCheckedListToModel(self._magnet_model, checked_list)

        self.addHeadersToModel(self._magnet_model)

    def addExtraShells(self):
        """
        Add a combobox for multiple shell display
        """
        param_name, param_length = self.getMultiplicity(self.model_parameters)

        if param_length == 0:
            return

        # cell 1: variable name
        item1 = QtGui.QStandardItem(param_name)

        func = QtGui.QComboBox()
        func.addItems([str(i+1) for i in xrange(param_length)])
        func.currentIndexChanged.connect(self.modifyShellsInList)

        # cell 2: combobox
        item2 = QtGui.QStandardItem()
        self._model_model.appendRow([item1, item2])

        # Beautify the row:  span columns 2-4
        shell_row = self._model_model.rowCount()
        shell_index = self._model_model.index(shell_row-1, 1)
        self.lstParams.setIndexWidget(shell_index, func)

        self._last_model_row = self._model_model.rowCount()


    def modifyShellsInList(self, index):
        """
        Add/remove additional multishell parameters
        """
        # Find row location of the combobox
        last_row = self._last_model_row
        remove_rows = self._model_model.rowCount() - last_row

        if remove_rows > 1:
            self._model_model.removeRows(last_row, remove_rows)

        multishell_parameters = self.getIterParams(self.model_parameters)

        for i in xrange(index):
            for par in multishell_parameters:
                param_name = self.replaceShellName(par.name, i+2)
                #param_name = str(p.name) + str(i+2)
                item1 = QtGui.QStandardItem(param_name)
                item1.setCheckable(True)
                # check for polydisp params
                if par.polydisperse:
                    poly_item = QtGui.QStandardItem("Polydispersity")
                    item1_1 = QtGui.QStandardItem("Distribution")
                    # Find param in volume_params
                    for p in self.model_parameters.form_volume_parameters:
                        if p.name == par.name:
                            item1_2 = QtGui.QStandardItem(str(p.default))
                            item1_3 = QtGui.QStandardItem(str(p.limits[0]))
                            item1_4 = QtGui.QStandardItem(str(p.limits[1]))
                            item1_5 = QtGui.QStandardItem(p.units)
                            poly_item.appendRow([item1_1, item1_2, item1_3, item1_4, item1_5])
                            break
                    item1.appendRow([poly_item])

                item2 = QtGui.QStandardItem(str(par.default))
                item3 = QtGui.QStandardItem(str(par.limits[0]))
                item4 = QtGui.QStandardItem(str(par.limits[1]))
                item5 = QtGui.QStandardItem(par.units)
                self._model_model.appendRow([item1, item2, item3, item4, item5])

    def togglePoly(self, isChecked):
        """
        Enable/disable the polydispersity tab
        """
        self.tabFitting.setTabEnabled(TAB_POLY, isChecked)

    def toggleMagnetism(self, isChecked):
        """
        Enable/disable the magnetism tab
        """
        self.tabFitting.setTabEnabled(TAB_MAGNETISM, isChecked)

    def toggle2D(self, isChecked):
        """
        Enable/disable the controls dependent on 1D/2D data instance
        """
        self.chkMagnetism.setEnabled(isChecked)
        self.is2D = isChecked

