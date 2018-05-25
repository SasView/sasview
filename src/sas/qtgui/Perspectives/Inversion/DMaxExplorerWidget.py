# -*- coding: utf-8 -*-
"""
Dialog panel to explore the P(r) inversion results for a range
of D_max value. User picks a number of points and a range of
distances, then can toggle between inversion outputs and see
their distribution as a function of D_max.
"""

# global
import logging
import numpy as np
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

# sas-global
from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Plotting.Plotter import PlotterWidget
import sas.qtgui.Utilities.GuiUtils as GuiUtils

# local
from .UI.DMaxExplorer import Ui_DmaxExplorer

logger = logging.getLogger(__name__)

from sas.qtgui.Utilities.GuiUtils import enum

W = enum( 'NPTS',      #0
          'DMIN',      #1
          'DMAX',      #2
          'VARIABLE',  #3
)

class DmaxWindow(QtWidgets.QDialog, Ui_DmaxExplorer):
    # The controller which is responsible for managing signal slots connections
    # for the gui and providing an interface to the data model.
    name = "Dmax Explorer"  # For displaying in the combo box

    def __init__(self, pr_state, nfunc, parent=None):
        super(DmaxWindow, self).__init__()
        self.setupUi(self)
        self.parent = parent

        self.setWindowTitle("Dₐₓ Explorer")

        self.pr_state = pr_state
        self.nfunc = nfunc
        self.communicator = GuiUtils.Communicate()

        self.plot = PlotterWidget(self, self)
        self.hasPlot = False
        self.verticalLayout.insertWidget(0, self.plot)

        # Let's choose the Standard Item Model.
        self.model = QtGui.QStandardItemModel(self)
        self.mapper = QtWidgets.QDataWidgetMapper(self)

        # Add validators on line edits
        self.setupValidators()

        # Connect buttons to slots.
        # Needs to be done early so default values propagate properly.
        self.setupSlots()

        # Set up the model.
        self.setupModel()

        # # Set up the mapper
        self.setupMapper()

    def setupValidators(self):
        """Add validators on relevant line edits"""
        self.Npts.setValidator(QtGui.QIntValidator())
        self.minDist.setValidator(GuiUtils.DoubleValidator())
        self.maxDist.setValidator(GuiUtils.DoubleValidator())

    def setupSlots(self):
        self.closeButton.clicked.connect(self.close)
        self.model.itemChanged.connect(self.modelChanged)
        self.dependentVariable.currentIndexChanged.connect(lambda:self.modelChanged(None))

    def setupModel(self):
        self.model.blockSignals(True)
        self.model.setItem(W.NPTS, QtGui.QStandardItem(str(self.nfunc)))
        self.model.blockSignals(False)
        self.model.blockSignals(True)
        self.model.setItem(W.DMIN, QtGui.QStandardItem("{:.1f}".format(0.9*self.pr_state.d_max)))
        self.model.blockSignals(False)
        self.model.blockSignals(True)
        self.model.setItem(W.DMAX, QtGui.QStandardItem("{:.1f}".format(1.1*self.pr_state.d_max)))
        self.model.blockSignals(False)
        self.model.blockSignals(True)
        self.model.setItem(W.VARIABLE, QtGui.QStandardItem( "χ²/dof"))
        self.model.blockSignals(False)

    def setupMapper(self):
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

        try:
            dmin = float(self.model.item(W.DMIN).text())
            dmax = float(self.model.item(W.DMAX).text())
            npts = float(self.model.item(W.NPTS).text())
            xs = np.linspace(dmin, dmax, npts)
        except ValueError as e:
            msg = ("An input value is not correctly formatted. Please check {}"
                   .format(e.message))
            logger.error(msg)

        original = self.pr_state.d_max
        for x in xs:
            self.pr_state.d_max = x
            try:
                out, cov = self.pr_state.invert(self.pr_state.nfunc)

                iq0.append(self.pr_state.iq0(out))
                rg.append(self.pr_state.rg(out))
                pos.append(self.pr_state.get_positive(out))
                pos_err.append(self.pr_state.get_pos_err(out, cov))
                osc.append(self.pr_state.oscillations(out))
                bck.append(self.pr_state.background)
                chi2.append(self.pr_state.chi2)
            except Exception as ex:
                # This inversion failed, skip this D_max value
                msg = "ExploreDialog: inversion failed "
                msg += "for D_max=%s\n%s" % (str(x), ex)
                logger.error(msg)

        #Return the invertor to its original state
        self.pr_state.d_max = original
        try:
            self.pr_state.invert(self.nfunc)
        except RuntimeError as ex:
            msg = "ExploreDialog: inversion failed "
            msg += "for D_max=%s\n%s" % (str(x), ex)
            logger.error(msg)

        plotter = self.model.item(W.VARIABLE).text()
        y_label = y_unit = ""
        x_label = "D_{max}"
        x_unit = "A"
        if plotter == "χ²/dof":
            ys = chi2
            y_label = "\\chi^2/dof"
            y_unit = "a.u."
        elif plotter == "I(Q=0)":
            ys = iq0
            y_label = "I(q=0)"
            y_unit = "\\AA^{-1}"
        elif plotter == "Rg":
            ys = rg
            y_label = "R_g"
            y_unit = "\\AA"
        elif plotter == "Oscillation parameter":
            ys = osc
            y_label = "Osc"
            y_unit = "a.u."
        elif plotter == "Background":
            ys = bck
            y_label = "Bckg"
            y_unit = "\\AA^{-1}"
        elif plotter == "Positive Fraction":
            ys = pos
            y_label = "P^+"
            y_unit = "a.u."
        else:
            ys = pos_err
            y_label = "P^{+}_{1\\sigma}"
            y_unit = "a.u."

        data = Data1D(xs, ys)
        if self.hasPlot:
            self.plot.removePlot(None)
        self.hasPlot = True
        data.title = plotter
        data._xaxis= x_label
        data._xunit = x_unit
        data._yaxis = y_label
        data._yunit = y_unit
        self.plot.plot(data=data, marker="-")

    def closeEvent(self, event):
        """Override close event"""
        self.parent.dmaxWindow = None
        event.accept()
