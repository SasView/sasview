# -*- coding: utf-8 -*-
"""
Dialog panel to explore the P(r) inversion results for a range
of D_max value. User picks a number of points and a range of
distances, then can toggle between inversion outputs and see
their distribution as a function of D_max.
"""

# global
import sys
import os
from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import QtWebKit

from twisted.internet import threads

# sas-global
from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Plotting.Plotter import PlotterWidget
import sas.qtgui.Utilities.GuiUtils as GuiUtils

# local
from UI.dmax import Ui_DmaxExplorer
# from InvariantDetails import DetailsDialog
# from InvariantUtils import WIDGETS


class DmaxWindow(QtGui.QDialog, Ui_DmaxExplorer):
    # The controller which is responsible for managing signal slots connections
    # for the gui and providing an interface to the data model.
    name = "Dmax Explorer"  # For displaying in the combo box

    def __init__(self, pr_state, parent=None):
        super(DmaxWindow, self).__init__()
        self.setupUi(self)

        self.setWindowTitle("Dₘₐₓ Explorer")

        self.pr_state = pr_state
        self.communicator = GuiUtils.Communicate()

        self.plot = PlotterWidget(self, self)
        self.verticalLayout.insertWidget(0, self.plot)

        # Let's choose the Standard Item Model.
        self.model = QtGui.QStandardItemModel(self)

        # # Connect buttons to slots.
        # # Needs to be done early so default values propagate properly.
        # self.setupSlots()

        # # Set up the model.
        # self.setupModel()

        # # Set up the mapper
        # self.setupMapper()


if __name__ == "__main__":
    APP = QtGui.QApplication([])
    import qt4reactor
    qt4reactor.install()
    # DO NOT move the following import to the top!
    # (unless you know what you're doing)
    from twisted.internet import reactor
    DLG = DmaxWindow(reactor)
    DLG.show()
    reactor.run()
