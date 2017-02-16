import sys
from PyQt4 import QtGui
from PyQt4 import QtCore

from UI.FittingUI import Ui_FittingUI

class FittingWindow(QtGui.QDialog, Ui_FittingUI):
    name = "Fitting" # For displaying in the combo box
    def __init__(self, manager=None, parent=None):
        super(FittingWindow, self).__init__()
        self._model_model = QtGui.QStandardItemModel()
        self._poly_model = QtGui.QStandardItemModel()
        self.setupUi(self)

        self.tableView.setModel(self._model_model)
        self.setModelModel()

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

        
    def setModelModel(self):
        # Crete/overwrite model items

        parameters=[]
        p=["scale", "1", "0", "inf", ""]
        for i in xrange(1):
            #for parameter in parameters.keys():
            item1 = QtGui.QStandardItem("background")
            item1.setCheckable(True)
            item2 = QtGui.QStandardItem("0.001")
            item3 = QtGui.QStandardItem("-inf")
            item4 = QtGui.QStandardItem("inf")
            item5 = QtGui.QStandardItem("1/cm")
            self._model_model.appendRow([item1, item2, item3, item4, item5])

            item1 = QtGui.QStandardItem("l_radius")
            item1.setCheckable(True)
            item2 = QtGui.QStandardItem("100")
            item3 = QtGui.QStandardItem("0")
            item4 = QtGui.QStandardItem("inf")
            item5 = QtGui.QStandardItem("A")
            self._model_model.appendRow([item1, item2, item3, item4, item5])

            item1 = QtGui.QStandardItem("ls_sld")
            item1.setCheckable(True)
            item2 = QtGui.QStandardItem("3.5e-06")
            item3 = QtGui.QStandardItem("0")
            item4 = QtGui.QStandardItem("inf")
            item5 = QtGui.QStandardItem("1/A^2")
            self._model_model.appendRow([item1, item2, item3, item4, item5])

            item1 = QtGui.QStandardItem("s_radius")
            item1.setCheckable(True)
            item2 = QtGui.QStandardItem("25")
            item3 = QtGui.QStandardItem("0")
            item4 = QtGui.QStandardItem("inf")
            item5 = QtGui.QStandardItem("A")
            self._model_model.appendRow([item1, item2, item3, item4, item5])

            item1 = QtGui.QStandardItem("solvent_sld")
            item1.setCheckable(True)
            item2 = QtGui.QStandardItem("6.36e-06")
            item3 = QtGui.QStandardItem("0")
            item4 = QtGui.QStandardItem("inf")
            item5 = QtGui.QStandardItem("1/A^2")
            self._model_model.appendRow([item1, item2, item3, item4, item5])

            item1 = QtGui.QStandardItem("vol_frac_ls")
            item1.setCheckable(True)
            item2 = QtGui.QStandardItem("0.1")
            item3 = QtGui.QStandardItem("0")
            item4 = QtGui.QStandardItem("inf")
            item5 = QtGui.QStandardItem("")
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
    dlg = FittingWindow()
    dlg.show()
    sys.exit(app.exec_())
