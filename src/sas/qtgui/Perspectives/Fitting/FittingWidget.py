import sys
import json
import os
import numpy
from collections import defaultdict

import logging
import traceback
from twisted.internet import threads

from PyQt4 import QtGui
from PyQt4 import QtCore

from sasmodels import generate
from sasmodels import modelinfo
from sasmodels.sasview_model import load_standard_models

from sas.sasgui.guiframe.CategoryInstaller import CategoryInstaller
from sas.sasgui.guiframe.dataFitting import Data1D
from sas.sasgui.guiframe.dataFitting import Data2D
import sas.qtgui.GuiUtils as GuiUtils
from sas.sascalc.dataloader.data_info import Detector
from sas.sascalc.dataloader.data_info import Source
from sas.sasgui.perspectives.fitting.model_thread import Calc1D
from sas.sasgui.perspectives.fitting.model_thread import Calc2D

from UI.FittingWidgetUI import Ui_FittingWidgetUI

TAB_MAGNETISM = 4
TAB_POLY = 3
CATEGORY_DEFAULT = "Choose category..."
QMIN_DEFAULT = 0.0005
QMAX_DEFAULT = 0.5
NPTS_DEFAULT = 50

class FittingWidget(QtGui.QWidget, Ui_FittingWidgetUI):
    """
    Main widget for selecting form and structure factor models
    """
    def __init__(self, manager=None, parent=None, data=None, id=1):
        """

        :param manager:
        :param parent:
        :return:
        """
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

        # Which tab is this widget displayed in?
        self.tab_id = id

        # Parameters
        self.q_range_min = QMIN_DEFAULT
        self.q_range_max = QMAX_DEFAULT
        self.npts = NPTS_DEFAULT
        # Main Data[12]D holder
        self._data = None

        # Main GUI setup up
        self.setupUi(self)
        self.setWindowTitle("Fitting")
        self.communicate = self.parent.communicate

        # Set the main models
        # We can't use a single model here, due to restrictions on flattening
        # the model tree with subclassed QAbstractProxyModel...
        self._model_model = QtGui.QStandardItemModel()
        self._poly_model = QtGui.QStandardItemModel()
        self._magnet_model = QtGui.QStandardItemModel()

        # Set the proxy models for display
        #   Main display
        self._model_proxy = QtGui.QSortFilterProxyModel()
        self._model_proxy.setSourceModel(self._model_model)
        #self._model_proxy.setFilterRegExp(r"[^()]")

        #   Proxy display
        self._poly_proxy = QtGui.QSortFilterProxyModel()
        self._poly_proxy.setSourceModel(self._poly_model)
        self._poly_proxy.setFilterRegExp(r"[^()]")

        #   Magnetism display
        self._magnet_proxy = QtGui.QSortFilterProxyModel()
        self._magnet_proxy.setSourceModel(self._magnet_model)
        #self._magnet_proxy.setFilterRegExp(r"[^()]")

        # Param model displayed in param list
        self.lstParams.setModel(self._model_model)
        #self.lstParams.setModel(self._model_proxy)
        self.readCategoryInfo()
        self.model_parameters = None
        self.lstParams.setAlternatingRowColors(True)

        # Poly model displayed in poly list
        self.lstPoly.setModel(self._poly_proxy)
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
        self.cbCategory.addItem("Structure Factor")
        self.cbCategory.setCurrentIndex(0)

        self._index = data
        if data is not None:
            self.data = data

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
        # _index contains the QIndex with data
        self._index = value
        # _data contains the actual Data[12]D
        self._data = GuiUtils.dataFromItem(value[0])
        self.data_is_loaded = True
        # Tag along functionality
        self.updateQRange()
        self.cmdFit.setEnabled(True)

    def acceptsData(self):
        """ Tells the caller this widget can accept new dataset """
        return not self.data_is_loaded

    def disableModelCombo(self):
        """ Disable the combobox """
        self.cbModel.setEnabled(False)
        self.label_3.setEnabled(False)

    def enableModelCombo(self):
        """ Enable the combobox """
        self.cbModel.setEnabled(True)
        self.label_3.setEnabled(True)

    def disableStructureCombo(self):
        """ Disable the combobox """
        self.cbStructureFactor.setEnabled(False)
        self.label_4.setEnabled(False)

    def enableStructureCombo(self):
        """ Enable the combobox """
        self.cbStructureFactor.setEnabled(True)
        self.label_4.setEnabled(True)

    def updateQRange(self):
        """
        Updates Q Range display
        """
        if self.data_is_loaded:
            self.q_range_min, self.q_range_max, self.npts = self.computeDataRange(self.data)
        # set Q range labels on the main tab
        self.lblMinRangeDef.setText(str(self.q_range_min))
        self.lblMaxRangeDef.setText(str(self.q_range_max))
        # set Q range labels on the options tab
        self.txtMaxRange.setText(str(self.q_range_max))
        self.txtMinRange.setText(str(self.q_range_min))
        self.txtNpts.setText(str(self.npts))

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
        # Tabs
        self.tabFitting.setTabEnabled(TAB_POLY, False)
        self.tabFitting.setTabEnabled(TAB_MAGNETISM, False)
        self.lblChi2Value.setText("---")
        # Update Q Ranges
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
        # Line edits
        self.txtNpts.textChanged.connect(self.onNpts)
        self.txtMinRange.textChanged.connect(self.onMinRange)
        self.txtMaxRange.textChanged.connect(self.onMaxRange)

        # Respond to change in parameters from the UI
        self._model_model.itemChanged.connect(self.updateParamsFromModel)
        self._poly_model.itemChanged.connect(self.onPolyModelChange)
        # TODO after the poly_model prototype accepted
        #self._magnet_model.itemChanged.connect(self.onMagneticModelChange)

    def setDefaultStructureCombo(self):
        """
        Fill in the structure factors combo box with defaults
        """
        structure_factor_list = self.master_category_dict.pop('Structure Factor')
        structure_factors = ["None"]
        self.cbStructureFactor.clear()
        for (structure_factor, _) in structure_factor_list:
            structure_factors.append(structure_factor)
        self.cbStructureFactor.addItems(sorted(structure_factors))

    def onSelectCategory(self):
        """
        Select Category from list
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

        # Safely clear and enable the model combo
        self.cbModel.blockSignals(True)
        self.cbModel.clear()
        self.cbModel.blockSignals(False)
        self.enableModelCombo()
        self.disableStructureCombo()

        self._previous_category_index = self.cbCategory.currentIndex()
        # Retrieve the list of models
        model_list = self.master_category_dict[str(category)]
        models = []
        # Populate the models combobox
        for (model, _) in model_list:
            models.append(model)
        self.cbModel.addItems(sorted(models))

    def onSelectModel(self):
        """
        Respond to select Model from list event
        """
        model = str(self.cbModel.currentText())

        # SasModel -> QModel
        self.setModelModel(model)

        if self._index is None:
            # Create default datasets if no data passed
            if self.is2D:
                self.createDefault2dData()
            else:
                self.createDefault1dData()
            # DESIGN: create the theory now or on Plot event?
            #self.createTheoryIndex()
        else:
            # Create datasets and errorbars for current data
            if self.is2D:
                self.calculate2DForModel()
            else:
                self.calculate1DForModel()
            # TODO: attach the chart to index

    def onSelectStructureFactor(self):
        """
        Select Structure Factor from list
        """
        model = str(self.cbModel.currentText())
        structure = str(self.cbStructureFactor.currentText())
        self.setModelModel(model, structure_factor=structure)

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

    def getIterParams(self, model):
        """
        Returns a list of all multi-shell parameters in 'model'
        """
        return list(filter(lambda par: "[" in par.name, model.iq_parameters))

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
        assert isinstance(model, QtGui.QStandardItemModel)
        checked_list = ['background', '0.001', '-inf', 'inf', '1/cm']
        self.addCheckedListToModel(model, checked_list)

    def addScaleToModel(self, model):
        """
        Adds scale parameter with default values to the model
        """
        assert isinstance(model, QtGui.QStandardItemModel)
        checked_list = ['scale', '1.0', '0.0', 'inf', '']
        self.addCheckedListToModel(model, checked_list)

    def addCheckedListToModel(self, model, param_list):
        assert isinstance(model, QtGui.QStandardItemModel)
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

    def setModelModel(self, model_name, structure_factor=None):
        """
        Setting model parameters into table based on selected category
        """
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
        self.addParametersToModel(self.model_parameters, self._model_model)
        self.addHeadersToModel(self._model_model)

        # Add structure factor
        if structure_factor is not None and structure_factor != "None":
            structure_module = generate.load_kernel_module(structure_factor)
            structure_parameters = modelinfo.make_parameter_table(getattr(structure_module, 'parameters', []))
            self.addSimpleParametersToModel(structure_parameters, self._model_model)
        else:
            self.addStructureFactor()

        # Multishell models need additional treatment
        self.addExtraShells()

        # Add polydispersity to the model
        self.setPolyModel()
        # Add magnetic parameters to the model
        self.setMagneticModel()

        # Now we claim the model has been loaded
        self.model_is_loaded = True

        # Update Q Ranges
        self.updateQRange()

    def onPolyModelChange(self, item):
        """
        Callback method for updating the main model and sasmodel
        parameters with the GUI values in the polydispersity view
        """
        model_column = item.column()
        model_row = item.row()
        name_index = self._poly_model.index(model_row, 0)
        # Extract changed value. Assumes proper validation by QValidator/Delegate
        value = float(item.text())
        parameter_name = str(self._poly_model.data(name_index).toPyObject()) # "distribution of sld" etc.
        if "Distribution of" in parameter_name:
            parameter_name = parameter_name[16:]
        property_name = str(self._poly_model.headerData(model_column, 1).toPyObject()) # Value, min, max, etc.
        print "%s(%s) => %d" % (parameter_name, property_name, value)

        # Update the sasmodel
        #self.kernel_module.params[parameter_name] = value

        # Reload the main model - may not be required if no variable is shown in main view
        #model = str(self.cbModel.currentText())
        #self.setModelModel(model)

        pass # debug anchor

    def updateParamsFromModel(self, item):
        """
        Callback method for updating the sasmodel parameters with the GUI values
        """
        model_column = item.column()
        model_row = item.row()
        name_index = self._model_model.index(model_row, 0)

        if model_column == 0:
            # Assure we're dealing with checkboxes
            if not item.isCheckable():
                return
            status = item.checkState()
            # If multiple rows selected - toggle all of them
            rows = [s.row() for s in self.lstParams.selectionModel().selectedRows()]

            # Switch off signaling from the model to avoid multiple calls
            self._model_model.blockSignals(True)
            # Convert to proper indices and set requested enablement
            items = [self._model_model.item(row, 0).setCheckState(status) for row in rows]
            self._model_model.blockSignals(False)
            return

        # Extract changed value. Assumes proper validation by QValidator/Delegate
        value = float(item.text())
        parameter_name = str(self._model_model.data(name_index).toPyObject()) # sld, background etc.
        property_name = str(self._model_model.headerData(1, model_column).toPyObject()) # Value, min, max, etc.

        print "%s(%s) => %d" % (parameter_name, property_name, value)
        self.kernel_module.params[parameter_name] = value

        # min/max to be changed in self.kernel_module.details[parameter_name] = ['Ang', 0.0, inf]

        # magnetic params in self.kernel_module.details['M0:parameter_name'] = value
        # multishell params in self.kernel_module.details[??] = value

    def computeDataRange(self, data):
        """
        Compute the minimum and the maximum range of the data
        return the npts contains in data
        """
        assert data is not None
        assert (isinstance(data, Data1D) or isinstance(data, Data2D))
        qmin, qmax, npts = None, None, None
        if isinstance(data, Data1D):
            try:
                qmin = min(data.x)
                qmax = max(data.x)
                npts = len(data.x)
            except (ValueError, TypeError):
                msg = "Unable to find min/max/length of \n data named %s" % \
                            data.filename
                raise ValueError, msg

        else:
            qmin = 0
            try:
                x = max(numpy.fabs(data.xmin), numpy.fabs(data.xmax))
                y = max(numpy.fabs(data.ymin), numpy.fabs(data.ymax))
            except (ValueError, TypeError):
                msg = "Unable to find min/max of \n data named %s" % \
                            data.filename
                raise ValueError, msg
            qmax = numpy.sqrt(x * x + y * y)
            npts = len(data.data)
        return qmin, qmax, npts

    def addParametersToModel(self, parameters, model):
        """
        Update local ModelModel with sasmodel parameters
        """
        multishell_parameters = self.getIterParams(parameters)
        multishell_param_name, _ = self.getMultiplicity(parameters)

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
                    if p.name != param.name:
                        continue
                    item1_2 = QtGui.QStandardItem(str(p.default))
                    item1_3 = QtGui.QStandardItem(str(p.limits[0]))
                    item1_4 = QtGui.QStandardItem(str(p.limits[1]))
                    item1_5 = QtGui.QStandardItem(p.units)
                    poly_item.appendRow([item1_1, item1_2, item1_3, item1_4, item1_5])
                    break
                # Add the polydisp item as a child
                item1.appendRow([poly_item])
            # Param values
            item2 = QtGui.QStandardItem(str(param.default))
            # TODO: the error column.
            # Either add a proxy model or a custom view delegate
            #item_err = QtGui.QStandardItem()
            item3 = QtGui.QStandardItem(str(param.limits[0]))
            item4 = QtGui.QStandardItem(str(param.limits[1]))
            item5 = QtGui.QStandardItem(param.units)
            model.appendRow([item1, item2, item3, item4, item5])

        # Update the counter used for multishell display
        self._last_model_row = self._model_model.rowCount()

    def addSimpleParametersToModel(self, parameters, model):
        """
        Update local ModelModel with sasmodel parameters
        """
        for param in parameters.iq_parameters:
            # Modify parameter name from <param>[n] to <param>1
            item_name = param.name
            item1 = QtGui.QStandardItem(item_name)
            item1.setCheckable(True)
            # Param values
            item2 = QtGui.QStandardItem(str(param.default))
            # TODO: the error column.
            # Either add a proxy model or a custom view delegate
            #item_err = QtGui.QStandardItem()
            item3 = QtGui.QStandardItem(str(param.limits[0]))
            item4 = QtGui.QStandardItem(str(param.limits[1]))
            item5 = QtGui.QStandardItem(param.units)
            model.appendRow([item1, item2, item3, item4, item5])

        # Update the counter used for multishell display
        self._last_model_row = self._model_model.rowCount()

    def createDefault1dData(self):
        """
        Create default data for fitting perspective
        Only when the page is on theory mode.
        """
        x = numpy.linspace(start=self.q_range_min, stop=self.q_range_max,
                           num=self.npts, endpoint=True)
        self._data = Data1D(x=x)
        self._data.xaxis('\\rm{Q}', "A^{-1}")
        self._data.yaxis('\\rm{Intensity}', "cm^{-1}")
        self._data.is_data = False
        self._data.id = str(self.tab_id) + " data"
        self._data.group_id = str(self.tab_id) + " Model1D"

    def createDefault2dData(self):
        """
        Create 2D data by default
        Only when the page is on theory mode.
        """
        self._data = Data2D()
        qmax = self.q_range_max / numpy.sqrt(2)
        self._data.xaxis('\\rm{Q_{x}}', 'A^{-1}')
        self._data.yaxis('\\rm{Q_{y}}', 'A^{-1}')
        self._data.is_data = False
        self._data.id = str(self.tab_id) + " data"
        self._data.group_id = str(self.tab_id) + " Model2D"

        # Default detector
        self._data.detector.append(Detector())
        index = len(self._data.detector) - 1
        self._data.detector[index].distance = 8000   # mm
        self._data.source.wavelength = 6             # A
        self._data.detector[index].pixel_size.x = 5  # mm
        self._data.detector[index].pixel_size.y = 5  # mm
        self._data.detector[index].beam_center.x = qmax
        self._data.detector[index].beam_center.y = qmax
        # theory default: assume the beam
        #center is located at the center of sqr detector
        xmax = qmax
        xmin = -qmax
        ymax = qmax
        ymin = -qmax
        qstep = self.npts

        x = numpy.linspace(start=xmin, stop=xmax, num=qstep, endpoint=True)
        y = numpy.linspace(start=ymin, stop=ymax, num=qstep, endpoint=True)
        # Use data info instead
        new_x = numpy.tile(x, (len(y), 1))
        new_y = numpy.tile(y, (len(x), 1))
        new_y = new_y.swapaxes(0, 1)

        # all data required in 1d array
        qx_data = new_x.flatten()
        qy_data = new_y.flatten()
        q_data = numpy.sqrt(qx_data * qx_data + qy_data * qy_data)

        # set all True (standing for unmasked) as default
        mask = numpy.ones(len(qx_data), dtype=bool)
        # calculate the range of qx and qy: this way,
        # it is a little more independent
        # store x and y bin centers in q space
        x_bins = x
        y_bins = y

        self._data.source = Source()
        self._data.data = numpy.ones(len(mask))
        self._data.err_data = numpy.ones(len(mask))
        self._data.qx_data = qx_data
        self._data.qy_data = qy_data
        self._data.q_data = q_data
        self._data.mask = mask
        self._data.x_bins = x_bins
        self._data.y_bins = y_bins
        # max and min taking account of the bin sizes
        self._data.xmin = xmin
        self._data.xmax = xmax
        self._data.ymin = ymin
        self._data.ymax = ymax

    def createTheoryIndex(self):
        """
        Create a QStandardModelIndex containing default model data
        """
        name = self.kernel_module.name
        if self.is2D:
            name += "2d"
        name = "M%i [%s]" % (self.tab_id, name)
        new_item = GuiUtils.createModelItemWithPlot(QtCore.QVariant(self.data), name=name)
        # Notify the GUI manager so it can update the theory model in DataExplorer
        self.communicate.updateTheoryFromPerspectiveSignal.emit(new_item)

    def onFit(self):
        """
        Perform fitting on the current data
        """
        #self.calculate1DForModel()
        pass

    def onPlot(self):
        """
        Plot the current set of data
        """
        # TODO: reimplement basepage.py/_update_paramv_on_fit
        if self.data is None or not self._data.is_data:
            self.createDefault2dData() if self.is2D else self.createDefault1dData()
        self.calculate2DForModel() if self.is2D else self.calculate1DForModel()

    def onNpts(self, text):
        """
        Callback for number of points line edit update
        """
        # assumes type/value correctness achieved with QValidator
        try:
            self.npts = int(text)
        except:
            pass

    def onMinRange(self, text):
        """
        Callback for minimum range of points line edit update
        """
        # assumes type/value correctness achieved with QValidator
        try:
            self.q_range_min = float(text)
        except:
            pass
        # set Q range labels on the main tab
        self.lblMinRangeDef.setText(str(self.q_range_min))

    def onMaxRange(self, text):
        """
        Callback for maximum range of points line edit update
        """
        # assumes type/value correctness achieved with QValidator
        try:
            self.q_range_max = float(text)
        except:
            pass
        # set Q range labels on the main tab
        self.lblMaxRangeDef.setText(str(self.q_range_max))

    def calculate1DForModel(self):
        """
        Prepare the fitting data object, based on current ModelModel
        """
        self.calc_1D = Calc1D(data=self.data,
                              model=self.kernel_module,
                              page_id=0,
                              qmin=self.q_range_min,
                              qmax=self.q_range_max,
                              smearer=None,
                              state=None,
                              weight=None,
                              fid=None,
                              toggle_mode_on=False,
                              completefn=self.complete1D,
                              update_chisqr=True,
                              exception_handler=self.calcException,
                              source=None)
        # Instead of starting the thread with
        #   self.calc_1D.queue()
        # let's try running the async request
        calc_thread = threads.deferToThread(self.calc_1D.compute)
        calc_thread.addCallback(self.complete1D)

    def complete1D(self, return_data):
        """
        Plot the current data
        """
        # Unpack return data from Calc1D
        x, y, page_id, state, weight,\
        fid, toggle_mode_on, \
        elapsed, index, model,\
        data, update_chisqr, source = return_data

        # Create the new plot
        new_plot = Data1D(x=x, y=y)
        new_plot.is_data = False
        new_plot.dy = numpy.zeros(len(y))
        _yaxis, _yunit = data.get_yaxis()
        _xaxis, _xunit = data.get_xaxis()
        new_plot.title = data.name

        new_plot.group_id = data.group_id
        if new_plot.group_id == None:
            new_plot.group_id = data.group_id
        new_plot.id = str(self.tab_id) + " " + data.name
        new_plot.name = model.name + " [" + data.name + "]"
        new_plot.xaxis(_xaxis, _xunit)
        new_plot.yaxis(_yaxis, _yunit)

        # Assign the new Data1D object-wide
        self._data = new_plot
        self.createTheoryIndex()

        #output=self._cal_chisqr(data=data,
        #                        fid=fid,
        #                        weight=weight,
        #                        page_id=page_id,
        #                        index=index)

    def calculate2DForModel(self):
        """
        Prepare the fitting data object, based on current ModelModel
        """
        self.calc_2D = Calc2D(data=self.data,
                              model=self.kernel_module,
                              page_id=0,
                              qmin=self.q_range_min,
                              qmax=self.q_range_max,
                              smearer=None,
                              state=None,
                              weight=None,
                              fid=None,
                              toggle_mode_on=False,
                              completefn=self.complete2D,
                              update_chisqr=True,
                              exception_handler=self.calcException,
                              source=None)

        # Instead of starting the thread with
        #    self.calc_2D.queue()
        # let's try running the async request
        calc_thread = threads.deferToThread(self.calc_2D.compute)
        calc_thread.addCallback(self.complete2D)

    def complete2D(self, return_data):
        """
        Plot the current data
        Should be a rewrite of fitting.py/_complete2D
        """
        image, data, page_id, model, state, toggle_mode_on,\
        elapsed, index, fid, qmin, qmax, weight, \
        update_chisqr, source = return_data

        numpy.nan_to_num(image)
        new_plot = Data2D(image=image, err_image=data.err_data)
        new_plot.name = model.name + '2d'
        new_plot.title = "Analytical model 2D "
        new_plot.id = str(page_id) + " " + data.name
        new_plot.group_id = str(page_id) + " Model2D"
        new_plot.detector = data.detector
        new_plot.source = data.source
        new_plot.is_data = False
        new_plot.qx_data = data.qx_data
        new_plot.qy_data = data.qy_data
        new_plot.q_data = data.q_data
        new_plot.mask = data.mask
        ## plot boundaries
        new_plot.ymin = data.ymin
        new_plot.ymax = data.ymax
        new_plot.xmin = data.xmin
        new_plot.xmax = data.xmax

        title = data.title

        new_plot.is_data = False
        if data.is_data:
            data_name = str(data.name)
        else:
            data_name = str(model.__class__.__name__) + '2d'

        if len(title) > 1:
            new_plot.title = "Model2D for %s " % model.name + data_name
        new_plot.name = model.name + " [" + \
                                    data_name + "]"

        # Assign the new Data2D object-wide
        self._data = new_plot
        self.createTheoryIndex()

        #output=self._cal_chisqr(data=data,
        #                        weight=weight,
        #                        fid=fid,
        #                        page_id=page_id,
        #                        index=index)
        #    self._plot_residuals(page_id=page_id, data=data, fid=fid,
        #                            index=index, weight=weight)

    def calcException(self, etype, value, tb):
        """
        Something horrible happened in the deferred. Cry me a river.
        """
        logging.error("".join(traceback.format_exception(etype, value, tb)))
        msg = traceback.format_exception(etype, value, tb, limit=1)

    def replaceShellName(self, param_name, value):
        """
        Updates parameter name from <param_name>[n_shell] to <param_name>value
        """
        assert '[' in param_name
        return param_name[:param_name.index('[')]+str(value)

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
            self.addCheckedListToModel(self._poly_model, checked_list)

            #TODO: Need to find cleaner way to input functions
            func = QtGui.QComboBox()
            func.addItems(['rectangle', 'array', 'lognormal', 'gaussian', 'schulz',])
            func_index = self.lstPoly.model().index(row, 6)
            self.lstPoly.setIndexWidget(func_index, func)

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
                        if p.name != par.name:
                            continue
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

