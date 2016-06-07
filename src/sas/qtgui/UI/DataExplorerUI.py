# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'DataExplorerUI.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_DataExplorerUI(object):
    def setupUi(self, DataExplorerUI):
        DataExplorerUI.setObjectName(_fromUtf8("DataExplorerUI"))
        DataExplorerUI.resize(454, 577)
        self.gridLayout_4 = QtGui.QGridLayout(DataExplorerUI)
        self.gridLayout_4.setObjectName(_fromUtf8("gridLayout_4"))
        self.label = QtGui.QLabel(DataExplorerUI)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout_4.addWidget(self.label, 0, 0, 1, 1)
        self.comboBox = QtGui.QComboBox(DataExplorerUI)
        self.comboBox.setObjectName(_fromUtf8("comboBox"))
        self.comboBox.addItem(_fromUtf8(""))
        self.comboBox.addItem(_fromUtf8(""))
        self.comboBox.addItem(_fromUtf8(""))
        self.comboBox.addItem(_fromUtf8(""))
        self.comboBox.addItem(_fromUtf8(""))
        self.comboBox.addItem(_fromUtf8(""))
        self.gridLayout_4.addWidget(self.comboBox, 1, 0, 1, 1)
        spacerItem = QtGui.QSpacerItem(278, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout_4.addItem(spacerItem, 1, 1, 1, 1)
        self.groupBox = QtGui.QGroupBox(DataExplorerUI)
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.gridLayout = QtGui.QGridLayout(self.groupBox)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.treeView = QtGui.QTreeView(self.groupBox)
        self.treeView.setDragEnabled(True)
        self.treeView.setDragDropMode(QtGui.QAbstractItemView.DragDrop)
        self.treeView.setDefaultDropAction(QtCore.Qt.CopyAction)
        self.treeView.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.treeView.setObjectName(_fromUtf8("treeView"))
        self.gridLayout.addWidget(self.treeView, 0, 0, 1, 1)
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.pushButton = QtGui.QPushButton(self.groupBox)
        self.pushButton.setObjectName(_fromUtf8("pushButton"))
        self.verticalLayout.addWidget(self.pushButton)
        self.pushButton_2 = QtGui.QPushButton(self.groupBox)
        self.pushButton_2.setObjectName(_fromUtf8("pushButton_2"))
        self.verticalLayout.addWidget(self.pushButton_2)
        spacerItem1 = QtGui.QSpacerItem(20, 141, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem1)
        self.gridLayout.addLayout(self.verticalLayout, 0, 1, 1, 1)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.pushButton_6 = QtGui.QPushButton(self.groupBox)
        self.pushButton_6.setObjectName(_fromUtf8("pushButton_6"))
        self.horizontalLayout.addWidget(self.pushButton_6)
        self.comboBox_3 = QtGui.QComboBox(self.groupBox)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.comboBox_3.sizePolicy().hasHeightForWidth())
        self.comboBox_3.setSizePolicy(sizePolicy)
        self.comboBox_3.setObjectName(_fromUtf8("comboBox_3"))
        self.comboBox_3.addItem(_fromUtf8(""))
        self.comboBox_3.addItem(_fromUtf8(""))
        self.comboBox_3.addItem(_fromUtf8(""))
        self.horizontalLayout.addWidget(self.comboBox_3)
        self.checkBox = QtGui.QCheckBox(self.groupBox)
        self.checkBox.setObjectName(_fromUtf8("checkBox"))
        self.horizontalLayout.addWidget(self.checkBox)
        spacerItem2 = QtGui.QSpacerItem(197, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem2)
        self.gridLayout.addLayout(self.horizontalLayout, 1, 0, 1, 2)
        self.gridLayout_4.addWidget(self.groupBox, 2, 0, 1, 2)
        self.groupBox_2 = QtGui.QGroupBox(DataExplorerUI)
        self.groupBox_2.setObjectName(_fromUtf8("groupBox_2"))
        self.gridLayout_2 = QtGui.QGridLayout(self.groupBox_2)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.listView = QtGui.QListView(self.groupBox_2)
        self.listView.setObjectName(_fromUtf8("listView"))
        self.gridLayout_2.addWidget(self.listView, 0, 0, 2, 1)
        self.pushButton_3 = QtGui.QPushButton(self.groupBox_2)
        self.pushButton_3.setObjectName(_fromUtf8("pushButton_3"))
        self.gridLayout_2.addWidget(self.pushButton_3, 0, 1, 1, 1)
        spacerItem3 = QtGui.QSpacerItem(20, 198, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout_2.addItem(spacerItem3, 1, 1, 1, 1)
        self.gridLayout_4.addWidget(self.groupBox_2, 3, 0, 1, 2)
        self.groupBox_3 = QtGui.QGroupBox(DataExplorerUI)
        self.groupBox_3.setObjectName(_fromUtf8("groupBox_3"))
        self.gridLayout_3 = QtGui.QGridLayout(self.groupBox_3)
        self.gridLayout_3.setObjectName(_fromUtf8("gridLayout_3"))
        self.pushButton_4 = QtGui.QPushButton(self.groupBox_3)
        self.pushButton_4.setObjectName(_fromUtf8("pushButton_4"))
        self.gridLayout_3.addWidget(self.pushButton_4, 0, 0, 1, 1)
        self.pushButton_5 = QtGui.QPushButton(self.groupBox_3)
        self.pushButton_5.setObjectName(_fromUtf8("pushButton_5"))
        self.gridLayout_3.addWidget(self.pushButton_5, 1, 0, 1, 1)
        self.comboBox_2 = QtGui.QComboBox(self.groupBox_3)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.comboBox_2.sizePolicy().hasHeightForWidth())
        self.comboBox_2.setSizePolicy(sizePolicy)
        self.comboBox_2.setObjectName(_fromUtf8("comboBox_2"))
        self.comboBox_2.addItem(_fromUtf8(""))
        self.gridLayout_3.addWidget(self.comboBox_2, 1, 1, 1, 1)
        self.gridLayout_4.addWidget(self.groupBox_3, 4, 0, 1, 1)
        self.groupBox_3.raise_()
        self.groupBox_2.raise_()
        self.groupBox.raise_()
        self.comboBox.raise_()
        self.label.raise_()

        self.retranslateUi(DataExplorerUI)
        QtCore.QMetaObject.connectSlotsByName(DataExplorerUI)

    def retranslateUi(self, DataExplorerUI):
        DataExplorerUI.setWindowTitle(_translate("DataExplorerUI", "Dialog", None))
        self.label.setText(_translate("DataExplorerUI", "Selection Options", None))
        self.comboBox.setItemText(0, _translate("DataExplorerUI", "Select all", None))
        self.comboBox.setItemText(1, _translate("DataExplorerUI", "Unselect all", None))
        self.comboBox.setItemText(2, _translate("DataExplorerUI", "Select all 1D", None))
        self.comboBox.setItemText(3, _translate("DataExplorerUI", "Unselect all 1D", None))
        self.comboBox.setItemText(4, _translate("DataExplorerUI", "Select all 2D", None))
        self.comboBox.setItemText(5, _translate("DataExplorerUI", "Unselect all 2D", None))
        self.groupBox.setTitle(_translate("DataExplorerUI", "Data", None))
        self.pushButton.setText(_translate("DataExplorerUI", "Load", None))
        self.pushButton_2.setText(_translate("DataExplorerUI", "Delete", None))
        self.pushButton_6.setText(_translate("DataExplorerUI", "Send to", None))
        self.comboBox_3.setItemText(0, _translate("DataExplorerUI", "Fitting", None))
        self.comboBox_3.setItemText(1, _translate("DataExplorerUI", "Pr inversion", None))
        self.comboBox_3.setItemText(2, _translate("DataExplorerUI", "Invariant", None))
        self.checkBox.setText(_translate("DataExplorerUI", "Batch mode", None))
        self.groupBox_2.setTitle(_translate("DataExplorerUI", "Theory", None))
        self.pushButton_3.setText(_translate("DataExplorerUI", "Freeze", None))
        self.groupBox_3.setTitle(_translate("DataExplorerUI", "Plot", None))
        self.pushButton_4.setText(_translate("DataExplorerUI", "New", None))
        self.pushButton_5.setText(_translate("DataExplorerUI", "Append to", None))
        self.comboBox_2.setItemText(0, _translate("DataExplorerUI", "Graph1", None))


class DataExplorerUI(QtGui.QDialog, Ui_DataExplorerUI):
    def __init__(self, parent=None, f=QtCore.Qt.WindowFlags()):
        QtGui.QDialog.__init__(self, parent, f)

        self.setupUi(self)

