import json
import os

from PyQt5 import QtGui
from PyQt5 import QtCore
from PyQt5 import QtWidgets

from collections import defaultdict
from sas.qtgui.Utilities.CategoryInstaller import CategoryInstaller
from sasmodels.sasview_model import load_standard_models

from .UI.CategoryManagerUI import Ui_CategoryManagerUI
from .UI.ChangeCategoryUI import Ui_ChangeCategoryUI

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

class Categories(object):
    """
    Container class for accessing model categories
    """
    def __init__(self):
        self.master_category_dict = defaultdict(list)
        self.by_model_dict = defaultdict(list)
        self.model_enabled_dict = defaultdict(bool)
        self.models = {}

        # Prepare the master category list
        self.readCategoryInfo()

        # Prepare model->category lookup
        self.setupModelDict()

    def readCategoryInfo(self):
        """
        Reads the categories in from file
        """
        categorization_file = CategoryInstaller.get_user_file()
        if not os.path.isfile(categorization_file):
            categorization_file = CategoryInstaller.get_default_file()
        with open(categorization_file, 'rb') as cat_file:
            self.master_category_dict = json.load(cat_file)
            self.regenerateModelDict()

        self.category_list = sorted(self.master_category_dict.keys())

    def saveCategories(self):
        """
        Serializes categorization info to file
        """
        self.regenerateMasterDict()
        with open(CategoryInstaller.get_user_file(), 'w') as cat_file:
            json.dump(self.master_category_dict, cat_file)

    def setupModelDict(self):
        """
        create a dictionary for model->category mapping
        """
        # Load the model dict
        models = load_standard_models()
        for model in models:
            # {model name -> model object}
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

    def regenerateMasterDict(self):
        """
        regenerates self.master_category_dict from
        self.by_model_dict and self.model_enabled_dict
        """
        self.master_category_dict = defaultdict(list)
        for model in self.by_model_dict:
            for category in self.by_model_dict[model]:
                self.master_category_dict[category].append\
                    ((model, self.model_enabled_dict[model]))

    def modelToCategory(self):
        """
        Getter for the model->category dict
        """
        return self.by_model_dict

    def modelDict(self):
        """
        Getter for the model list
        """
        return self.models

    def categoryDict(self):
        """
        Getter for the category dict
        """
        return self.master_category_dict

    def categoryList(self):
        """
        Getter for the category list
        """
        return self.category_list



class CategoryManager(QtWidgets.QDialog, Ui_CategoryManagerUI):
    def __init__(self, parent=None, manager=None):
        super(CategoryManager, self).__init__(parent)
        self.setupUi(self)

        self.communicator = manager.communicator()

        self.setWindowTitle("Category Manager")

        self.initializeGlobals()

        self.initializeModels()

        self.initializeSignals()

    def initializeGlobals(self):
        """
        Initialize global variables used in this class
        """
        # Default checked state
        self.chkEnable.setCheckState(QtCore.Qt.Checked)

        # Modify is disabled by default
        self.cmdModify.setEnabled(False)

        # Data for chosen model
        self.model_data = None

        # Categories object
        self.categories = Categories()

    def initializeModels(self):
        """
        Set up models and views
        """
        # Set the main models
        self._category_model = ToolTippedItemModel()
        self.lstCategory.setModel(self._category_model)
        # Proxy model for showing a subset of model content
        self.model_proxy = QtCore.QSortFilterProxyModel(self)
        self.model_proxy.setSourceModel(self._category_model)
        self.lstCategory.setModel(self.model_proxy)

        self.initializeModelList()

        self.setTableProperties(self.lstCategory)

        self.lstCategory.setAlternatingRowColors(True)
        # self.lstCategory.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        # self.lstCategory.setAttribute(QtCore.Qt.WA_MacShowFocusRect, False)

    def initializeModelList(self):
        """
        Model category combo setup
        """
        self._category_model.clear()
        for ind, model in enumerate(self.categories.modelDict()):
            item = QtGui.QStandardItem(model)
            empty_item = QtGui.QStandardItem()
            empty_item.setEditable(False)
            # Add a checkbox to it
            item.setCheckable(True)
            item.setCheckState(QtCore.Qt.Checked)
            item.setEditable(False)
            current_category = self.categories.modelToCategory()[model]
            self._category_model.appendRow([item, empty_item])
            self._category_model.item(ind, 1).setText(', '.join(i for i in current_category))

    def initializeSignals(self):
        """
        :return:
        """
        self.cmdOK.clicked.connect(self.onClose)
        self.cmdModify.clicked.connect(self.onModify)
        self.cmdReset.clicked.connect(self.onReset)

        self.chkEnable.toggled.connect(self.onEnableAll)

        # every change in txtSearch
        self.txtSearch.textChanged.connect(self.onSearch)

        # Signals from the list
        selectionModel = self.lstCategory.selectionModel()
        selectionModel.selectionChanged.connect(self.onListSelection)


    def onClose(self):
        """
        Save the category file before exiting
        """
        self.categories.saveCategories()
        # Ask the fitting widget to reload the comboboxes
        self.communicator.updateModelCategoriesSignal.emit()

        self.close()

    def selectedModels(self):
        """
        Returns a list of selected models
        """
        selected_models = []
        selectionModel = self.lstCategory.selectionModel()
        selectedRows = selectionModel.selectedRows()
        for row in selectedRows:
            model_index = self.model_proxy.mapToSource(row)
            current_text = self._category_model.itemFromIndex(model_index).text()
            selected_models.append(self.categories.modelDict()[current_text])
        return selected_models

    def onListSelection(self):
        """
        Respond to row selection and update GUI
        """
        selected_items = self.selectedModels()
        self.cmdModify.setEnabled(len(selected_items) == 1)

    def onReset(self):
        """
        Reload the saved categories
        """
        self.initializeGlobals()
        # Reload the Categories object
        self.categories = Categories()
        # Reload the model
        self.initializeModelList()
        self.setTableProperties(self.lstCategory)
        self.lstCategory.setAlternatingRowColors(True)

    def onEnableAll(self, isChecked):
        """
        Respond to the Enable/Disable All checkbox
        """
        select = QtCore.Qt.Checked if isChecked else QtCore.Qt.Unchecked
        for row in range(self._category_model.rowCount()):
            self._category_model.item(row).setCheckState(select)

    def onSearch(self):
        """
        Respond to text entered in search field
        """
        if self.txtSearch.isModified():
            input_to_check = str(self.txtSearch.text())

        # redefine the proxy model
        self.model_proxy.setFilterRegExp(QtCore.QRegExp(input_to_check,
                         QtCore.Qt.CaseInsensitive, QtCore.QRegExp.FixedString))

    def onModify(self):
        """
        Show the Change Category dialog - modal
        """
        # Selected category:
        selected_models = self.selectedModels()
        if len(selected_models) > 1:
            # Somehow we got more than one model - complain!
            raise AttributeError("Please select only one model.")
        change_dialog = ChangeCategory(parent=self, categories=self.categories, model=selected_models[0])

        if change_dialog.exec_() != QtWidgets.QDialog.Accepted:
            return
        # Reload the model
        self.initializeModelList()
        self.setTableProperties(self.lstCategory)
        self.lstCategory.setAlternatingRowColors(True)

    def setTableProperties(self, table):
        """
        Setting table properties
        """
        # Table properties
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        #table.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Expanding)
        table.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        table.resizeColumnsToContents()

        # Header
        header = table.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        header.ResizeMode(QtWidgets.QHeaderView.Interactive)


        self._category_model.setHeaderData(0, QtCore.Qt.Horizontal, "Model")
        self._category_model.setHeaderData(1, QtCore.Qt.Horizontal, "Category")

        self._category_model.header_tooltips = ['Select model',
                                                'Change or create new category']

class ChangeCategory(QtWidgets.QDialog, Ui_ChangeCategoryUI):
    """
    Dialog for adding/removing categories for a single model
    """
    def __init__(self, parent=None, categories=None, model=None):
        super(ChangeCategory, self).__init__(parent)
        self.setupUi(self)

        self.model = model
        self.parent = parent
        self.categories = categories

        self.initializeElements()

        self.initializeList()

        self.initializeSignals()

    def initializeElements(self):
        """
        Initialize local GUI elements with information from the Categories object
        """
        self.cbCategories.addItems(self.categories.categoryList())
        self.setWindowTitle("Change Category for: "+ self.model.name)
        self.lblTitle.setText("Current categories for " + self.model.name)
        self.rbExisting.setChecked(True)
        self.onAddChoice()

    def initializeList(self):
        """
        Initialize the category list for the given model
        """
        current_categories = self.categories.modelToCategory()[self.model.name]
        for cat in current_categories:
            self.lstCategories.addItem(cat)

    def initializeSignals(self):
        """
        Initialize signals for UI elements
        """
        self.cmdAdd.clicked.connect(self.onAdd)
        self.cmdRemove.clicked.connect(self.onRemove)
        self.cmdOK.clicked.connect(self.onOK)
        self.cmdCancel.clicked.connect(self.close)

        # Signals from the list
        self.lstCategories.itemSelectionChanged.connect(self.onListSelection)

        # Signals from the radio buttons
        self.rbExisting.toggled.connect(self.onAddChoice)

    def onAddChoice(self):
        """
        Respond to the type selection for new category
        """
        isNew = self.rbNew.isChecked()
        self.cbCategories.setEnabled(not isNew)
        self.txtNewCategory.setEnabled(isNew)

    def onListSelection(self):
        """
        Respond to selection in the category list view
        """
        selected_items = self.selectedModels()
        self.cmdRemove.setEnabled(len(selected_items) > 0)

    def selectedModels(self):
        """
        Returns a list of selected models
        """
        selected_categories = []
        selectedRows = self.lstCategories.selectedItems()
        selected_categories = [str(row.text()) for row in selectedRows]

        return selected_categories

    def onAdd(self):
        """
        Add the chosen category to the list
        """
        if self.rbExisting.isChecked():
            new_category = self.cbCategories.currentText()
        else:
            new_category = self.txtNewCategory.text()
        # Display the current value as txt
        if new_category:
            self.lstCategories.addItem(new_category)

    def onRemove(self):
        """
        Remove selected categories in the list
        """
        selectedRows = self.lstCategories.selectedItems()
        if not selectedRows:
            return
        for row in selectedRows:
            self.lstCategories.takeItem(self.lstCategories.row(row))

    def onOK(self):
        """
        Accept the new categories for the model
        """
        # Read in the categories
        self.categories.modelToCategory()[self.model.name] = self.listCategories()
        self.accept()

    def listCategories(self):
        """
        Returns the list of categories from the QListWidget
        """
        return [str(self.lstCategories.item(i).text()) for i in range(self.lstCategories.count())]
