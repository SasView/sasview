import sys
import json
import  os
from PyQt4 import QtGui
from PyQt4 import QtCore

from UI.fitting import Ui_Dialog

from sasmodels import generate
from sasmodels import modelinfo

from collections import defaultdict
from sas.sasgui.guiframe.CategoryInstaller import CategoryInstaller

class prototype(QtGui.QDialog, Ui_Dialog):
    def __init__(self):
        super(prototype, self).__init__()
        self._model_model = QtGui.QStandardItemModel()
        self._poly_model = QtGui.QStandardItemModel()
        self.setupUi(self)

        self._readCategoryInfo()
        cat_list = sorted(self.master_category_dict.keys())
        self.comboBox.addItems(cat_list)
        self.tableView.setModel(self._model_model)

        model_list = self.master_category_dict['Cylinder']
        for (model, enabled) in model_list:
            self.comboBox_2.addItem(model)
        self.setModelModel('barbell')

        self.pushButton.setEnabled(False)
        self.checkBox_3.setEnabled(False)
        self.checkBox_4.setEnabled(False)
        self.label_20.setText("---")
        self.label_21.setText("---")
        self.label_24.setText("---")

        #self.setTableProperties(self.tableView)

        self.tableView_2.setModel(self._poly_model)
        self.setPolyModel()
        self.setTableProperties(self.tableView_2)

        for row in range(2):
            c = QtGui.QComboBox()
            c.addItems(['rectangle','array','lognormal','gaussian','schulz',])
            i = self.tableView_2.model().index(row,6)
            self.tableView_2.setIndexWidget(i,c)

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

        
    def setModelModel(self, model_name):
        # Crete/overwrite model items

        model_name = str(model_name)
        kernel_module = generate.load_kernel_module(model_name)
        parameters = modelinfo.make_parameter_table(getattr(kernel_module, 'parameters', []))

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

        #TODO: iq_parameters are used here. If orientation paramateres or magnetic are needed kernel_paramters should be used instead
        #For orientation and magentic parameters param.type needs to be checked
        for param in parameters.iq_parameters:
            item1 = QtGui.QStandardItem(param.name)
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

    def setTableProperties(self, table):

        table.setStyleSheet("background-image: url(model.png);")

        # Table properties
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Expanding)
        table.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        # Header
        header = table.horizontalHeader()
        header.setResizeMode(QtGui.QHeaderView.Stretch)
        header.setStretchLastSection(True)

    def setPolyModel(self):
        item1 = QtGui.QStandardItem("Distribution of radius")
        item1.setCheckable(True)
        item2 = QtGui.QStandardItem("0")
        item3 = QtGui.QStandardItem("")
        item4 = QtGui.QStandardItem("")
        item5 = QtGui.QStandardItem("35")
        item6 = QtGui.QStandardItem("3")
        item7 = QtGui.QStandardItem("")
        self._poly_model.appendRow([item1, item2, item3, item4, item5, item6, item7])
        item1 = QtGui.QStandardItem("Distribution of thickness")
        item1.setCheckable(True)
        item2 = QtGui.QStandardItem("0")
        item3 = QtGui.QStandardItem("")
        item4 = QtGui.QStandardItem("")
        item5 = QtGui.QStandardItem("35")
        item6 = QtGui.QStandardItem("3")
        item7 = QtGui.QStandardItem("")
        self._poly_model.appendRow([item1, item2, item3, item4, item5, item6, item7])

        self._poly_model.setHeaderData(0, QtCore.Qt.Horizontal, QtCore.QVariant("Parameter"))
        self._poly_model.setHeaderData(1, QtCore.Qt.Horizontal, QtCore.QVariant("PD[ratio]"))
        self._poly_model.setHeaderData(2, QtCore.Qt.Horizontal, QtCore.QVariant("Min"))
        self._poly_model.setHeaderData(3, QtCore.Qt.Horizontal, QtCore.QVariant("Max"))
        self._poly_model.setHeaderData(4, QtCore.Qt.Horizontal, QtCore.QVariant("Npts"))
        self._poly_model.setHeaderData(5, QtCore.Qt.Horizontal, QtCore.QVariant("Nsigs"))
        self._poly_model.setHeaderData(6, QtCore.Qt.Horizontal, QtCore.QVariant("Function"))

        self.tableView_2.resizeColumnsToContents()
        header = self.tableView_2.horizontalHeader()
        header.ResizeMode(QtGui.QHeaderView.Stretch)
        header.setStretchLastSection(True)


if __name__ == "__main__":
    app = QtGui.QApplication([])
    dlg = prototype()
    dlg.show()
    sys.exit(app.exec_())
