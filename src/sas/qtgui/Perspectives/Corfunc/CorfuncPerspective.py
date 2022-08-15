
import numpy as np
import math

# global
from PyQt5.QtGui import QStandardItem
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT

from numpy.linalg.linalg import LinAlgError


from typing import Optional, List

import logging

from PyQt5 import QtCore
from PyQt5 import QtGui, QtWidgets

# sas-global
# pylint: disable=import-error, no-name-in-module

from sas.qtgui.Perspectives.Corfunc.CorfunSlider import CorfuncSlider
from sas.qtgui.Perspectives.Corfunc.QSpaceCanvas import QSpaceCanvas
from sas.qtgui.Perspectives.Corfunc.RealSpaceCanvas import RealSpaceCanvas
from sas.sascalc.corfunc.extrapolation_data import ExtrapolationParameters, ExtrapolationInteractionState

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Utilities.Reports.reportdata import ReportData
from sas.qtgui.Utilities.Reports import ReportBase

from sas.sascalc.corfunc.corfunc_calculator import CorfuncCalculator
# pylint: enable=import-error, no-name-in-module

# local
from .UI.CorfuncPanel import Ui_CorfuncDialog
from .util import WIDGETS, safe_float
from .SaveExtrapolatedPopup import SaveExtrapolatedPopup
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

        # Add slider widget
        self.slider = CorfuncSlider()
        self.sliderLayout.insertWidget(1, self.slider)

        # Plots
        self._q_space_plot = QSpaceCanvas(self)
        self.qSpaceLayout.insertWidget(0, self._q_space_plot)
        self.qSpaceLayout.insertWidget(1, NavigationToolbar2QT(self._q_space_plot, self))

        self._real_space_plot = RealSpaceCanvas(self)
        self.realSpaceLayout.insertWidget(0, self._real_space_plot)
        self.realSpaceLayout.insertWidget(1, NavigationToolbar2QT(self._real_space_plot, self))

        # Things to make the corfunc panel behave
        self.mainLayout.setStretch(0, 0)
        self.mainLayout.setStretch(1, 1)
        self.controlFrame.setFixedWidth(583)

        # Connect buttons to slots.
        # Needs to be done early so default values propagate properly.
        self.setup_slots()

        # Set up the model.
        self.setup_model()

        # Set up the mapper
        self.setup_mapper()

    def set_background_warning(self, show_warning: bool = True):
        if show_warning:
            self.txtBackground.setStyleSheet("QLineEdit { background-color: rgb(255,255,0) }")
        else:
            self.txtBackground.setStyleSheet("")

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

        self.txtLowerQMax.textEdited.connect(self.on_extrapolation_text_changed_1)
        self.txtUpperQMin.textEdited.connect(self.on_extrapolation_text_changed_2)
        self.txtUpperQMax.textEdited.connect(self.on_extrapolation_text_changed_3)
        self.set_text_enable(False)

        self.slider.valueEdited.connect(self.on_extrapolation_slider_changed)
        self.slider.valueEditing.connect(self.on_extrapolation_slider_changing)

        self.trigger.connect(self.finish_transform)
        self.txtBackground.textChanged.connect(self.on_background_text_changed)

    def set_text_enable(self, state: bool):
        self.txtLowerQMax.setEnabled(state)
        self.txtUpperQMin.setEnabled(state)
        self.txtUpperQMax.setEnabled(state)

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
        self.model.setItem(WIDGETS.W_POLY_RYAN, QtGui.QStandardItem(str(0)))
        self.model.setItem(WIDGETS.W_POLY_STRIBECK, QtGui.QStandardItem(str(0)))
        self.model.setItem(WIDGETS.W_PERIOD, QtGui.QStandardItem(str(0)))

    def removeData(self, data_list=None):
        """Remove the existing data reference from the Invariant Persepective"""
        if not data_list or self._model_item not in data_list:
            return
        # Clear data plots
        self._q_space_plot.data = None
        self._q_space_plot.extrap = None
        self._q_space_plot.draw_data()
        self._real_space_plot.data = None
        self._real_space_plot.extrap = None
        self._real_space_plot.draw_data()
        self.slider.setEnabled(False)
        # Clear calculator, model, and data path
        self._calculator = CorfuncCalculator()
        self._model_item = None
        self.has_data = False
        self._path = ""
        # Pass an empty dictionary to set all inputs to their default values
        self.updateFromParameters({})
        self.set_text_enable(False)

    def model_changed(self, _):
        """Actions to perform when the data is updated"""
        if not self.mapper:
            return
        self.mapper.toFirst()
        self.slider.extrapolation_parameters = self.extrapolation_parmameters
        self._q_space_plot.draw_data()

    def _update_calculator(self):
        self._calculator.extrapolation_parameters = self.extrapolation_parmameters

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

        self.tabWidget.setCurrentIndex(0)


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

        self._real_space_plot.draw_data()
        self.cmdExtract.setEnabled(True)
        self.cmdSave.setEnabled(True)
        self.tabWidget.setCurrentIndex(1)

    def extract(self):
        transforms = self._real_space_plot.data

        params = self._calculator.extract_parameters(transforms[0])

        if params is not None:

            self.model.itemChanged.disconnect(self.model_changed)

            self.model.setItem(WIDGETS.W_CORETHICK, QtGui.QStandardItem("{:.3g}".format(params.core_thickness)))
            self.model.setItem(WIDGETS.W_INTTHICK, QtGui.QStandardItem("{:.3g}".format(params.interface_thickness)))
            self.model.setItem(WIDGETS.W_HARDBLOCK, QtGui.QStandardItem("{:.3g}".format(params.hard_block_thickness)))
            self.model.setItem(WIDGETS.W_SOFTBLOCK, QtGui.QStandardItem("{:.3g}".format(params.soft_block_thickness)))
            self.model.setItem(WIDGETS.W_CRYSTAL, QtGui.QStandardItem("{:.3g}".format(params.local_crystallinity)))
            self.model.setItem(WIDGETS.W_POLY_RYAN, QtGui.QStandardItem("{:.3g}".format(params.polydispersity_ryan)))
            self.model.setItem(WIDGETS.W_POLY_STRIBECK, QtGui.QStandardItem("{:.3g}".format(params.polydispersity_stribeck)))
            self.model.setItem(WIDGETS.W_PERIOD, QtGui.QStandardItem("{:.3g}".format(params.long_period)))

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
        self.mapper.addMapping(self.txtPolyRyan, WIDGETS.W_POLY_RYAN)
        self.mapper.addMapping(self.txtPolyStribeck, WIDGETS.W_POLY_STRIBECK)
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

    def allowBatch(self):
        """
        We cannot perform corfunc analysis in batch at this time.
        """
        return False

    def allowSwap(self):
        """
        We cannot swap data with corfunc analysis at this time.
        """
        return False

    @property
    def extrapolation_parmameters(self) -> Optional[ExtrapolationParameters]:
        if self.data is not None:
            return ExtrapolationParameters(
                min(self.data.x),
                safe_float(self.model.item(WIDGETS.W_QMIN).text()),
                safe_float(self.model.item(WIDGETS.W_QMAX).text()),
                safe_float(self.model.item(WIDGETS.W_QCUTOFF).text()),
                max(self.data.x))
        else:
            return None

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
        self.model.setItem(WIDGETS.W_POLY_RYAN, QtGui.QStandardItem(""))
        self.model.setItem(WIDGETS.W_POLY_STRIBECK, QtGui.QStandardItem(""))
        self.model.setItem(WIDGETS.W_PERIOD, QtGui.QStandardItem(""))

        self._q_space_plot.data = data
        self._q_space_plot.extrap = None

        # Put the slider in sensible places
        log_data_min = math.log(min(self.data.x))
        log_data_max = math.log(max(self.data.x))

        def fractional_position(f):
            return math.exp(f*log_data_max + (1-f)*log_data_min)

        self.model.setItem(WIDGETS.W_QMIN,
                           QtGui.QStandardItem("%.7g"%fractional_position(0.2)))
        self.model.setItem(WIDGETS.W_QMAX,
                           QtGui.QStandardItem("%.7g"%fractional_position(0.7)))
        self.model.setItem(WIDGETS.W_QCUTOFF,
                           QtGui.QStandardItem("%.7g"%fractional_position(0.8)))


        # Reconnect model
        self.model.itemChanged.connect(self.model_changed)

        self.slider.extrapolation_parameters = self.extrapolation_parmameters
        self.slider.setEnabled(True)

        self.model_changed(None)
        self.cmdTransform.setEnabled(False)
        self._path = data.name
        self.model.setItem(WIDGETS.W_FILENAME, QtGui.QStandardItem(self._path))
        self._real_space_plot.data = None
        self._real_space_plot.draw_data()
        self.set_text_enable(True)
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

    def on_extrapolation_text_changed_1(self, text):
        """ Text in LowerQMax changed"""

        #
        # Note: We need to update based on params below, not a call to self.extrapolation_parameters,
        #       because that value wont be updated until after the QLineEdit.textEdited signals are
        #       processed
        #

        params = self.extrapolation_parmameters._replace(point_1=safe_float(text))
        self.slider.extrapolation_parameters = params
        self._q_space_plot.update_lines(ExtrapolationInteractionState(params))
        self.notify_extrapolation_text_box_validity(params)

    def on_extrapolation_text_changed_2(self, text):
        """ Text in UpperQMin changed"""

        #
        # Note: We need to update based on params below, not a call to self.extrapolation_parameters,
        #       because that value wont be updated until after the QLineEdit.textEdited signals are
        #       processed
        #

        params = self.extrapolation_parmameters._replace(point_2=safe_float(text))
        self.slider.extrapolation_parameters = params
        self._q_space_plot.update_lines(ExtrapolationInteractionState(params))
        self.notify_extrapolation_text_box_validity(params)

    def on_extrapolation_text_changed_3(self, text):
        """ Text in UpperQMax changed"""

        #
        # Note: We need to update based on params below, not a call to self.extrapolation_parameters,
        #       because that value wont be updated until after the QLineEdit.textEdited signals are
        #       processed
        #

        params = self.extrapolation_parmameters._replace(point_3=safe_float(text))
        self.slider.extrapolation_parameters = params
        self._q_space_plot.update_lines(ExtrapolationInteractionState(params))
        self.notify_extrapolation_text_box_validity(params)

    def notify_extrapolation_text_box_validity(self, params):
        """ Set the colour of the text boxes to red if they have bad parameter definitions"""
        box_1_style = ""
        box_2_style = ""
        box_3_style = ""
        red = "QLineEdit { background-color: rgb(255,0,0); color: rgb(255,255,255) }"

        if params.point_1 <= params.data_q_min:
            box_1_style = red

        if params.point_2 <= params.point_1:
            box_1_style = red
            box_2_style = red

        if params.point_3 <= params.point_2:
            box_2_style = red
            box_3_style = red

        if params.data_q_max <= params.point_3:
            box_3_style = red

        # if v3 < v1 and v2, all three will go red (because of transitivity of <=), but this is good
        if params.point_3 <= params.point_1:
            box_1_style = red
            box_3_style = red

        self.txtLowerQMax.setStyleSheet(box_1_style)
        self.txtUpperQMin.setStyleSheet(box_2_style)
        self.txtUpperQMax.setStyleSheet(box_3_style)

    def on_extrapolation_slider_changed(self, state: ExtrapolationParameters):
        """ Slider state changed"""
        format_string = "%.8g"
        self.model.setItem(WIDGETS.W_QMIN,
                           QtGui.QStandardItem(format_string%state.point_1))
        self.model.setItem(WIDGETS.W_QMAX,
                           QtGui.QStandardItem(format_string%state.point_2))
        self.model.setItem(WIDGETS.W_QCUTOFF,
                           QtGui.QStandardItem(format_string%state.point_3))

    def on_extrapolation_slider_changing(self, state: ExtrapolationInteractionState):
        """ Slider is being moved about"""
        self._q_space_plot.update_lines(state)

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

    def on_background_text_changed(self, data):
        """ Background value number changed"""
        # If data has a "bad" value we want to indicate this
        # The only good values can be interpreted as non-negative floats

        is_bad = True

        try:
            value = float(data)
            if self.data is not None:
                min = np.min(self.data.y)
                if value <= min:
                    is_bad = False
                else:
                    logging.warning(f"Background value results in negative intensities ({value} > {min})")
            else:
                is_bad = False

        except ValueError:
            pass

        self.set_background_warning(is_bad)



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
            'polydispersity': self.txtPolyRyan.text(),
            'polydispersity_stribeck': self.txtPolyStribeck.text(),
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
            WIDGETS.W_POLY_RYAN, QtGui.QStandardItem(params.get('polydispersity', '0')))
        self.model.setItem(
            WIDGETS.W_POLY_STRIBECK, QtGui.QStandardItem(params.get('polydispersity_stribeck', '0')))
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