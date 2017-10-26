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
import logging
import numpy as np
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

logger = logging.getLogger(__name__)

def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)

W = enum( 'NPTS',           #0
          'DMIN',               #1
          'DMAX',               #2
          'VARIABLE',         #3
)

class DmaxWindow(QtGui.QDialog, Ui_DmaxExplorer):
    # The controller which is responsible for managing signal slots connections
    # for the gui and providing an interface to the data model.
    name = "Dmax Explorer"  # For displaying in the combo box

    def __init__(self, pr_state, nfunc, parent=None):
        super(DmaxWindow, self).__init__()
        self.setupUi(self)

        self.setWindowTitle("Dₘₐₓ Explorer")

        self.pr_state = pr_state
        self.nfunc = nfunc
        self.communicator = GuiUtils.Communicate()

        self.plot = PlotterWidget(self, self)
        self.verticalLayout.insertWidget(0, self.plot)

        # Let's choose the Standard Item Model.
        self.model = QtGui.QStandardItemModel(self)
        self.mapper = None

        # # Connect buttons to slots.
        # # Needs to be done early so default values propagate properly.
        self.setupSlots()

        # Set up the model.
        self.setupModel()

        # # Set up the mapper
        self.setupMapper()

    def setupSlots(self):
        self.closeButton.clicked.connect(self.close)

        self.model.itemChanged.connect(self.modelChanged)

    def setupModel(self):
        self.model.setItem(W.NPTS, QtGui.QStandardItem(str(self.nfunc)))
        self.model.setItem(W.DMIN,
                           QtGui.QStandardItem(
                               str(0.9*self.pr_state.d_max)))
        self.model.setItem(W.DMAX,
                           QtGui.QStandardItem(
                               str(1.1*self.pr_state.d_max)))
        self.model.setItem(W.VARIABLE,
                           QtGui.QStandardItem( "χ²/dof"))

    def setupMapper(self):
        self.mapper = QtGui.QDataWidgetMapper(self)
        self.mapper.setOrientation(QtCore.Qt.Vertical)
        self.mapper.setModel(self.model)

        self.mapper.addMapping(self.Npts, W.NPTS)
        self.mapper.addMapping(self.minDist, W.DMIN)
        self.mapper.addMapping(self.maxDist, W.DMAX)
        self.mapper.addMapping(self.dependentVariable, W.VARIABLE)

        self.mapper.toFirst()

    def modelChanged(self, item):
        if not self.mapper:
            return

        iq0 = []
        rg = []
        pos = []
        pos_err = []
        osc = []
        bck = []
        chi2 = []

        xs = np.linspace(float(self.model.item(W.DMIN).text()),
                         float(self.model.item(W.DMAX).text()),
                         float(self.model.item(W.NPTS).text()))

        original = self.pr_state.d_max
        for x in xs:
            self.pr_state.d_max = x
            try:
                out, cov = self.pr_state.invert(self.nfunc)

                iq0.append(self.pr_state.iq0(out))
                rg.append(self.pr_state.rg(out))
                pos.append(self.pr_state.get_positive(out))
                pos_err.append(self.pr_state.get_pos_err(out, cov))
                osc.append(self.pr_state.oscillations(out))
                bck.append(self.pr_state.background)
                chi2.append(self.pr_state.chi2)
            except:
                # This inversion failed, skip this D_max value
                msg = "ExploreDialog: inversion failed "
                msg += "for D_max=%s\n%s" % (str(x), sys.exc_value)
                print(msg)
                # logger.error(msg)
        self.pr_state.d_max = original

        plotter = unicode(self.model.item(W.VARIABLE).text())
        if plotter == u"χ²/dof":
            ys = chi2
        elif plotter == u"I(Q=0)":
            ys = iq0
        elif plotter == u"Rg":
            ys = rg
        elif plotter == u"Oscillation parameter":
            ys = osc
        elif plotter == u"Background":
            ys = bck
        elif plotter == u"Positive Fraction":
            ys = pos
        else:
            ys = pos_err

        self.plot.plot(data=Data1D(xs, ys), marker="-")


if __name__ == "__main__":
    APP = QtGui.QApplication([])
    import qt4reactor
    qt4reactor.install()
    # DO NOT move the following import to the top!
    # (unless you know what you're doing)
    from twisted.internet import reactor
    from sas.sascalc.pr.invertor import Invertor
    from sas.sascalc.dataloader.loader import Loader

    data = Loader().load("../../../../../test/pr_inversion/test/sphere_80.txt")[0]
    pr_state = Invertor()
    pr_state.x = data.x
    pr_state.y = data.y
    pr_state.err = data.dy+1e-3

    DLG = DmaxWindow(pr_state, 10, reactor)
    DLG.show()
    reactor.run()
