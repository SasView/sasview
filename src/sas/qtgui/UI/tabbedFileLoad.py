# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'tabbedFileLoad.ui'
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

class Ui_DataLoadWidget(object):
    def setupUi(self, DataLoadWidget):
        DataLoadWidget.setObjectName(_fromUtf8("DataLoadWidget"))
        DataLoadWidget.resize(481, 612)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/res/ball.ico")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        DataLoadWidget.setWindowIcon(icon)
        self.dataTab = QtGui.QWidget()
        self.dataTab.setObjectName(_fromUtf8("dataTab"))
        self.gridLayout_2 = QtGui.QGridLayout(self.dataTab)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.label = QtGui.QLabel(self.dataTab)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout_2.addWidget(self.label, 0, 0, 1, 1)
        self.comboBox = QtGui.QComboBox(self.dataTab)
        self.comboBox.setObjectName(_fromUtf8("comboBox"))
        self.comboBox.addItem(_fromUtf8(""))
        self.comboBox.addItem(_fromUtf8(""))
        self.comboBox.addItem(_fromUtf8(""))
        self.comboBox.addItem(_fromUtf8(""))
        self.comboBox.addItem(_fromUtf8(""))
        self.comboBox.addItem(_fromUtf8(""))
        self.gridLayout_2.addWidget(self.comboBox, 1, 0, 1, 1)
        spacerItem = QtGui.QSpacerItem(352, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout_2.addItem(spacerItem, 1, 1, 1, 2)
        self.groupBox = QtGui.QGroupBox(self.dataTab)
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.gridLayout = QtGui.QGridLayout(self.groupBox)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.treeView = QtGui.QTreeView(self.groupBox)
        self.treeView.setObjectName(_fromUtf8("treeView"))
        self.gridLayout.addWidget(self.treeView, 0, 0, 1, 1)
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.pushButton = QtGui.QPushButton(self.groupBox)
        self.pushButton.setObjectName(_fromUtf8("pushButton"))
        self.horizontalLayout_3.addWidget(self.pushButton)
        self.pushButton_2 = QtGui.QPushButton(self.groupBox)
        self.pushButton_2.setObjectName(_fromUtf8("pushButton_2"))
        self.horizontalLayout_3.addWidget(self.pushButton_2)
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem1)
        self.gridLayout.addLayout(self.horizontalLayout_3, 1, 0, 1, 1)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.pushButton_6 = QtGui.QPushButton(self.groupBox)
        self.pushButton_6.setObjectName(_fromUtf8("pushButton_6"))
        self.horizontalLayout.addWidget(self.pushButton_6)
        self.comboBox_3 = QtGui.QComboBox(self.groupBox)
        self.comboBox_3.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
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
        self.gridLayout.addLayout(self.horizontalLayout, 2, 0, 1, 1)
        self.gridLayout_2.addWidget(self.groupBox, 2, 0, 1, 3)
        self.groupBox_3 = QtGui.QGroupBox(self.dataTab)
        self.groupBox_3.setObjectName(_fromUtf8("groupBox_3"))
        self.gridLayout_3 = QtGui.QGridLayout(self.groupBox_3)
        self.gridLayout_3.setObjectName(_fromUtf8("gridLayout_3"))
        self.pushButton_5 = QtGui.QPushButton(self.groupBox_3)
        self.pushButton_5.setObjectName(_fromUtf8("pushButton_5"))
        self.gridLayout_3.addWidget(self.pushButton_5, 0, 0, 1, 1)
        self.pushButton_8 = QtGui.QPushButton(self.groupBox_3)
        self.pushButton_8.setObjectName(_fromUtf8("pushButton_8"))
        self.gridLayout_3.addWidget(self.pushButton_8, 1, 0, 1, 1)
        self.comboBox_2 = QtGui.QComboBox(self.groupBox_3)
        self.comboBox_2.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        self.comboBox_2.setObjectName(_fromUtf8("comboBox_2"))
        self.comboBox_2.addItem(_fromUtf8(""))
        self.gridLayout_3.addWidget(self.comboBox_2, 1, 1, 1, 1)
        self.gridLayout_2.addWidget(self.groupBox_3, 3, 0, 1, 2)
        spacerItem3 = QtGui.QSpacerItem(287, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout_2.addItem(spacerItem3, 3, 2, 1, 1)
        DataLoadWidget.addTab(self.dataTab, _fromUtf8(""))
        self.theoryTab = QtGui.QWidget()
        self.theoryTab.setObjectName(_fromUtf8("theoryTab"))
        self.gridLayout_5 = QtGui.QGridLayout(self.theoryTab)
        self.gridLayout_5.setObjectName(_fromUtf8("gridLayout_5"))
        self.groupBox_2 = QtGui.QGroupBox(self.theoryTab)
        self.groupBox_2.setObjectName(_fromUtf8("groupBox_2"))
        self.gridLayout_4 = QtGui.QGridLayout(self.groupBox_2)
        self.gridLayout_4.setObjectName(_fromUtf8("gridLayout_4"))
        self.listView = QtGui.QListView(self.groupBox_2)
        self.listView.setObjectName(_fromUtf8("listView"))
        self.gridLayout_4.addWidget(self.listView, 0, 0, 1, 2)
        self.pushButton_9 = QtGui.QPushButton(self.groupBox_2)
        self.pushButton_9.setObjectName(_fromUtf8("pushButton_9"))
        self.gridLayout_4.addWidget(self.pushButton_9, 1, 0, 1, 1)
        spacerItem4 = QtGui.QSpacerItem(353, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout_4.addItem(spacerItem4, 1, 1, 1, 1)
        self.gridLayout_5.addWidget(self.groupBox_2, 0, 0, 1, 1)
        DataLoadWidget.addTab(self.theoryTab, _fromUtf8(""))

        self.retranslateUi(DataLoadWidget)
        DataLoadWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(DataLoadWidget)

    def retranslateUi(self, DataLoadWidget):
        DataLoadWidget.setWindowTitle(_translate("DataLoadWidget", "TabWidget", None))
        self.label.setText(_translate("DataLoadWidget", "Selection Options", None))
        self.comboBox.setItemText(0, _translate("DataLoadWidget", "Select all", None))
        self.comboBox.setItemText(1, _translate("DataLoadWidget", "Unselect all", None))
        self.comboBox.setItemText(2, _translate("DataLoadWidget", "Select all 1D", None))
        self.comboBox.setItemText(3, _translate("DataLoadWidget", "Unselect all 1D", None))
        self.comboBox.setItemText(4, _translate("DataLoadWidget", "Select all 2D", None))
        self.comboBox.setItemText(5, _translate("DataLoadWidget", "Unselect all 2D", None))
        self.groupBox.setTitle(_translate("DataLoadWidget", "Data", None))
        self.pushButton.setText(_translate("DataLoadWidget", "Load", None))
        self.pushButton_2.setText(_translate("DataLoadWidget", "Delete", None))
        self.pushButton_6.setText(_translate("DataLoadWidget", "Send to", None))
        self.comboBox_3.setItemText(0, _translate("DataLoadWidget", "Fitting", None))
        self.comboBox_3.setItemText(1, _translate("DataLoadWidget", "Pr inversion", None))
        self.comboBox_3.setItemText(2, _translate("DataLoadWidget", "Invariant", None))
        self.checkBox.setText(_translate("DataLoadWidget", "Batch mode", None))
        self.groupBox_3.setTitle(_translate("DataLoadWidget", "Plot", None))
        self.pushButton_5.setText(_translate("DataLoadWidget", "New", None))
        self.pushButton_8.setText(_translate("DataLoadWidget", "Append to", None))
        self.comboBox_2.setItemText(0, _translate("DataLoadWidget", "Graph1", None))
        DataLoadWidget.setTabText(DataLoadWidget.indexOf(self.dataTab), _translate("DataLoadWidget", "Data", None))
        self.groupBox_2.setTitle(_translate("DataLoadWidget", "Theory", None))
        self.pushButton_9.setText(_translate("DataLoadWidget", "Freeze", None))
        DataLoadWidget.setTabText(DataLoadWidget.indexOf(self.theoryTab), _translate("DataLoadWidget", "Theory", None))

import main_resources_rc

class DataLoadWidget(QtGui.QTabWidget, Ui_DataLoadWidget):
    def __init__(self, parent=None, f=QtCore.Qt.WindowFlags()):
        QtGui.QTabWidget.__init__(self, parent, f)

        self.setupUi(self)

