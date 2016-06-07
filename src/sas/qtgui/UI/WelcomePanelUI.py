# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'WelcomePanelUI.ui'
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

class Ui_WelcomePanelUI(object):
    def setupUi(self, WelcomePanelUI):
        WelcomePanelUI.setObjectName(_fromUtf8("WelcomePanelUI"))
        WelcomePanelUI.resize(658, 711)
        self.gridLayout = QtGui.QGridLayout(WelcomePanelUI)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.imgSasView = QtGui.QLabel(WelcomePanelUI)
        self.imgSasView.setText(_fromUtf8(""))
        self.imgSasView.setPixmap(QtGui.QPixmap(_fromUtf8(":/res/SVwelcome.png")))
        self.imgSasView.setObjectName(_fromUtf8("imgSasView"))
        self.gridLayout.addWidget(self.imgSasView, 0, 0, 1, 1)
        self.line = QtGui.QFrame(WelcomePanelUI)
        self.line.setFrameShape(QtGui.QFrame.HLine)
        self.line.setFrameShadow(QtGui.QFrame.Sunken)
        self.line.setObjectName(_fromUtf8("line"))
        self.gridLayout.addWidget(self.line, 1, 0, 1, 1)
        self.lblAcknowledgements = QtGui.QLabel(WelcomePanelUI)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblAcknowledgements.sizePolicy().hasHeightForWidth())
        self.lblAcknowledgements.setSizePolicy(sizePolicy)
        self.lblAcknowledgements.setObjectName(_fromUtf8("lblAcknowledgements"))
        self.gridLayout.addWidget(self.lblAcknowledgements, 2, 0, 1, 1)
        self.lblVersion = QtGui.QLabel(WelcomePanelUI)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblVersion.sizePolicy().hasHeightForWidth())
        self.lblVersion.setSizePolicy(sizePolicy)
        self.lblVersion.setObjectName(_fromUtf8("lblVersion"))
        self.gridLayout.addWidget(self.lblVersion, 3, 0, 1, 1)
        self.lblLink = QtGui.QLabel(WelcomePanelUI)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblLink.sizePolicy().hasHeightForWidth())
        self.lblLink.setSizePolicy(sizePolicy)
        self.lblLink.setObjectName(_fromUtf8("lblLink"))
        self.gridLayout.addWidget(self.lblLink, 4, 0, 1, 1)

        self.retranslateUi(WelcomePanelUI)
        QtCore.QMetaObject.connectSlotsByName(WelcomePanelUI)

    def retranslateUi(self, WelcomePanelUI):
        WelcomePanelUI.setWindowTitle(_translate("WelcomePanelUI", "Dialog", None))
        self.lblAcknowledgements.setText(_translate("WelcomePanelUI", "This work originally developed as part of the DANSE project funded by the NSF\n"
"under grant DMR-0520547, and currently maintained by NIST, UMD, ORNL, ISIS, ESS\n"
"and ILL.", None))
        self.lblVersion.setText(_translate("WelcomePanelUI", "<html><head/><body><p>SasView 4.0.0-Alpha<br/>Build: 1<br/>(c) 2009 - 2013, UTK, UMD, NIST, ORNL, ISIS, ESS and ILL</p><p><br/></p></body></html>", None))
        self.lblLink.setText(_translate("WelcomePanelUI", "<html><head/><body><p>Comments? Bugs? Requests?</p><p><a href=\"mailto:help@sasview.org\"><span style=\" text-decoration: underline; color:#0000ff;\">Send us a ticket at: help@sasview.org</span></a></p></body></html>", None))

import main_resources_rc

class WelcomePanelUI(QtGui.QDialog, Ui_WelcomePanelUI):
    def __init__(self, parent=None, f=QtCore.Qt.WindowFlags()):
        QtGui.QDialog.__init__(self, parent, f)

        self.setupUi(self)

