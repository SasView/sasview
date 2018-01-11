import os
import sys

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from PyQt5 import QtGui, QtCore, QtWidgets

import sas.qtgui.Utilities.ObjectLibrary as ObjectLibrary

from sas.qtgui.Perspectives.Fitting.UI.ConstraintWidgetUI import Ui_ConstraintWidgetUI

class ConstraintWidget(QtWidgets.QWidget, Ui_ConstraintWidgetUI):
    """
    Constraints Dialog to select the desired parameter/model constraints
    """

    def __init__(self, parent=None):
        super(ConstraintWidget, self).__init__()
        self.parent = parent
        self.setupUi(self)
        self.currentType = "FitPage"

        # Set up signals/slots
        self.initializeSignals()

        # Create the list of tabs
        self.updateFitList()

    def initializeSignals(self):
        """
        Set up signals/slots for this widget
        """
        self.btnSingle.toggled.connect(self.onFitTypeChange)
        self.btnBatch.toggled.connect(self.onFitTypeChange)
        self.cbSeries.indexChanged.connect(self.onSpecialCaseChange)
        self.cmdFit.clicked.connect(self.onFit)
        self.cmdHelp.clicked.connect(self.onHelp)

    def onFitTypeChange(self, checked):
        """
        Respond to the fit type change
        single fit/batch fit
        """
        pass

    def onSpecialCaseChange(self, index):
        """
        Respond to the combobox change for special case constraint sets
        """
        pass

    def onFit(self):
        """
        Perform the constrained/simultaneous fit
        """
        pass

    def onHelp(self):
        """
        Display the help page
        """
        pass

    def updateFitList(self):
        """
        Fill the list of model/data sets for fitting/constraining
        """
        # look at the object library to find all fit tabs
        objects = ObjectLibrary.listObjects()
        if not objects:
            return
        tabs = [tab for tab in ObjectLibrary.listObjects() if self.currentType in tab]

        pass

    def updateConstraintList(self):
        """
        Fill the list of constraints for the current selection of model/data sets
        """
        pass


