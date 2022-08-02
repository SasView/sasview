"""
This module provides the intelligence behind the gui interface for Corfunc.
"""
# pylint: disable=E1101

# global
from PyQt5.QtGui import QStandardItem
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT

from numpy.linalg.linalg import LinAlgError
import numpy as np

from typing import Optional, List

from PyQt5 import QtCore
from PyQt5 import QtGui, QtWidgets

# sas-global
# pylint: disable=import-error, no-name-in-module

from sas.qtgui.Perspectives.Corfunc.CorfuncSlider import CorfuncSlider
from sas.qtgui.Perspectives.Corfunc.CorfuncCanvas import CorfuncCanvas

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Utilities.Reports.reportdata import ReportData
from sas.qtgui.Utilities.Reports import ReportBase

from sas.sascalc.corfunc.corfunc_calculator import CorfuncCalculator
# pylint: enable=import-error, no-name-in-module

# local
from .UI.CorfuncPanel import Ui_CorfuncDialog
from .corefuncutil import WIDGETS
from .saveextrapolated import SaveExtrapolatedPopup
from ..perspective import Perspective

class CorfuncWindow(QtWidgets.QDialog, Ui_CorfuncDialog, Perspective):
    """Displays the correlation function analysis of sas data."""

    name = "Corfunc"
    ext = "crf"

    @property
    def title(self):
        """ Window title """
        return "Corfunc Perspective"

    trigger = QtCore.pyqtSignal(tuple)

# pylint: disable=unused-argument
    def __init__(self, parent=None):
        super(CorfuncWindow, self).__init__()
        self.setupUi(self)

        self.setWindowTitle(self.title)

        self.parent = parent
        self.mapper = None
        self._path = ""
        self.model = QtGui.QStandardItemModel(self)
        self.communicate = self.parent.communicator()
        self.communicate.dataDeletedSignal.connect(self.removeData)
        self._calculator = CorfuncCalculator()
        self._allow_close = False
        self._model_item: Optional[QStandardItem] = None
        self.data = None
        self.has_data = False
        self.txtLowerQMin.setText("0.0")
        self.txtLowerQMin.setEnabled(False)
        self.extrapolation_curve = None


        self.slider = CorfuncSlider()
        self.plotLayout.insertWidget(2, self.slider)

        self._q_space_plot = CorfuncCanvas(self.model)
        self.plotLayout.insertWidget(1, self._q_space_plot)
        self.plotLayout.insertWidget(2, NavigationToolbar2QT(self._q_space_plot, self))

        self._real_space_plot = CorfuncCanvas(self.model)
        self.plotLayout.insertWidget(3, self._real_space_plot)
        self.plotLayout.insertWidget(4, NavigationToolbar2QT(self._real_space_plot, self))

        self.gridLayout_4.setColumnStretch(0, 1)
        self.gridLayout_4.setColumnStretch(1, 2)

        # Connect buttons to slots.
        # Needs to be done early so default values propagate properly.
        self.setup_slots()

        # Set up the model.
        self.setup_model()

        # Set up the mapper
        self.setup_mapper()

    def isSerializable(self):
        """
        Tell the caller that this perspective writes its state
        """
        return True

    def setup_slots(self):
        """Connect the buttons to their appropriate slots."""
        self.cmdExtrapolate.clicked.connect(self.extrapolate)
        self.cmdExtrapolate.setEnabled(False)
        self.cmdTransform.clicked.connect(self.transform)
        self.cmdTransform.setEnabled(False)
        self.cmdExtract.clicked.connect(self.extract)
        self.cmdExtract.setEnabled(False)
        self.cmdSave.clicked.connect(self.on_save)
        self.cmdSave.setEnabled(False)
        self.cmdSaveExtrapolation.clicked.connect(self.on_save_extrapolation)
        self.cmdSaveExtrapolation.setEnabled(False)

        self.cmdCalculateBg.clicked.connect(self.calculate_background)
        self.cmdCalculateBg.setEnabled(False)
        self.cmdHelp.clicked.connect(self.showHelp)

        self.model.itemChanged.connect(self.model_changed)

        self.trigger.connect(self.finish_transform)

    def setup_model(self):
        """Populate the model with default data."""
        # filename
        item = QtGui.QStandardItem(self._path)
        self.model.setItem(WIDGETS.W_FILENAME, item)

        self.model.setItem(WIDGETS.W_QMIN,
                           QtGui.QStandardItem("0.01"))
        self.model.setItem(WIDGETS.W_QMAX,
                           QtGui.QStandardItem("0.20"))
        self.model.setItem(WIDGETS.W_QCUTOFF,
                           QtGui.QStandardItem("0.22"))
        self.model.setItem(WIDGETS.W_BACKGROUND,
                           QtGui.QStandardItem("0"))
        #self.model.setItem(W.W_TRANSFORM,
        #                   QtGui.QStandardItem("Fourier"))
        self.model.setItem(WIDGETS.W_GUINIERA,
                           QtGui.QStandardItem("0.0"))
        self.model.setItem(WIDGETS.W_GUINIERB,
                           QtGui.QStandardItem("0.0"))
        self.model.setItem(WIDGETS.W_PORODK,
                           QtGui.QStandardItem("0.0"))
        self.model.setItem(WIDGETS.W_PORODSIGMA,
                           QtGui.QStandardItem("0.0"))
        self.model.setItem(WIDGETS.W_CORETHICK, QtGui.QStandardItem(str(0)))
        self.model.setItem(WIDGETS.W_INTTHICK, QtGui.QStandardItem(str(0)))
        self.model.setItem(WIDGETS.W_HARDBLOCK, QtGui.QStandardItem(str(0)))
        self.model.setItem(WIDGETS.W_SOFTBLOCK, QtGui.QStandardItem(str(0)))
        self.model.setItem(WIDGETS.W_CRYSTAL, QtGui.QStandardItem(str(0)))
        self.model.setItem(WIDGETS.W_POLY, QtGui.QStandardItem(str(0)))
        self.model.setItem(WIDGETS.W_PERIOD, QtGui.QStandardItem(str(0)))

    def removeData(self, data_list=None):
        """Remove the existing data reference from the Invariant Persepective"""
        if not data_list or self._model_item not in data_list:
            return
        # Clear data plots
        self._q_space_plot.data = None
        self._q_space_plot.extrap = None
        self._q_space_plot.draw_q_space()
        self._real_space_plot.data = None
        self._real_space_plot.extrap = None
        self._real_space_plot.draw_real_space()
        self.slider.setEnabled(False)
        # Clear calculator, model, and data path
        self._calculator = CorfuncCalculator()
        self._model_item = None
        self.has_data = False
        self._path = ""
        # Pass an empty dictionary to set all inputs to their default values
        self.updateFromParameters({})

    def model_changed(self, _):
        """Actions to perform when the data is updated"""
        if not self.mapper:
            return
        self.mapper.toFirst()
        self._q_space_plot.draw_q_space()
        #TODO: Update slider

    def _update_calculator(self):
        self._calculator.lowerq = float(self.model.item(WIDGETS.W_QMIN).text())
        qmax1 = float(self.model.item(WIDGETS.W_QMAX).text())
        qmax2 = float(self.model.item(WIDGETS.W_QCUTOFF).text())
        self._calculator.upperq = (qmax1, qmax2)
        self._calculator.background = \
            float(self.model.item(WIDGETS.W_BACKGROUND).text())

    def extrapolate(self):
        """Extend the experiemntal data with guinier and porod curves."""
        self._update_calculator()
        self.model.itemChanged.disconnect(self.model_changed)
        try:
            params, extrapolation, self.extrapolation_curve = self._calculator.compute_extrapolation()
        except (LinAlgError, ValueError):
            message = "These is not enough data in the fitting range. "\
                      "Try decreasing the upper Q, increasing the "\
                      "cutoff Q, or increasing the lower Q."
            QtWidgets.QMessageBox.warning(self, "Calculation Error",
                                      message)
            self.model.setItem(WIDGETS.W_GUINIERA, QtGui.QStandardItem(""))
            self.model.setItem(WIDGETS.W_GUINIERB, QtGui.QStandardItem(""))
            self.model.setItem(WIDGETS.W_PORODK, QtGui.QStandardItem(""))
            self.model.setItem(WIDGETS.W_PORODSIGMA, QtGui.QStandardItem(""))
            self._q_space_plot.extrap = None
            self.model_changed(None)
            return
        finally:
            self.model.itemChanged.connect(self.model_changed)

        self.model.setItem(WIDGETS.W_GUINIERA, QtGui.QStandardItem("{:.3g}".format(params['A'])))
        self.model.setItem(WIDGETS.W_GUINIERB, QtGui.QStandardItem("{:.3g}".format(params['B'])))
        self.model.setItem(WIDGETS.W_PORODK, QtGui.QStandardItem("{:.3g}".format(params['K'])))
        self.model.setItem(WIDGETS.W_PORODSIGMA,
                           QtGui.QStandardItem("{:.4g}".format(params['sigma'])))

        self._q_space_plot.extrap = extrapolation
        self.model_changed(None)
        self.cmdTransform.setEnabled(True)
        self.cmdSaveExtrapolation.setEnabled(True)


    def transform(self):
        """Calculate the real space version of the extrapolation."""
        #method = self.model.item(W.W_TRANSFORM).text().lower()

        method = "fourier"

        extrap = self._q_space_plot.extrap
        background = float(self.model.item(WIDGETS.W_BACKGROUND).text())

        def updatefn(msg):
            """Report progress of transformation."""
            self.communicate.statusBarUpdateSignal.emit(msg)

        def completefn(transforms):
            """Extract the values from the transforms and plot"""
            self.trigger.emit(transforms)

        self._update_calculator()
        self._calculator.compute_transform(extrap, method, background,
                                           completefn, updatefn)


    def finish_transform(self, transforms):
        self._real_space_plot.data = transforms

        self.update_real_space_plot(transforms)

        self._real_space_plot.draw_real_space()
        self.cmdExtract.setEnabled(True)
        self.cmdSave.setEnabled(True)

    def extract(self):
        transforms = self._real_space_plot.data

        params = self._calculator.extract_parameters(transforms[0])

        self.model.itemChanged.disconnect(self.model_changed)
        self.model.setItem(WIDGETS.W_CORETHICK, QtGui.QStandardItem("{:.3g}".format(params['d0'])))
        self.model.setItem(WIDGETS.W_INTTHICK, QtGui.QStandardItem("{:.3g}".format(params['dtr'])))
        self.model.setItem(WIDGETS.W_HARDBLOCK, QtGui.QStandardItem("{:.3g}".format(params['Lc'])))
        self.model.setItem(WIDGETS.W_SOFTBLOCK, QtGui.QStandardItem("{:.3g}".format(params['soft'])))
        self.model.setItem(WIDGETS.W_CRYSTAL, QtGui.QStandardItem("{:.3g}".format(params['fill'])))
        self.model.setItem(WIDGETS.W_POLY, QtGui.QStandardItem("{:.3g}".format(params['A'])))
        self.model.setItem(WIDGETS.W_PERIOD, QtGui.QStandardItem("{:.3g}".format(params['max'])))
        self.model.itemChanged.connect(self.model_changed)
        self.model_changed(None)


    def update_real_space_plot(self, datas):
        """take the datas tuple and create a plot in DE"""

        assert isinstance(datas, tuple)
        plot_id = id(self)
        titles = [f"1D Correlation [{self._path}]", f"3D Correlation [{self._path}]",
                  'Interface Distribution Function']
        for i, plot in enumerate(datas):
            plot_to_add = self.parent.createGuiData(plot)
            # set plot properties
            title = plot_to_add.title
            plot_to_add.scale = 'linear'
            plot_to_add.symbol = 'Line'
            plot_to_add._xaxis = "x"
            plot_to_add._xunit = "A"
            plot_to_add._yaxis = "\Gamma"
            if i < len(titles):
                title = titles[i]
                plot_to_add.name = titles[i]
            GuiUtils.updateModelItemWithPlot(self._model_item, plot_to_add, title)
            #self.axes.set_xlim(min(data1.x), max(data1.x) / 4)
        pass

    def setup_mapper(self):
        """Creating mapping between model and gui elements."""
        self.mapper = QtWidgets.QDataWidgetMapper(self)
        self.mapper.setOrientation(QtCore.Qt.Vertical)
        self.mapper.setModel(self.model)

        self.mapper.addMapping(self.txtLowerQMax, WIDGETS.W_QMIN)
        self.mapper.addMapping(self.txtUpperQMin, WIDGETS.W_QMAX)
        self.mapper.addMapping(self.txtUpperQMax, WIDGETS.W_QCUTOFF)
        self.mapper.addMapping(self.txtBackground, WIDGETS.W_BACKGROUND)
        #self.mapper.addMapping(self.transformCombo, W.W_TRANSFORM)

        self.mapper.addMapping(self.txtGuinierA, WIDGETS.W_GUINIERA)
        self.mapper.addMapping(self.txtGuinierB, WIDGETS.W_GUINIERB)
        self.mapper.addMapping(self.txtPorodK, WIDGETS.W_PORODK)
        self.mapper.addMapping(self.txtPorodSigma, WIDGETS.W_PORODSIGMA)

        self.mapper.addMapping(self.txtAvgCoreThick, WIDGETS.W_CORETHICK)
        self.mapper.addMapping(self.txtAvgIntThick, WIDGETS.W_INTTHICK)
        self.mapper.addMapping(self.txtAvgHardBlock, WIDGETS.W_HARDBLOCK)
        self.mapper.addMapping(self.txtAvgSoftBlock, WIDGETS.W_SOFTBLOCK)
        self.mapper.addMapping(self.txtPolydisp, WIDGETS.W_POLY)
        self.mapper.addMapping(self.txtLongPeriod, WIDGETS.W_PERIOD)
        self.mapper.addMapping(self.txtLocalCrystal, WIDGETS.W_CRYSTAL)

        self.mapper.addMapping(self.txtFilename, WIDGETS.W_FILENAME)

        self.mapper.toFirst()

    def calculate_background(self):
        """Find a good estimate of the background value."""
        self._update_calculator()
        try:
            background = self._calculator.compute_background()
            temp = QtGui.QStandardItem("{:.4g}".format(background))
            self.model.setItem(WIDGETS.W_BACKGROUND, temp)
        except (LinAlgError, ValueError):
            message = "These is not enough data in the fitting range. "\
                      "Try decreasing the upper Q or increasing the cutoff Q"
            QtWidgets.QMessageBox.warning(self, "Calculation Error",
                                      message)


    # pylint: disable=invalid-name
    def showHelp(self):
        """
        Opens a webpage with help on the perspective
        """
        """ Display help when clicking on Help button """
        treeLocation = "/user/qtgui/Perspectives/Corfunc/corfunc_help.html"
        self.parent.showHelp(treeLocation)

    @staticmethod
    def allowBatch():
        """
        We cannot perform corfunc analysis in batch at this time.
        """
        return False

    @staticmethod
    def allowSwap():
        """
        We cannot swap data with corfunc analysis at this time.
        """
        return False

    def setData(self, data_item: List[QStandardItem], is_batch=False):
        """
        Obtain a QStandardItem object and dissect it to get Data1D/2D
        Pass it over to the calculator
        """


        if self.has_data:
            msg = "Data is already loaded into the Corfunc perspective. Sending a new data set "
            msg += f"will remove the Corfunc analysis for {self._path}. Continue?"
            dialog = QtWidgets.QMessageBox(self, text=msg)
            dialog.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
            retval = dialog.exec_()
            if retval == QtWidgets.QMessageBox.Cancel:
                return

        model_item = data_item[0]
        data = GuiUtils.dataFromItem(model_item)
        self.data = data
        self._model_item = model_item
        self._calculator.set_data(data)
        self.cmdCalculateBg.setEnabled(True)
        self.cmdExtrapolate.setEnabled(True)

        self.model.itemChanged.disconnect(self.model_changed)
        self.model.setItem(WIDGETS.W_GUINIERA, QtGui.QStandardItem(""))
        self.model.setItem(WIDGETS.W_GUINIERB, QtGui.QStandardItem(""))
        self.model.setItem(WIDGETS.W_PORODK, QtGui.QStandardItem(""))
        self.model.setItem(WIDGETS.W_PORODSIGMA, QtGui.QStandardItem(""))
        self.model.setItem(WIDGETS.W_CORETHICK, QtGui.QStandardItem(""))
        self.model.setItem(WIDGETS.W_INTTHICK, QtGui.QStandardItem(""))
        self.model.setItem(WIDGETS.W_HARDBLOCK, QtGui.QStandardItem(""))
        self.model.setItem(WIDGETS.W_SOFTBLOCK, QtGui.QStandardItem(""))
        self.model.setItem(WIDGETS.W_CRYSTAL, QtGui.QStandardItem(""))
        self.model.setItem(WIDGETS.W_POLY, QtGui.QStandardItem(""))
        self.model.setItem(WIDGETS.W_PERIOD, QtGui.QStandardItem(""))
        self.model.itemChanged.connect(self.model_changed)

        self._q_space_plot.data = data
        self._q_space_plot.extrap = None
        self.model_changed(None)
        self.cmdTransform.setEnabled(False)
        self._path = data.name
        self.model.setItem(WIDGETS.W_FILENAME, QtGui.QStandardItem(self._path))
        self._real_space_plot.data = None
        self._real_space_plot.draw_real_space()
        self.has_data = True

    def setClosable(self, value=True):
        """
        Allow outsiders close this widget
        """
        assert isinstance(value, bool)

        self._allow_close = value

    def closeEvent(self, event):
        """
        Overwrite QDialog close method to allow for custom widget close
        """
        if self._allow_close:
            # reset the closability flag
            self.setClosable(value=False)
            # Tell the MdiArea to close the container if it is visible
            if self.parentWidget():
                self.parentWidget().close()
            event.accept()
        else:
            event.ignore()
            # Maybe we should just minimize
            self.setWindowState(QtCore.Qt.WindowMinimized)

    def on_save(self):
        """
        Save corfunc state into a file
        """
        f_name = QtWidgets.QFileDialog.getSaveFileName(
            caption="Save As",
            filter="Corfunc Text Output (*.crf)",
            parent=None)[0]
        if not f_name:
            return
        if "." not in f_name:
            f_name += ".crf"

        data1, data3, data_idf = self._real_space_plot.data

        with open(f_name, "w") as outfile:
            outfile.write("X 1D 3D IDF\n")
            np.savetxt(outfile,
                       np.vstack([(data1.x, data1.y, data3.y, data_idf.y)]).T)
    # pylint: enable=invalid-name

    def on_save_extrapolation(self):
        q = self.data.x
        if self.extrapolation_curve is not None:
            window = SaveExtrapolatedPopup(q, self.extrapolation_curve)
            window.exec_()
        else:
            raise RuntimeError("Inconsistent state: save extrapolation called without extrapolation")

    def serializeAll(self):
        """
        Serialize the corfunc state so data can be saved
        Corfunc is not batch-ready so this will only effect a single page
        :return: {data-id: {self.name: {corfunc-state}}}
        """
        return self.serializeCurrentPage()

    def serializeCurrentPage(self):
        """
        Serialize and return a dictionary of {data_id: corfunc-state}
        Return empty dictionary if no data
        :return: {data-id: {self.name: {corfunc-state}}}
        """
        state = {}
        if self.has_data:
            tab_data = self.getPage()
            data_id = tab_data.pop('data_id', '')
            state[data_id] = {'corfunc_params': tab_data}
        return state

    def getPage(self):
        """
        Serializes full state of this corfunc page
        Called by Save Analysis
        :return: {corfunc-state}
        """
        # Get all parameters from page
        data = GuiUtils.dataFromItem(self._model_item)
        param_dict = self.getState()
        param_dict['data_name'] = str(data.name)
        param_dict['data_id'] = str(data.id)
        return param_dict

    def getState(self):
        """
        Collects all active params into a dictionary of {name: value}
        :return: {name: value}
        """
        return {
            'guinier_a': self.txtGuinierA.text(),
            'guinier_b': self.txtGuinierB.text(),
            'porod_k': self.txtPorodK.text(),
            'porod_sigma': self.txtPorodSigma.text(),
            'avg_core_thick': self.txtAvgCoreThick.text(),
            'avg_inter_thick': self.txtAvgIntThick.text(),
            'avg_hard_block_thick': self.txtAvgHardBlock.text(),
            'avg_soft_block_thick': self.txtAvgSoftBlock.text(),
            'local_crystalinity': self.txtLocalCrystal.text(),
            'polydispersity': self.txtPolydisp.text(),
            'long_period': self.txtLongPeriod.text(),
            'lower_q_max': self.txtLowerQMax.text(),
            'upper_q_min': self.txtUpperQMin.text(),
            'upper_q_max': self.txtUpperQMax.text(),
            'background': self.txtBackground.text(),
        }

    def updateFromParameters(self, params):
        """
        Called by Open Project, Open Analysis, and removeData
        :param params: {param_name: value} -> Default values used if not valid
        :return: None
        """
        # Params should be a dictionary
        if not isinstance(params, dict):
            c_name = params.__class__.__name__
            msg = "Corfunc.updateFromParameters expects a dictionary"
            raise TypeError(f"{msg}: {c_name} received")
        # Assign values to 'Invariant' tab inputs - use defaults if not found
        self.model.setItem(
            WIDGETS.W_GUINIERA, QtGui.QStandardItem(params.get('guinier_a', '0.0')))
        self.model.setItem(
            WIDGETS.W_GUINIERB, QtGui.QStandardItem(params.get('guinier_b', '0.0')))
        self.model.setItem(
            WIDGETS.W_PORODK, QtGui.QStandardItem(params.get('porod_k', '0.0')))
        self.model.setItem(WIDGETS.W_PORODSIGMA, QtGui.QStandardItem(
            params.get('porod_sigma', '0.0')))
        self.model.setItem(WIDGETS.W_CORETHICK, QtGui.QStandardItem(
            params.get('avg_core_thick', '0')))
        self.model.setItem(WIDGETS.W_INTTHICK, QtGui.QStandardItem(
            params.get('avg_inter_thick', '0')))
        self.model.setItem(WIDGETS.W_HARDBLOCK, QtGui.QStandardItem(
            params.get('avg_hard_block_thick', '0')))
        self.model.setItem(WIDGETS.W_SOFTBLOCK, QtGui.QStandardItem(
            params.get('avg_soft_block_thick', '0')))
        self.model.setItem(WIDGETS.W_CRYSTAL, QtGui.QStandardItem(
            params.get('local_crystalinity', '0')))
        self.model.setItem(
            WIDGETS.W_POLY, QtGui.QStandardItem(params.get('polydispersity', '0')))
        self.model.setItem(
            WIDGETS.W_PERIOD, QtGui.QStandardItem(params.get('long_period', '0')))
        self.model.setItem(
            WIDGETS.W_FILENAME, QtGui.QStandardItem(params.get('data_name', '')))
        self.model.setItem(
            WIDGETS.W_QMIN, QtGui.QStandardItem(params.get('lower_q_max', '0.01')))
        self.model.setItem(
            WIDGETS.W_QMAX, QtGui.QStandardItem(params.get('upper_q_min', '0.20')))
        self.model.setItem(
            WIDGETS.W_QCUTOFF, QtGui.QStandardItem(params.get('upper_q_max', '0.22')))
        self.model.setItem(WIDGETS.W_BACKGROUND, QtGui.QStandardItem(
            params.get('background', '0')))
        self.cmdCalculateBg.setEnabled(params.get('background', '0') != '0')
        self.cmdSave.setEnabled(params.get('guinier_a', '0.0') != '0.0')
        self.cmdExtrapolate.setEnabled(params.get('guinier_a', '0.0') != '0.0')
        self.cmdTransform.setEnabled(params.get('long_period', '0') != '0')
        self.cmdExtract.setEnabled(params.get('long_period', '0') != '0')
        if params.get('guinier_a', '0.0') != '0.0':
            self.extrapolate()
        if params.get('long_period', '0') != '0':
            self.transform()

    def get_figures(self):
        """
        Get plots for the report
        """

        return [self._real_space_plot.fig]

    @property
    def real_space_figure(self):
        return self._real_space_plot.fig

    @property
    def q_space_figure(self):
        return self._q_space_plot.fig

    @property
    def supports_reports(self) -> bool:
        return True

    def getReport(self) -> Optional[ReportData]:
        if not self.has_data:
            return None

        report = ReportBase("Correlation Function")
        report.add_data_details(self.data)

        # Format keys
        parameters = self.getState()
        fancy_parameters = {}

        for key in parameters:
            nice_key = " ".join([s.capitalize() for s in key.split("_")])
            if parameters[key].strip() == '':
                fancy_parameters[nice_key] = '-'
            else:
                fancy_parameters[nice_key] = parameters[key]

        report.add_table_dict(fancy_parameters, ("Parameter", "Value"))
        report.add_plot(self.q_space_figure)
        report.add_plot(self.real_space_figure)

        return report.report_data