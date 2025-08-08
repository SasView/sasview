import json
import logging
import os.path
from collections import defaultdict

from PySide6 import QtCore, QtWidgets

import sasmodels.modelinfo
from sasmodels import generate, modelinfo
from sasmodels.sasview_model import load_standard_models

from sas.qtgui.Utilities.CategoryInstaller import CategoryInstaller
from sas.qtgui.Utilities.ModelEditors.Dialogs.UI.ModelSelectorUI import Ui_ModelSelector
from sas.sascalc.fit import models

logger = logging.getLogger(__name__)

CATEGORY_CUSTOM = "Plugin Models"
CATEGORY_STRUCTURE = "Structure Factor"


class ModelSelector(QtWidgets.QDialog, Ui_ModelSelector):
    """
    Helper widget to get model parameters from a list of available models sorted by type
    """

    # Signals
    returnModelParamsSignal = QtCore.Signal(str, list)

    def __init__(self, parent=None):
        super(ModelSelector, self).__init__(parent)
        self.setupUi(self)

        self.parent = parent
        self.models = {}
        self.custom_models = self.customModels()
        self.selection = None
        self.plugins = None
        self.model_parameters = None
        self.master_category_dict = defaultdict(list)
        self.by_model_dict = defaultdict(list)
        self.model_enabled_dict = defaultdict(bool)

        self.addSignals()
        self.onLoad()

    def addSignals(self):
        """Connect signals to slots"""
        if self.parent:
            self.parent.destroyed.connect(self.onClose)
        self.modelTree.itemSelectionChanged.connect(self.onSelectionChanged)
        self.cmdLoadModel.clicked.connect(self.onLoadModel)
        self.cmdCancel.clicked.connect(self.onClose)

    def onLoad(self):
        # Create model dictionary of all models and load it into the QTreeWidget
        self.setupModelDict()
        self.populateModelTree()

    def setupModelDict(self):
        """Set up a dictionary of all available models and their categories"""
        categorization_file = CategoryInstaller.get_user_file()
        if not os.path.isfile(categorization_file):
            categorization_file = CategoryInstaller.get_default_file()
        with open(categorization_file, 'rb') as cat_file:
            self.master_category_dict = json.load(cat_file)
            self.regenerateModelDict()

        # Load list of available models
        models = load_standard_models()
        for model in models:
            self.models[model.name] = model

        self.readCustomCategoryInfo()

    def readCustomCategoryInfo(self):
        """Reads the custom model category"""
        # Looking for plugins
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

    def regenerateModelDict(self):
        """Regenerates self.by_model_dict which has each model name as the
        key and the list of categories belonging to that model
        along with the enabled mapping
        """
        self.by_model_dict = defaultdict(list)
        for category in self.master_category_dict:
            for (model, enabled) in self.master_category_dict[category]:
                self.by_model_dict[model].append(category)
                self.model_enabled_dict[model] = enabled

    def populateModelTree(self):
        """Populate the model tree with available models"""
        for category in self.master_category_dict:
            category_item = QtWidgets.QTreeWidgetItem(self.modelTree)
            category_item.setText(0, category)
            for (model, _) in self.master_category_dict[category]:
                model_item = QtWidgets.QTreeWidgetItem(category_item)
                model_item.setText(0, model)

    def onSelectionChanged(self):
        """Update selected model and display user selection"""
        # Only one item can be selected at a time as per selectionMode = SingleSelection in the .ui file
        selected_items = self.modelTree.selectedItems()
        if selected_items:
            selected_item = selected_items[0]
            if selected_item.parent() is None:
                # User selected a category. Remove selection.
                self.modelTree.blockSignals(True)
                self.modelTree.clearSelection()
                self.modelTree.blockSignals(False)
            else:
                # User selected a model. Display selection in label.
                self.selection = selected_item.text(0)
                self.lblSelection.clear()
                self.lblSelection.setText(self.selection)

    def onLoadModel(self):
        """Get parameters for selected model, convert to usable data, send to parent. Close dialog if successful."""
        iq_parameters = self.getParameters()
        self.returnModelParamsSignal.emit(self.lblSelection.text(), iq_parameters)
        self.close()
        self.deleteLater()

    def getParameters(self) -> [sasmodels.modelinfo.Parameter]:
        """Get parameters for the selected model and return them as a list"""
        name = self.selection

        if self.modelTree.selectedItems()[0].parent() == CATEGORY_CUSTOM:
            # custom kernel load requires full path
            name = os.path.join(models.find_plugins_dir(), name+".py")
        try:
            kernel_module = generate.load_kernel_module(name)
        except (ModuleNotFoundError, FileNotFoundError):
            # can happen when name attribute not the same as actual filename
            curr_model = self.models[self.selection]
            name, _ = os.path.splitext(os.path.basename(curr_model.filename))
            try:
                kernel_module = generate.load_kernel_module(name)
            except ModuleNotFoundError as ex:
                logger.error(f"Can't find the model {self.selection}\n{ex}")
                return

        return self._find_parameters_from_kernel_module(kernel_module)

    def _find_parameters_from_kernel_module(self, kernel_module: sasmodels.sasview_model.ModuleType) \
            -> [sasmodels.modelinfo.Parameter]:
        """Find the parameters for a kernel module, depending on the model type"""
        if hasattr(kernel_module, 'model_info'):
            # for sum/multiply models
            self.model_parameters = kernel_module.model_info.parameters
        elif hasattr(kernel_module, 'parameters'):
            # built-in and custom models
            self.model_parameters = modelinfo.make_parameter_table(getattr(kernel_module, 'parameters', []))
        elif hasattr(kernel_module, 'Model') and hasattr(kernel_module.Model, "_model_info"):
            # this probably won't work if there's no model_info, but just in case
            self.model_parameters = kernel_module.Model._model_info.parameters
        else:
            # no parameters - default to blank table
            logger.warning(f"No parameters found in model '{self.selection}'.")
            self.model_parameters = modelinfo.ParameterTable([])

        return self.model_parameters.iq_parameters

    @classmethod
    def customModels(cls):
        """Read in file names in the custom plugin directory"""
        manager = models.ModelManager()
        # TODO: Cache plugin models instead of scanning the directory each time.
        manager.update()
        # TODO: Define plugin_models property in ModelManager.
        return manager.base.plugin_models

    def onClose(self):
        self.close()
        self.deleteLater()
