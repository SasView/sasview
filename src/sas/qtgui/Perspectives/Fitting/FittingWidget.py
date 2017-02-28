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

        self.model_is_loaded = False
        self._data = data
        self.is2D = False
        self.modelHasShells = False
        self.data_assigned = False

        self.setupUi(self)

        self.setWindowTitle("Fitting")

        # set the main models
        self._model_model = QtGui.QStandardItemModel()
        self._poly_model = QtGui.QStandardItemModel()
        self._magnet_model = QtGui.QStandardItemModel()

        # Param model displayed in param list
        self.lstParams.setModel(self._model_model)
        self._readCategoryInfo()
        self.model_parameters = None

        # Poly model displayed in poly list
        self.lstPoly.setModel(self._poly_model)
        self.setPolyModel()
        self.setTableProperties(self.lstPoly)

        # Magnetism model displayed in magnetism list
        self.lstMagnetic.setModel(self._magnet_model)
        self.setMagneticModel()
        self.setTableProperties(self.lstMagnetic)

        # Fill in the combo boxes
        structure_factor_list = self.master_category_dict.pop('Structure Factor')
        for (structure_factor, enabled) in structure_factor_list:
            self.cbStructureFactor.addItem(structure_factor)

        category_list = sorted(self.master_category_dict.keys())
        self.cbCategory.addItems(category_list)

        category = self.cbCategory.currentText()
        model_list = self.master_category_dict[str(category)]
        for (model, enabled) in model_list:
            self.cbModel.addItem(model)

        # Connect GUI element signals
        self.cbStructureFactor.currentIndexChanged.connect(self.selectStructureFactor)
        self.cbCategory.currentIndexChanged.connect(self.selectCategory)
        self.cbModel.currentIndexChanged.connect(self.selectModel)
        self.chk2DView.toggled.connect(self.toggle2D)
        self.chkPolydispersity.toggled.connect(self.togglePoly)
        self.chkMagnetism.toggled.connect(self.toggleMagnetism)

        # Set initial control enablement
        self.cmdFit.setEnabled(False)
        self.cmdPlot.setEnabled(True)
        self.chkPolydispersity.setEnabled(True)
        self.chkPolydispersity.setCheckState(False)
        self.chk2DView.setEnabled(True)
        self.chk2DView.setCheckState(False)
        self.chkMagnetism.setEnabled(False)
        self.chkMagnetism.setCheckState(False)

        self.tabFitting.setTabEnabled(TAB_POLY, False)
        self.tabFitting.setTabEnabled(TAB_MAGNETISM, False)

        # set initial labels
        self.lblMinRangeDef.setText("---")
        self.lblMaxRangeDef.setText("---")
        self.lblChi2Value.setText("---")

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

    def selectCategory(self):
        """
        Select Category from list
        :return:
        """
        self.cbModel.clear()
        category = self.cbCategory.currentText()
        model_list = self.master_category_dict[str(category)]
        for (model, enabled) in model_list:
            self.cbModel.addItem(model)

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

    def checkMultiplicity(self, model):
        """
        """
        iter_param = ""
        iter_length = 0
        for param in model.iq_parameters:
            name = param.name
            if "[" in name:
                # pull out the iterator parameter name
                #iter_param = name[name.index('[')+1:-1]
                iter_length = param.length
                iter_param = param.length_control
        return (iter_param, iter_length)
        
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

        #TODO: scaale and background are implicit in sasmodels and needs to be added
        item1 = QtGui.QStandardItem('scale')
        item1.setCheckable(True)
        item2 = QtGui.QStandardItem('1.0')
        item3 = QtGui.QStandardItem('0.0')
        item4 = QtGui.QStandardItem('inf')
        item5 = QtGui.QStandardItem('')
        self._model_model.appendRow([item1, item2, item3, item4, item5])

        item1 = QtGui.QStandardItem('background')
        item1.setCheckable(True)
        item2 = QtGui.QStandardItem('0.001')
        item3 = QtGui.QStandardItem('-inf')
        item4 = QtGui.QStandardItem('inf')
        item5 = QtGui.QStandardItem('1/cm')
        self._model_model.appendRow([item1, item2, item3, item4, item5])

        multishell_param_name, multishell_param_length = self.checkMultiplicity(self.model_parameters)
        multishell_param_fullname = "[%s]" % multishell_param_name
        #TODO: iq_parameters are used here. If orientation paramateres or magnetic are needed
        # kernel_paramters should be used instead
        #For orientation and magentic parameters param.type needs to be checked
        for param in self.model_parameters.iq_parameters:
            # don't include shell parameters
            if param.name == multishell_param_name:
                continue
            # Modify parameter name from <param>[n] to <param>1
            item_name = param.name
            if multishell_param_fullname in param.name:
                item_name = self.replaceShellName(param.name, 1)
            item1 = QtGui.QStandardItem(item_name)
            item1.setCheckable(True)
            item2 = QtGui.QStandardItem(str(param.default))
            item3 = QtGui.QStandardItem(str(param.limits[0]))
            item4 = QtGui.QStandardItem(str(param.limits[1]))
            item5 = QtGui.QStandardItem(param.units)
            self._model_model.appendRow([item1, item2, item3, item4, item5])

        self._model_model.setHeaderData(0, QtCore.Qt.Horizontal, QtCore.QVariant("Parameter"))
        self._model_model.setHeaderData(1, QtCore.Qt.Horizontal, QtCore.QVariant("Value"))
        self._model_model.setHeaderData(2, QtCore.Qt.Horizontal, QtCore.QVariant("Min"))
        self._model_model.setHeaderData(3, QtCore.Qt.Horizontal, QtCore.QVariant("Max"))
        self._model_model.setHeaderData(4, QtCore.Qt.Horizontal, QtCore.QVariant("[Units]"))

        self.addExtraShells()

        self.setPolyModel()
        self.setMagneticModel()
        self.model_is_loaded = True

    def replaceShellName(self, param_name, value):
        """
        Updates parameter name from <param_name>[n_shell] to <param_name>value
        """
        new_name  = param_name[:param_name.index('[')]+str(value)
        return new_name

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
        if self.model_parameters:
            for row, param in enumerate(self.model_parameters.form_volume_parameters):
                item1 = QtGui.QStandardItem("Distribution of "+param.name)
                item1.setCheckable(True)
                item2 = QtGui.QStandardItem("0")
                item3 = QtGui.QStandardItem("")
                item4 = QtGui.QStandardItem("")
                item5 = QtGui.QStandardItem("35")
                item6 = QtGui.QStandardItem("3")
                item7 = QtGui.QStandardItem("")

                self._poly_model.appendRow([item1, item2, item3, item4, item5, item6, item7])

                #TODO: Need to find cleaner way to input functions
                func = QtGui.QComboBox()
                func.addItems(['rectangle','array','lognormal','gaussian','schulz',])
                func_index = self.lstPoly.model().index(row,6)
                self.lstPoly.setIndexWidget(func_index,func)

        self._poly_model.setHeaderData(0, QtCore.Qt.Horizontal, QtCore.QVariant("Parameter"))
        self._poly_model.setHeaderData(1, QtCore.Qt.Horizontal, QtCore.QVariant("PD[ratio]"))
        self._poly_model.setHeaderData(2, QtCore.Qt.Horizontal, QtCore.QVariant("Min"))
        self._poly_model.setHeaderData(3, QtCore.Qt.Horizontal, QtCore.QVariant("Max"))
        self._poly_model.setHeaderData(4, QtCore.Qt.Horizontal, QtCore.QVariant("Npts"))
        self._poly_model.setHeaderData(5, QtCore.Qt.Horizontal, QtCore.QVariant("Nsigs"))
        self._poly_model.setHeaderData(6, QtCore.Qt.Horizontal, QtCore.QVariant("Function"))

    def setMagneticModel(self):
        """
        Set magnetism values on model
        """
        if self.model_parameters:
            for row, param in enumerate(self.model_parameters.form_volume_parameters):
                item1 = QtGui.QStandardItem("Distribution of "+param.name)
                item1.setCheckable(True)
                item2 = QtGui.QStandardItem("0")
                item3 = QtGui.QStandardItem("")
                item4 = QtGui.QStandardItem("")
                item5 = QtGui.QStandardItem("35")
                item6 = QtGui.QStandardItem("3")
                item7 = QtGui.QStandardItem("")

                self._magnet_model.appendRow([item1, item2, item3, item4, item5, item6, item7])

                #TODO: Need to find cleaner way to input functions
                func = QtGui.QComboBox()
                func.addItems(['rectangle','array','lognormal','gaussian','schulz',])
                func_index = self.lstMagnetic.model().index(row,6)
                self.lstMagnetic.setIndexWidget(func_index,func)

        self._magnet_model.setHeaderData(0, QtCore.Qt.Horizontal, QtCore.QVariant("Parameter"))
        self._magnet_model.setHeaderData(1, QtCore.Qt.Horizontal, QtCore.QVariant("PD[ratio]"))
        self._magnet_model.setHeaderData(2, QtCore.Qt.Horizontal, QtCore.QVariant("Min"))
        self._magnet_model.setHeaderData(3, QtCore.Qt.Horizontal, QtCore.QVariant("Max"))
        self._magnet_model.setHeaderData(4, QtCore.Qt.Horizontal, QtCore.QVariant("Npts"))
        self._magnet_model.setHeaderData(5, QtCore.Qt.Horizontal, QtCore.QVariant("Nsigs"))
        self._magnet_model.setHeaderData(6, QtCore.Qt.Horizontal, QtCore.QVariant("Function"))

    def addExtraShells(self):
        """
        Add a combobox for multiple shell display
        """
        param_name, param_length = self.checkMultiplicity(self.model_parameters)

        if param_length == 0:
            return

        item1 = QtGui.QStandardItem(param_name)

        func = QtGui.QComboBox()
        func.addItems([str(i+1) for i in xrange(param_length)])

        item2 = QtGui.QStandardItem()
        self._model_model.appendRow([item1, item2])

        shell_row = self._model_model.rowCount()
        shell_index = self._model_model.index(shell_row-1, 1)
        self.lstParams.setIndexWidget(shell_index, func)
        self.lstParams.setSpan(shell_row-1,2,2,4)

    def togglePoly(self, isChecked):
        """
        """
        self.tabFitting.setTabEnabled(TAB_POLY, isChecked)

    def toggleMagnetism(self, isChecked):
        """
        """
        self.tabFitting.setTabEnabled(TAB_MAGNETISM, isChecked)

    def toggle2D(self, isChecked):
        """
        """
        self.chkMagnetism.setEnabled(isChecked)
        self.is2D = isChecked

