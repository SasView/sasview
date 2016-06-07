# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'MainWindow.ui'
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

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(915, 555)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 915, 21))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        self.menu_File = QtGui.QMenu(self.menubar)
        self.menu_File.setObjectName(_fromUtf8("menu_File"))
        self.menuEdit = QtGui.QMenu(self.menubar)
        self.menuEdit.setObjectName(_fromUtf8("menuEdit"))
        self.menuView = QtGui.QMenu(self.menubar)
        self.menuView.setObjectName(_fromUtf8("menuView"))
        self.menuTool = QtGui.QMenu(self.menubar)
        self.menuTool.setObjectName(_fromUtf8("menuTool"))
        self.menuFitting = QtGui.QMenu(self.menubar)
        self.menuFitting.setObjectName(_fromUtf8("menuFitting"))
        self.menuWindow = QtGui.QMenu(self.menubar)
        self.menuWindow.setObjectName(_fromUtf8("menuWindow"))
        self.menuAnalysis = QtGui.QMenu(self.menubar)
        self.menuAnalysis.setObjectName(_fromUtf8("menuAnalysis"))
        self.menuHelp = QtGui.QMenu(self.menubar)
        self.menuHelp.setObjectName(_fromUtf8("menuHelp"))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        MainWindow.setStatusBar(self.statusbar)
        self.toolBar = QtGui.QToolBar(MainWindow)
        self.toolBar.setObjectName(_fromUtf8("toolBar"))
        MainWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)
        self.actionReset = QtGui.QAction(MainWindow)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/res/reset.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionReset.setIcon(icon)
        self.actionReset.setObjectName(_fromUtf8("actionReset"))
        self.actionSave = QtGui.QAction(MainWindow)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(_fromUtf8(":/res/save.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionSave.setIcon(icon1)
        self.actionSave.setObjectName(_fromUtf8("actionSave"))
        self.actionReport = QtGui.QAction(MainWindow)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(_fromUtf8(":/res/report.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionReport.setIcon(icon2)
        self.actionReport.setObjectName(_fromUtf8("actionReport"))
        self.actionUndo = QtGui.QAction(MainWindow)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(_fromUtf8(":/res/undo.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon3.addPixmap(QtGui.QPixmap(_fromUtf8("res/undo.png")), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.actionUndo.setIcon(icon3)
        self.actionUndo.setObjectName(_fromUtf8("actionUndo"))
        self.actionRedo = QtGui.QAction(MainWindow)
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(_fromUtf8(":/res/redo.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionRedo.setIcon(icon4)
        self.actionRedo.setObjectName(_fromUtf8("actionRedo"))
        self.actionCopy = QtGui.QAction(MainWindow)
        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap(_fromUtf8(":/res/copy.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionCopy.setIcon(icon5)
        self.actionCopy.setObjectName(_fromUtf8("actionCopy"))
        self.actionPaste = QtGui.QAction(MainWindow)
        icon6 = QtGui.QIcon()
        icon6.addPixmap(QtGui.QPixmap(_fromUtf8(":/res/paste.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionPaste.setIcon(icon6)
        self.actionPaste.setObjectName(_fromUtf8("actionPaste"))
        self.actionBookmarks = QtGui.QAction(MainWindow)
        self.actionBookmarks.setCheckable(True)
        icon7 = QtGui.QIcon()
        icon7.addPixmap(QtGui.QPixmap(_fromUtf8(":/res/bookmark.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionBookmarks.setIcon(icon7)
        self.actionBookmarks.setObjectName(_fromUtf8("actionBookmarks"))
        self.actionPerspective = QtGui.QAction(MainWindow)
        self.actionPerspective.setObjectName(_fromUtf8("actionPerspective"))
        self.menubar.addAction(self.menu_File.menuAction())
        self.menubar.addAction(self.menuEdit.menuAction())
        self.menubar.addAction(self.menuView.menuAction())
        self.menubar.addAction(self.menuTool.menuAction())
        self.menubar.addAction(self.menuFitting.menuAction())
        self.menubar.addAction(self.menuWindow.menuAction())
        self.menubar.addAction(self.menuAnalysis.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())
        self.toolBar.addAction(self.actionReset)
        self.toolBar.addAction(self.actionSave)
        self.toolBar.addAction(self.actionReport)
        self.toolBar.addAction(self.actionUndo)
        self.toolBar.addAction(self.actionRedo)
        self.toolBar.addAction(self.actionCopy)
        self.toolBar.addAction(self.actionPaste)
        self.toolBar.addAction(self.actionBookmarks)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow", None))
        self.menu_File.setTitle(_translate("MainWindow", "&File", None))
        self.menuEdit.setTitle(_translate("MainWindow", "Edit", None))
        self.menuView.setTitle(_translate("MainWindow", "View", None))
        self.menuTool.setTitle(_translate("MainWindow", "Tool", None))
        self.menuFitting.setTitle(_translate("MainWindow", "Fitting", None))
        self.menuWindow.setTitle(_translate("MainWindow", "Window", None))
        self.menuAnalysis.setTitle(_translate("MainWindow", "Analysis", None))
        self.menuHelp.setTitle(_translate("MainWindow", "Help", None))
        self.toolBar.setWindowTitle(_translate("MainWindow", "toolBar", None))
        self.actionReset.setText(_translate("MainWindow", "Reset", None))
        self.actionReset.setToolTip(_translate("MainWindow", "Reset", None))
        self.actionSave.setText(_translate("MainWindow", "Save", None))
        self.actionSave.setToolTip(_translate("MainWindow", "Save", None))
        self.actionReport.setText(_translate("MainWindow", "Report", None))
        self.actionReport.setToolTip(_translate("MainWindow", "report", None))
        self.actionUndo.setText(_translate("MainWindow", "Undo", None))
        self.actionRedo.setText(_translate("MainWindow", "Redo", None))
        self.actionRedo.setToolTip(_translate("MainWindow", "Redo", None))
        self.actionCopy.setText(_translate("MainWindow", "Copy", None))
        self.actionCopy.setToolTip(_translate("MainWindow", "Copy parameter values", None))
        self.actionPaste.setText(_translate("MainWindow", "Paste", None))
        self.actionPaste.setToolTip(_translate("MainWindow", "Paste parameter values", None))
        self.actionBookmarks.setText(_translate("MainWindow", "Bookmarks", None))
        self.actionPerspective.setText(_translate("MainWindow", "Perspective", None))

import main_resources_rc

class MainWindow(QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None, f=QtCore.Qt.WindowFlags()):
        QtGui.QMainWindow.__init__(self, parent, f)

        self.setupUi(self)

