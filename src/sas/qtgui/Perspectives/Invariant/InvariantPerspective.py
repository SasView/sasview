# global
import copy
import logging

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets
from twisted.internet import reactor, threads

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Plotting.PlotterData import Data1D, DataRole

# sas-global
from sas.sascalc.invariant import invariant

# local
from ..perspective import Perspective
from .InvariantDetails import DetailsDialog
from .InvariantUtils import WIDGETS
from .UI.TabbedInvariantUI import Ui_tabbedInvariantUI

# The minimum q-value to be used when extrapolating
Q_MINIMUM = 1e-5
# The maximum q-value to be used when extrapolating
Q_MAXIMUM = 10
# Default number of points of interpolation: high and low range
NPOINTS_Q_INTERP = 10
# Default power law for interpolation
DEFAULT_POWER_LOW = 4

# Background of line edits if settings OK or wrong
BG_WHITE = "background-color: rgb(255, 255, 255);"
BG_RED = "background-color: rgb(244, 170, 164);"


class InvariantWindow(QtWidgets.QDialog, Ui_tabbedInvariantUI, Perspective):
    # The controller which is responsible for managing signal slots connections
    # for the gui and providing an interface to the data model.


    name = "Invariant"
    ext = 'inv'

    @property
    def title(self):
        """ Perspective name """
        return "Invariant Perspective"


    def __init__(self, parent=None):
        super().__init__()
        self.setupUi(self)

        self.setWindowTitle(self.title)

        # initial input params
        self._background = 0.0
        self._scale = 1.0
        self._contrast = 8.0e-6
        self._porod = None

        self.parent = parent

        self._manager = parent
        self._reactor = reactor
        self._model_item = QtGui.QStandardItem()

        self.detailsDialog = DetailsDialog(self)
        self.detailsDialog.cmdOK.clicked.connect(self.enabling)

        self._low_extrapolate = False
        self._low_guinier = True
        self._low_fit = False
        self._low_points = NPOINTS_Q_INTERP
        self._low_power_value = DEFAULT_POWER_LOW

        self._high_extrapolate = False
        self._high_fit = False
        self._high_points = NPOINTS_Q_INTERP
        self._high_power_value = DEFAULT_POWER_LOW

        # Define plots
        self.high_extrapolation_plot = None
        self.low_extrapolation_plot = None

        # no reason to have this widget resizable
        self.resize(self.minimumSizeHint())

        self.communicate = self._manager.communicator()
        self.communicate.dataDeletedSignal.connect(self.removeData)

        self._data = None
        self._path = ""
        self._calculator = None

        self._allow_close = False

        # Modify font in order to display Angstrom symbol correctly
        new_font = 'font-family: -apple-system, "Helvetica Neue", "Ubuntu";'
        self.lblTotalQUnits.setStyleSheet(new_font)
        self.lblSpecificSurfaceUnits.setStyleSheet(new_font)
        self.lblInvariantTotalQUnits.setStyleSheet(new_font)
        self.lblContrastUnits.setStyleSheet(new_font)
        self.lblPorodCstUnits.setStyleSheet(new_font)
        self.lblExtrapolQUnits.setStyleSheet(new_font)

        # To remove blue square around line edits
        self.txtBackgd.setAttribute(QtCore.Qt.WA_MacShowFocusRect, False)
        self.txtContrast.setAttribute(QtCore.Qt.WA_MacShowFocusRect, False)
        self.txtScale.setAttribute(QtCore.Qt.WA_MacShowFocusRect, False)
        self.txtPorodCst.setAttribute(QtCore.Qt.WA_MacShowFocusRect, False)
        self.txtNptsHighQ.setAttribute(QtCore.Qt.WA_MacShowFocusRect, False)
        self.txtNptsLowQ.setAttribute(QtCore.Qt.WA_MacShowFocusRect, False)
        self.txtPowerLowQ.setAttribute(QtCore.Qt.WA_MacShowFocusRect, False)
        self.txtPowerHighQ.setAttribute(QtCore.Qt.WA_MacShowFocusRect, False)

        # Let's choose the Standard Item Model.
        self.model = QtGui.QStandardItemModel(self)

        # Connect buttons to slots.
        # Needs to be done early so default values propagate properly.
        self.setupSlots()

        # Set up the model.
        self.setupModel()

        # Set up the mapper
        self.setupMapper()

        # Default enablement
        self.cmdCalculate.setEnabled(False)

        # validator: double
        self.txtExtrapolQMin.setValidator(GuiUtils.DoubleValidator())
        self.txtExtrapolQMax.setValidator(GuiUtils.DoubleValidator())
        self.txtBackgd.setValidator(GuiUtils.DoubleValidator())
        self.txtContrast.setValidator(GuiUtils.DoubleValidator())
        self.txtScale.setValidator(GuiUtils.DoubleValidator())
        self.txtPorodCst.setValidator(GuiUtils.DoubleValidator())

        # validator: integer number
        self.txtNptsLowQ.setValidator(QtGui.QIntValidator())
        self.txtNptsHighQ.setValidator(QtGui.QIntValidator())
        self.txtPowerLowQ.setValidator(GuiUtils.DoubleValidator())
        self.txtPowerHighQ.setValidator(GuiUtils.DoubleValidator())

        self.mapper.toFirst()

    def get_low_q_extrapolation_upper_limit(self): # TODO: No usages
        q_value = self._data.x[int(self.txtNptsLowQ.text()) - 1]
        return q_value

    def set_low_q_extrapolation_upper_limit(self, value): # TODO: No usages
        n_pts = (np.abs(self._data.x - value)).argmin() + 1
        item = QtGui.QStandardItem(str(n_pts))
        self.model.setItem(WIDGETS.W_NPTS_LOWQ, item)
        self.txtNptsLowQ.setText(str(n_pts))

    def get_high_q_extrapolation_lower_limit(self): # TODO: No usgaes
        q_value = self._data.x[len(self._data.x) - int(self.txtNptsHighQ.text()) - 1]
        return q_value

    def set_high_q_extrapolation_lower_limit(self, value): # TODO: No usages
        n_pts = len(self._data.x) - (np.abs(self._data.x - value)).argmin() + 1
        item = QtGui.QStandardItem(str(int(n_pts)))
        self.model.setItem(WIDGETS.W_NPTS_HIGHQ, item)
        self.txtNptsHighQ.setText(str(n_pts))

    def enabling(self):
        """ """
        self.cmdStatus.setEnabled(True)

    def setClosable(self, value: bool=True):
        """ Allow outsiders close this widget """
        assert isinstance(value, bool) # TODO: Remove

        self._allow_close = value

    def isSerializable(self):
        """
        Tell the caller that this perspective writes its state
        """
        return True

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

    def updateFromModel(self):
        """ Update the globals based on the data in the model """
        self._background = float(self.model.item(WIDGETS.W_BACKGROUND).text())
        self._contrast = float(self.model.item(WIDGETS.W_CONTRAST).text())
        self._scale = float(self.model.item(WIDGETS.W_SCALE).text())
        if self.model.item(WIDGETS.W_POROD_CST).text() != 'None' and self.model.item(WIDGETS.W_POROD_CST).text() != '':
            self._porod = float(self.model.item(WIDGETS.W_POROD_CST).text())

        # Low extrapolating
        self._low_extrapolate = str(self.model.item(WIDGETS.W_ENABLE_LOWQ).text()) == 'true'
        self._low_points = float(self.model.item(WIDGETS.W_NPTS_LOWQ).text())
        self._low_guinier = str(self.model.item(WIDGETS.W_LOWQ_GUINIER).text()) == 'true'
        self._low_fit = str(self.model.item(WIDGETS.W_LOWQ_FIT).text()) == 'true'
        self._low_power_value = float(self.model.item(WIDGETS.W_LOWQ_POWER_VALUE).text())

        # High extrapolating
        self._high_extrapolate = str(self.model.item(WIDGETS.W_ENABLE_HIGHQ).text()) == 'true'
        self._high_points = float(self.model.item(WIDGETS.W_NPTS_HIGHQ).text())
        self._high_fit = str(self.model.item(WIDGETS.W_HIGHQ_FIT).text()) == 'true'
        self._high_power_value = float(self.model.item(WIDGETS.W_HIGHQ_POWER_VALUE).text())

    def calculateInvariant(self): # TODO: pythonic name
        """ Use twisted to thread the calculations away """
        # Find out if extrapolation needs to be used.
        extrapolation = None
        if self._low_extrapolate and self._high_extrapolate:
            extrapolation = "both"
        elif self._high_extrapolate:
            extrapolation = "high"
        elif self._low_extrapolate:
            extrapolation = "low"

        # modify the Calculate button to indicate background process
        self.cmdCalculate.setText("Calculating...")
        self.cmdCalculate.setEnabled(False)

        # Send the calculations to separate thread.
        d = threads.deferToThread(self.calculateThread, extrapolation)

        # Add deferred callback for call return
        d.addCallback(self.deferredPlot)
        d.addErrback(self.calculationFailed)

    def calculationFailed(self, reason): # TODO: rename to on_calculation_failed
        print("calculation failed: ", reason) # TODO: Print to log
        self.allow_calculation()

    def deferredPlot(self, model):
        """
        Run the GUI/model update in the main thread
        """
        reactor.callFromThread(lambda: self.plotResult(model))
        self.allow_calculation()

    def allow_calculation(self):
        # Set the calculate button to available
        self.cmdCalculate.setEnabled(True)
        self.cmdCalculate.setText("Calculate")

    def plotResult(self, model): # TODO: Pythonic name, typing
        """ Plot result of calculation """

        self.model = model
        self._data = GuiUtils.dataFromItem(self._model_item)
        # Send the modified model item to DE for keeping in the model
        plots = [self._model_item]
        if self.high_extrapolation_plot:
            self.high_extrapolation_plot.plot_role = DataRole.ROLE_DEFAULT
            self.high_extrapolation_plot.symbol = "Line"
            self.high_extrapolation_plot.show_errors = False
            self.high_extrapolation_plot.show_q_range_sliders = True
            self.high_extrapolation_plot.slider_update_on_move = False
            self.high_extrapolation_plot.slider_perspective_name = self.name
            self.high_extrapolation_plot.slider_low_q_input = ['txtNptsHighQ']
            self.high_extrapolation_plot.slider_low_q_setter = ['set_high_q_extrapolation_lower_limit']
            self.high_extrapolation_plot.slider_low_q_getter = ['get_high_q_extrapolation_lower_limit']
            self.high_extrapolation_plot.slider_high_q_input = ['txtExtrapolQMax']
            GuiUtils.updateModelItemWithPlot(self._model_item, self.high_extrapolation_plot,
                                             self.high_extrapolation_plot.title)
            plots.append(self.high_extrapolation_plot)
        if self.low_extrapolation_plot:
            self.low_extrapolation_plot.plot_role = DataRole.ROLE_DEFAULT
            self.low_extrapolation_plot.symbol = "Line"
            self.low_extrapolation_plot.show_errors = False
            self.low_extrapolation_plot.show_q_range_sliders = True
            self.low_extrapolation_plot.slider_update_on_move = False
            self.low_extrapolation_plot.slider_perspective_name = self.name
            self.low_extrapolation_plot.slider_high_q_input = ['txtNptsLowQ']
            self.low_extrapolation_plot.slider_high_q_setter = ['set_low_q_extrapolation_upper_limit']
            self.low_extrapolation_plot.slider_high_q_getter = ['get_low_q_extrapolation_upper_limit']
            self.low_extrapolation_plot.slider_low_q_input = ['txtExtrapolQMin']
            GuiUtils.updateModelItemWithPlot(self._model_item, self.low_extrapolation_plot,
                                             self.low_extrapolation_plot.title)
            plots.append(self.low_extrapolation_plot)
        if len(plots) > 1:
            self.communicate.plotRequestedSignal.emit(plots, None)

        # Update the details dialog in case it is open
        self.updateDetailsWidget(model)

    def updateDetailsWidget(self, model): # TODO: pythonic name, type model
        """
        On demand update of the details widget
        """
        if self.detailsDialog.isVisible():
            self.onStatus()

    def calculateThread(self, extrapolation): # Pythonic name, typing
        """
        Perform Invariant calculations.
        """
        # Get most recent values from GUI and model
        self.updateFromModel()

        # Define base message
        msg = ''

        # Set base Q* values to 0.0
        qstar_low = 0.0
        qstar_low_err = 0.0
        qstar_high = 0.0
        qstar_high_err = 0.0

        temp_data = copy.deepcopy(self._data)

        calculation_failed = False
        low_calculation_pass = False
        high_calculation_pass = False

        # Update calculator with background, scale, and data values
        self._calculator.background = self._background
        self._calculator.scale = self._scale
        self._calculator.set_data(temp_data)

        # Low Q extrapolation calculations
        if self._low_extrapolate:
            function_low = "power_law"
            if self._low_guinier:
                function_low = "guinier"
            if self._low_fit:
                self._low_power_value = None

            self._calculator.set_extrapolation(
                range="low", npts=int(self._low_points),
                function=function_low, power=self._low_power_value)
            try:
                qmin_ext = float(self.txtExtrapolQMin.text())
                qmin = None if qmin_ext > self._data.x[0] else qmin_ext
                qstar_low, qstar_low_err = self._calculator.get_qstar_low(qmin)
                low_calculation_pass = True
            except Exception as ex:
                logging.warning(f'Low-q calculation failed: {str(ex)}')
                qstar_low = "ERROR"
                qstar_low_err = "ERROR"
        if self.low_extrapolation_plot and not low_calculation_pass:
            # Remove the existing extrapolation plot
            model_items = GuiUtils.getChildrenFromItem(self._model_item)
            for item in model_items:
                if item.text() == self.low_extrapolation_plot.title:
                    reactor.callFromThread(self._manager.filesWidget.closePlotsForItem, item)
                    reactor.callFromThread(self._model_item.removeRow, item.row())
                    break
            self.low_extrapolation_plot = None
        reactor.callFromThread(self.updateModelFromThread, WIDGETS.D_LOW_QSTAR, qstar_low)
        reactor.callFromThread(self.updateModelFromThread, WIDGETS.D_LOW_QSTAR_ERR, qstar_low_err)

        # High Q Extrapolation calculations
        if self._high_extrapolate:
            function_high = "power_law"
            if self._high_fit:
                self._high_power_value = None
            self._calculator.set_extrapolation(
                range="high", npts=int(self._high_points),
                function=function_high, power=self._high_power_value)
            try:
                qmax_ext = float(self.txtExtrapolQMax.text())
                qmax = None if qmax_ext < self._data.x[int(len(self._data.x) - 1)] else qmax_ext
                qstar_high, qstar_high_err = self._calculator.get_qstar_high(qmax)
                high_calculation_pass = True
            except Exception as ex:
                logging.warning(f'High-q calculation failed: {str(ex)}')
                qstar_high = "ERROR"
                qstar_high_err = "ERROR"
        if self.high_extrapolation_plot and not high_calculation_pass:
            # Remove the existing extrapolation plot
            model_items = GuiUtils.getChildrenFromItem(self._model_item)
            for item in model_items:
                if item.text() == self.high_extrapolation_plot.title:
                    reactor.callFromThread(self._manager.filesWidget.closePlotsForItem, item)
                    reactor.callFromThread(self._model_item.removeRow, item.row())
                    break
            self.high_extrapolation_plot = None
        reactor.callFromThread(self.updateModelFromThread, WIDGETS.D_HIGH_QSTAR, qstar_high)
        reactor.callFromThread(self.updateModelFromThread, WIDGETS.D_HIGH_QSTAR_ERR, qstar_high_err)

        # Q* Data calculations
        try:
            qstar_data, qstar_data_err = self._calculator.get_qstar_with_error()
        except Exception as ex:
            msg += str(ex)
            calculation_failed = True
            qstar_data = "ERROR"
            qstar_data_err = "ERROR"
        reactor.callFromThread(self.updateModelFromThread, WIDGETS.D_DATA_QSTAR, qstar_data)
        reactor.callFromThread(self.updateModelFromThread, WIDGETS.D_DATA_QSTAR_ERR, qstar_data_err)

        # Volume Fraction calculations
        try:
            volume_fraction, volume_fraction_error = self._calculator.get_volume_fraction_with_error(
                self._contrast, extrapolation=extrapolation)
        except Exception as ex:
            calculation_failed = True
            msg += str(ex)
            volume_fraction = "ERROR"
            volume_fraction_error = "ERROR"
        reactor.callFromThread(self.updateModelFromThread, WIDGETS.W_VOLUME_FRACTION, volume_fraction)
        reactor.callFromThread(self.updateModelFromThread, WIDGETS.W_VOLUME_FRACTION_ERR, volume_fraction_error)

        # Surface Error calculations
        if self._porod:
            try:
                surface, surface_error = self._calculator.get_surface_with_error(self._contrast, self._porod)
            except Exception as ex:
                calculation_failed = True
                msg += str(ex)
                surface = "ERROR"
                surface_error = "ERROR"
            reactor.callFromThread(self.updateModelFromThread, WIDGETS.W_SPECIFIC_SURFACE, surface)
            reactor.callFromThread(self.updateModelFromThread, WIDGETS.W_SPECIFIC_SURFACE_ERR, surface_error)

        # Enable the status button
        self.cmdStatus.setEnabled(True)
        # Early exit if calculations failed
        if calculation_failed:
            self.cmdStatus.setEnabled(False)
            logging.warning(f'Calculation failed: {msg}')
            return self.model

        if low_calculation_pass:
            extrapolated_data = self._calculator.get_extra_data_low(
                self._low_points, q_start=float(self.txtExtrapolQMin.text()))
            power_low = self._calculator.get_extrapolation_power(range='low')

            # Plot the chart
            title = f"Low-Q extrapolation [{self._data.name}]"

            # Convert the data into plottable
            self.low_extrapolation_plot = self._manager.createGuiData(extrapolated_data)

            self.low_extrapolation_plot.name = title
            self.low_extrapolation_plot.title = title
            self.low_extrapolation_plot.symbol = "Line"
            self.low_extrapolation_plot.has_errors = False

            # copy labels and units of axes for plotting
            self.low_extrapolation_plot._xaxis = temp_data._xaxis
            self.low_extrapolation_plot._xunit = temp_data._xunit
            self.low_extrapolation_plot._yaxis = temp_data._yaxis
            self.low_extrapolation_plot._yunit = temp_data._yunit

            if self._low_fit:
                reactor.callFromThread(self.updateModelFromThread, WIDGETS.W_LOWQ_POWER_VALUE, power_low)

        if high_calculation_pass:
            # for presentation in InvariantDetails
            qmax_input = float(self.txtExtrapolQMax.text())
            qmax_plot = qmax_input

            power_high = self._calculator.get_extrapolation_power(range='high')
            high_out_data = self._calculator.get_extra_data_high(q_end=qmax_plot, npts=500)

            # Plot the chart
            title = f"High-Q extrapolation [{self._data.name}]"

            # Convert the data into plottable
            self.high_extrapolation_plot = self._manager.createGuiData(high_out_data)
            self.high_extrapolation_plot.name = title
            self.high_extrapolation_plot.title = title
            self.high_extrapolation_plot.symbol = "Line"
            self.high_extrapolation_plot.has_errors = False

            # copy labels and units of axes for plotting
            self.high_extrapolation_plot._xaxis = temp_data._xaxis
            self.high_extrapolation_plot._xunit = temp_data._xunit
            self.high_extrapolation_plot._yaxis = temp_data._yaxis
            self.high_extrapolation_plot._yunit = temp_data._yunit

            if self._high_fit:
                reactor.callFromThread(self.updateModelFromThread, WIDGETS.W_HIGHQ_POWER_VALUE, power_high)

        if qstar_high == "ERROR":
            qstar_high = 0.0
            qstar_high_err = 0.0
        if qstar_low == "ERROR":
            qstar_low = 0.0
            qstar_low_err = 0.0
        qstar_total = qstar_data + qstar_low + qstar_high
        qstar_total_error = np.sqrt(
            qstar_data_err * qstar_data_err
            + qstar_low_err * qstar_low_err + qstar_high_err * qstar_high_err)
        reactor.callFromThread(self.updateModelFromThread, WIDGETS.W_INVARIANT, qstar_total)
        reactor.callFromThread(self.updateModelFromThread, WIDGETS.W_INVARIANT_ERR, qstar_total_error)

        return self.model

    def updateModelFromThread(self, widget, value): # TODO: Name, and typing
        """
        Update the model in the main thread
        """
        try:
            value = float('%.3g' % value) # TODO: Replace with round
        except TypeError:
            pass
        item = QtGui.QStandardItem(str(value))
        self.model.setItem(widget, item)
        self.mapper.toLast()

    def onStatus(self):
        """
        Display Invariant Details panel when clicking on Status button
        """
        self.detailsDialog.setModel(self.model)
        self.detailsDialog.showDialog()
        self.cmdStatus.setEnabled(False)

    def onHelp(self):
        """ Display help when clicking on Help button """
        treeLocation = "/user/qtgui/Perspectives/Invariant/invariant_help.html"
        self.parent.showHelp(treeLocation)

    def setupSlots(self):
        """ """
        self.cmdCalculate.clicked.connect(self.calculateInvariant)
        self.cmdStatus.clicked.connect(self.onStatus)
        self.cmdHelp.clicked.connect(self.onHelp)

        self.chkLowQ.stateChanged.connect(self.stateChanged)
        self.chkLowQ.stateChanged.connect(self.checkQExtrapolatedData)

        self.chkHighQ.stateChanged.connect(self.stateChanged)
        self.chkHighQ.stateChanged.connect(self.checkQExtrapolatedData)

        # slots for the Guinier and PowerLaw radio buttons at low Q
        # since they are not auto-exclusive
        self.rbGuinier.toggled.connect(self.lowGuinierAndPowerToggle)

        self.rbPowerLawLowQ.toggled.connect(self.lowGuinierAndPowerToggle)

        self.rbFitHighQ.toggled.connect(self.hiFitAndFixToggle)

        self.rbFitLowQ.toggled.connect(self.lowFitAndFixToggle)

        self.model.itemChanged.connect(self.modelChanged)

        # update model from gui editing by users
        self.txtBackgd.textChanged.connect(self.updateFromGui)

        self.txtScale.textChanged.connect(self.updateFromGui)

        self.txtContrast.textChanged.connect(self.updateFromGui)

        self.txtPorodCst.textChanged.connect(self.updateFromGui)

        self.txtPowerLowQ.textChanged.connect(self.updateFromGui)

        self.txtPowerHighQ.textChanged.connect(self.updateFromGui)

        self.txtNptsLowQ.textChanged.connect(self.updateFromGui)

        self.txtNptsHighQ.textChanged.connect(self.updateFromGui)

        # check values of n_points compared to distribution length
        self.txtNptsLowQ.textChanged.connect(self.checkLength)

        self.txtNptsHighQ.textChanged.connect(self.checkLength)

        self.txtExtrapolQMin.editingFinished.connect(self.checkQMinRange)
        self.txtExtrapolQMin.textChanged.connect(self.checkQMinRange)

        self.txtExtrapolQMax.editingFinished.connect(self.checkQMaxRange)
        self.txtExtrapolQMax.textChanged.connect(self.checkQMaxRange)

        self.txtNptsLowQ.editingFinished.connect(self.checkQRange)
        self.txtNptsLowQ.textChanged.connect(self.checkQRange)

        self.txtNptsHighQ.editingFinished.connect(self.checkQRange)
        self.txtNptsHighQ.textChanged.connect(self.checkQRange)

    def stateChanged(self):
        """
        Catch modifications from low- and high-Q extrapolation check boxes
        """
        sender = self.sender()

        itemf = QtGui.QStandardItem(str(sender.isChecked()).lower())
        if sender.text() == 'Enable Low-Q extrapolation':
            self.model.setItem(WIDGETS.W_ENABLE_LOWQ, itemf)

        if sender.text() == 'Enable High-Q extrapolation':
            self.model.setItem(WIDGETS.W_ENABLE_HIGHQ, itemf)

    def checkLength(self):
        """
        Validators of number of points for extrapolation.
        Error if it is larger than the distribution length
        """
        self.cmdCalculate.setEnabled(False)
        try:
            int_value = int(self.sender().text())
        except ValueError:
            self.sender().setStyleSheet(BG_RED)
            return

        if self._data:
            if len(self._data.x) < int_value:
                self.sender().setStyleSheet(BG_RED)
                logging.warning(f'The number of points must be smaller than {len(self._data.x)}')
            else:
                self.sender().setStyleSheet(BG_WHITE)
                self.allow_calculation()

    def modelChanged(self, item):
        """ Update when model changed """
        if item.row() == WIDGETS.W_ENABLE_LOWQ:
            toggle = (str(item.text()) == 'true')
            self._low_extrapolate = toggle
            self.lowQToggle(toggle)
        elif item.row() == WIDGETS.W_ENABLE_HIGHQ:
            toggle = (str(item.text()) == 'true')
            self._high_extrapolate = toggle
            self.highQToggle(toggle)

    def checkQExtrapolatedData(self):
        """
        Match status of low or high-Q extrapolated data checkbox in
        DataExplorer with low or high-Q extrapolation checkbox in invariant
        panel
        """
        # name to search in DataExplorer
        if 'Low' in str(self.sender().text()):
            name = "Low-Q extrapolation"
        if 'High' in str(self.sender().text()):
            name = "High-Q extrapolation"

        GuiUtils.updateModelItemStatus(self._manager.filesWidget.model,
                                       self._path, name,
                                       self.sender().checkState())

    def checkQMaxRange(self, value=None):
        if not value:
            value = float(self.txtExtrapolQMax.text()) if self.txtExtrapolQMax.text() else ''
        if value == '':
            self.model.setItem(WIDGETS.W_EX_QMAX, QtGui.QStandardItem(value))
            return
        item = QtGui.QStandardItem(self.txtExtrapolQMax.text())
        self.model.setItem(WIDGETS.W_EX_QMAX, item)
        self.checkQRange()

    def checkQMinRange(self, value=None):
        if not value:
            value = float(self.txtExtrapolQMin.text()) if self.txtExtrapolQMin.text() else ''
        if value == '':
            self.model.setItem(WIDGETS.W_EX_QMIN, QtGui.QStandardItem(value))
            return
        item = QtGui.QStandardItem(self.txtExtrapolQMin.text())
        self.model.setItem(WIDGETS.W_EX_QMIN, item)
        self.checkQRange()

    def checkQRange(self):
        """
        Validate the Q range for the upper and lower bounds

        Valid: q_low_max < q_high_min, q_low_min < q_low_max, q_high_min > q_low_max, q_high_max > q_high_min
        """
        q_high_min = q_low_min = np.inf
        q_high_max = q_low_max = -1 * np.inf
        try:
            # Set high extrapolation lower bound to infinity if no data, or if number points undefined
            q_high_min = self._data.x[len(self._data.x) - int(self.txtNptsHighQ.text())]
        except (ValueError, AttributeError, IndexError):
            # No data, number of points too large/small, or unable to convert number of points to int
            pass
        except Exception as e:
            logging.error(f"{e}")
        try:
            # Set high extrapolation upper bound to negative infinity if Q max input empty
            q_high_max = float(self.txtExtrapolQMax.text())
        except ValueError:
            # Couldn't convert Q min for extrapolation to a float
            pass
        except Exception as e:
            logging.error(f"{e}")
        try:
            # Set low extrapolation lower bound to infinity if Q min input empty
            q_low_min = float(self.txtExtrapolQMin.text())
        except ValueError:
            # Couldn't convert Q min for extrapolation to a float
            pass
        except Exception as e:
            logging.error(f"{e}")
        try:
            # Set high extrapolation lower bound to infinity if no data, or if number points undefined
            q_low_max = self._data.x[int(self.txtNptsLowQ.text())]
        except (ValueError, AttributeError, IndexError):
            # No data, number of points too large/small, or unable to convert number of points to int
            pass
        except Exception as e:
            logging.error(f"{e}")

        calculate = ((q_low_min < q_low_max) and (q_high_min < q_high_max) and (q_high_min > q_low_max)
                     and self.txtExtrapolQMax.text() and self.txtExtrapolQMin.text() and self.txtNptsLowQ.text()
                     and self.txtNptsHighQ.text())
        self.txtExtrapolQMin.setStyleSheet(BG_RED if q_low_min >= q_low_max and q_low_max < q_high_min else BG_WHITE)
        self.txtExtrapolQMax.setStyleSheet(BG_RED if q_high_min >= q_high_max and q_low_max < q_high_min else BG_WHITE)
        if calculate:
            self.allow_calculation()
        else:
            self.cmdCalculate.setEnabled(False)

    def updateFromGui(self):
        """ Update model when new user inputs """
        possible_senders = ['txtBackgd', 'txtContrast', 'txtPorodCst',
                            'txtScale', 'txtPowerLowQ', 'txtPowerHighQ',
                            'txtNptsLowQ', 'txtNptsHighQ']

        related_widgets = [WIDGETS.W_BACKGROUND, WIDGETS.W_CONTRAST,
                           WIDGETS.W_POROD_CST, WIDGETS.W_SCALE,
                           WIDGETS.W_LOWQ_POWER_VALUE, WIDGETS.W_HIGHQ_POWER_VALUE,
                           WIDGETS.W_NPTS_LOWQ, WIDGETS.W_NPTS_HIGHQ]

        related_internal_values = [self._background, self._contrast,
                                   self._porod, self._scale,
                                   self._low_power_value,
                                   self._high_power_value,
                                   self._low_points, self._high_points]

        item = QtGui.QStandardItem(self.sender().text())

        index_elt = possible_senders.index(self.sender().objectName())

        self.model.setItem(related_widgets[index_elt], item)
        try:
            related_internal_values[index_elt] = float(self.sender().text())
            self.sender().setStyleSheet(BG_WHITE)
            self.allow_calculation()
        except ValueError:
            # empty field, just skip
            self.sender().setStyleSheet(BG_RED)
            self.cmdCalculate.setEnabled(False)

    def lowGuinierAndPowerToggle(self, toggle):
        """
        Guinier and Power radio buttons cannot be selected at the same time
        If Power is selected, Fit and Fix radio buttons are visible and
        Power line edit can be edited if Fix is selected
        """
        if self.sender().text() == 'Guinier':
            itemt = QtGui.QStandardItem(str(toggle).lower())
            self.model.setItem(WIDGETS.W_LOWQ_GUINIER, itemt)
            toggle = not toggle
            self.rbPowerLawLowQ.setChecked(toggle)
        else:
            self.rbGuinier.setChecked(not toggle)
            itemt = QtGui.QStandardItem(str(not toggle).lower())
            self.model.setItem(WIDGETS.W_LOWQ_GUINIER, itemt)

        self.rbFitLowQ.setVisible(toggle)
        self.rbFixLowQ.setVisible(toggle)
        self.txtPowerLowQ.setEnabled(toggle and (not self._low_fit))
        self.updateFromModel()

    def lowFitAndFixToggle(self, toggle):
        """ Fit and Fix radiobuttons cannot be selected at the same time """
        itemt = QtGui.QStandardItem(str(toggle).lower())
        self.model.setItem(WIDGETS.W_LOWQ_FIT, itemt)
        self.txtPowerLowQ.setEnabled(not toggle)
        self.updateFromModel()

    def hiFitAndFixToggle(self, toggle):
        """
        Enable editing of power exponent if Fix for high Q is checked
        Disable otherwise
        """
        itemt = QtGui.QStandardItem(str(toggle).lower())
        self.model.setItem(WIDGETS.W_HIGHQ_FIT, itemt)
        self.txtPowerHighQ.setEnabled(not toggle)
        self.updateFromModel()

    def highQToggle(self, clicked):
        """ Disable/enable High Q extrapolation """
        self.rbFitHighQ.setEnabled(clicked)
        self.rbFixHighQ.setEnabled(clicked)
        self.txtNptsHighQ.setEnabled(clicked)
        self.txtPowerHighQ.setEnabled(clicked and not self._high_fit)

    def lowQToggle(self, clicked):
        """ Disable / enable Low Q extrapolation """
        self.rbGuinier.setEnabled(clicked)
        self.rbPowerLawLowQ.setEnabled(clicked)
        self.txtNptsLowQ.setEnabled(clicked)
        # Enable subelements
        self.rbFitLowQ.setVisible(self.rbPowerLawLowQ.isChecked())
        self.rbFixLowQ.setVisible(self.rbPowerLawLowQ.isChecked())
        self.rbFitLowQ.setEnabled(clicked)  # and not self._low_guinier)
        self.rbFixLowQ.setEnabled(clicked)  # and not self._low_guinier)

        self.txtPowerLowQ.setEnabled(clicked
                                     and not self._low_guinier
                                     and not self._low_fit)

    def setupModel(self):
        """ """
        # filename
        item = QtGui.QStandardItem(self._path)
        self.model.setItem(WIDGETS.W_NAME, item)

        # add Q parameters to the model
        qmin = 0.0
        item = QtGui.QStandardItem(str(qmin))
        self.model.setItem(WIDGETS.W_QMIN, item)
        qmax = 0.0
        item = QtGui.QStandardItem(str(qmax))
        self.model.setItem(WIDGETS.W_QMAX, item)

        # add extrapolated Q parameters to the model
        item = QtGui.QStandardItem(str(Q_MINIMUM))
        self.model.setItem(WIDGETS.W_EX_QMIN, item)
        item = QtGui.QStandardItem(str(Q_MAXIMUM))
        self.model.setItem(WIDGETS.W_EX_QMAX, item)

        # add custom input params
        item = QtGui.QStandardItem(str(self._background))
        self.model.setItem(WIDGETS.W_BACKGROUND, item)
        item = QtGui.QStandardItem(str(self._contrast))
        self.model.setItem(WIDGETS.W_CONTRAST, item)
        item = QtGui.QStandardItem(str(self._scale))
        self.model.setItem(WIDGETS.W_SCALE, item)
        # leave line edit empty if Porod constant not defined
        if self._porod is not None:
            item = QtGui.QStandardItem(str(self._porod))
        else:
            item = QtGui.QStandardItem('')
        self.model.setItem(WIDGETS.W_POROD_CST, item)

        # Dialog elements
        itemf = QtGui.QStandardItem("false")
        self.model.setItem(WIDGETS.W_ENABLE_HIGHQ, itemf)
        itemf = QtGui.QStandardItem("false")
        self.model.setItem(WIDGETS.W_ENABLE_LOWQ, itemf)

        item = QtGui.QStandardItem(str(NPOINTS_Q_INTERP))
        self.model.setItem(WIDGETS.W_NPTS_LOWQ, item)
        item = QtGui.QStandardItem(str(NPOINTS_Q_INTERP))
        self.model.setItem(WIDGETS.W_NPTS_HIGHQ, item)

        itemt = QtGui.QStandardItem("true")
        self.model.setItem(WIDGETS.W_LOWQ_GUINIER, itemt)

        itemt = QtGui.QStandardItem("true")
        self.model.setItem(WIDGETS.W_LOWQ_FIT, itemt)
        item = QtGui.QStandardItem(str(DEFAULT_POWER_LOW))
        self.model.setItem(WIDGETS.W_LOWQ_POWER_VALUE, item)

        itemt = QtGui.QStandardItem("true")
        self.model.setItem(WIDGETS.W_HIGHQ_FIT, itemt)
        item = QtGui.QStandardItem(str(DEFAULT_POWER_LOW))
        self.model.setItem(WIDGETS.W_HIGHQ_POWER_VALUE, item)

    def setupMapper(self):
        # Set up the mapper.
        self.mapper = QtWidgets.QDataWidgetMapper(self)
        self.mapper.setOrientation(QtCore.Qt.Vertical)
        self.mapper.setModel(self.model)

        # Filename
        self.mapper.addMapping(self.txtName, WIDGETS.W_NAME)

        # Qmin/Qmax
        self.mapper.addMapping(self.txtTotalQMin, WIDGETS.W_QMIN)
        self.mapper.addMapping(self.txtTotalQMax, WIDGETS.W_QMAX)
        # Extrapolated Qmin/Qmax
        self.mapper.addMapping(self.txtExtrapolQMin, WIDGETS.W_EX_QMIN)
        self.mapper.addMapping(self.txtExtrapolQMax, WIDGETS.W_EX_QMAX)

        # Background
        self.mapper.addMapping(self.txtBackgd, WIDGETS.W_BACKGROUND)

        # Scale
        self.mapper.addMapping(self.txtScale, WIDGETS.W_SCALE)

        # Contrast
        self.mapper.addMapping(self.txtContrast, WIDGETS.W_CONTRAST)

        # Porod constant
        self.mapper.addMapping(self.txtPorodCst, WIDGETS.W_POROD_CST)

        # Lowq/Highq items
        self.mapper.addMapping(self.chkLowQ, WIDGETS.W_ENABLE_LOWQ)
        self.mapper.addMapping(self.chkHighQ, WIDGETS.W_ENABLE_HIGHQ)

        self.mapper.addMapping(self.txtNptsLowQ, WIDGETS.W_NPTS_LOWQ)
        self.mapper.addMapping(self.rbGuinier, WIDGETS.W_LOWQ_GUINIER)
        self.mapper.addMapping(self.rbFitLowQ, WIDGETS.W_LOWQ_FIT)
        self.mapper.addMapping(self.txtPowerLowQ, WIDGETS.W_LOWQ_POWER_VALUE)

        self.mapper.addMapping(self.txtNptsHighQ, WIDGETS.W_NPTS_HIGHQ)
        self.mapper.addMapping(self.rbFitHighQ, WIDGETS.W_HIGHQ_FIT)
        self.mapper.addMapping(self.txtPowerHighQ, WIDGETS.W_HIGHQ_POWER_VALUE)

        # Output
        self.mapper.addMapping(self.txtVolFract, WIDGETS.W_VOLUME_FRACTION)
        self.mapper.addMapping(self.txtVolFractErr, WIDGETS.W_VOLUME_FRACTION_ERR)
        self.mapper.addMapping(self.txtSpecSurf, WIDGETS.W_SPECIFIC_SURFACE)
        self.mapper.addMapping(self.txtSpecSurfErr, WIDGETS.W_SPECIFIC_SURFACE_ERR)
        self.mapper.addMapping(self.txtInvariantTot, WIDGETS.W_INVARIANT)
        self.mapper.addMapping(self.txtInvariantTotErr, WIDGETS.W_INVARIANT_ERR)

        self.mapper.toFirst()

    def setData(self, data_item=None, is_batch=False):
        """
        Obtain a QStandardItem object and dissect it to get Data1D/2D
        Pass it over to the calculator
        """
        assert data_item is not None

        if self.txtName.text() == data_item[0].text():
            logging.info('This file is already loaded in Invariant panel.')
            return

        if not isinstance(data_item, list):
            msg = "Incorrect type passed to the Invariant Perspective"
            raise AttributeError(msg)

        if not isinstance(data_item[0], QtGui.QStandardItem):
            msg = "Incorrect type passed to the Invariant Perspective"
            raise AttributeError(msg)

        # only 1 file can be loaded
        self._model_item = data_item[0]

        # Reset plots on data change
        self.low_extrapolation_plot = None
        self.high_extrapolation_plot = None

        # Extract data on 1st child - this is the Data1D/2D component
        data = GuiUtils.dataFromItem(self._model_item)
        self.model.item(WIDGETS.W_NAME).setData(self._model_item.text())
        # update GUI and model with info from loaded data
        self.updateGuiFromFile(data=data)

    def removeData(self, data_list=None):
        """Remove the existing data reference from the Invariant Persepective"""
        if not data_list or self._model_item not in data_list:
            return
        self._data = None
        self._model_item = None
        self.low_extrapolation_plot = None
        self.high_extrapolation_plot = None
        self._path = ""
        self.txtName.setText('')
        self._porod = None
        # Pass an empty dictionary to set all inputs to their default values
        self.updateFromParameters({})
        # Disable buttons to return to base state
        self.cmdCalculate.setEnabled(False)
        self.cmdStatus.setEnabled(False)

    def updateGuiFromFile(self, data=None):
        """
        update display in GUI and plot
        """
        self._data = data

        # plot loaded file
        if not isinstance(self._data, Data1D):
            msg = "Invariant cannot be computed with 2D data."
            raise ValueError(msg)

        try:
            name = data.name
        except:
            msg = 'No data name chosen.'
            raise ValueError(msg)
        try:
            qmin = min(self._data.x)
            qmax = max(self._data.x)
        except:
            msg = "Unable to find q min/max of \n data named %s" % \
                  data.name
            raise ValueError(msg)

        # update model with input form files: name, qmin, qmax
        self.model.item(WIDGETS.W_NAME).setText(name)
        self.model.item(WIDGETS.W_QMIN).setText(str(qmin))
        self.model.item(WIDGETS.W_QMAX).setText(str(qmax))
        self._path = data.filename

        self._calculator = invariant.InvariantCalculator(
            data=self._data, background=self._background, scale=self._scale)

        # Ensure extrapolated number of points and Q range are valid on data load
        self.txtNptsLowQ.setText(self.txtNptsLowQ.text())
        self.txtNptsHighQ.setText(self.txtNptsHighQ.text())
        self.checkQRange()

        # Calculate and add to GUI: volume fraction, invariant total,
        # and specific surface if porod checked
        if self.cmdCalculate.isEnabled():
            self.calculateInvariant()

    def serializeAll(self):
        """
        Serialize the invariant state so data can be saved
        Invariant is not batch-ready so this will only effect a single page
        :return: {data-id: {self.name: {invariant-state}}}
        """
        return self.serializeCurrentPage()

    def serializeCurrentPage(self):
        """
        Serialize and return a dictionary of {data_id: invariant-state}
        Return empty dictionary if no data
        :return: {data-id: {self.name: {invariant-state}}}
        """
        state = {}
        if self._data:
            tab_data = self.getPage()
            data_id = tab_data.pop('data_id', '')
            state[data_id] = {'invar_params': tab_data}
        return state

    def getPage(self) -> dict: # TODO: Better name, serializePage, pageData
        """
        Serializes full state of this invariant page
        Called by Save Analysis
        :return: {invariant-state}
        """
        # Get all parameters from page
        param_dict = self.getState()
        if self._data:
            param_dict['data_name'] = str(self._data.name)
            param_dict['data_id'] = str(self._data.id)
        return param_dict

    def getState(self): # TODO: Better name, serializeState, stateData
        """
        Collects all active params into a dictionary of {name: value}
        :return: {name: value}
        """
        # Be sure model has been updated
        self.updateFromModel()
        return {
            'extrapolated_q_min': self.txtExtrapolQMin.text(),
            'extrapolated_q_max': self.txtExtrapolQMax.text(),
            'vol_fraction': self.txtVolFract.text(),
            'vol_fraction_err': self.txtVolFractErr.text(),
            'specific_surface': self.txtSpecSurf.text(),
            'specific_surface_err': self.txtSpecSurfErr.text(),
            'invariant_total': self.txtInvariantTot.text(),
            'invariant_total_err': self.txtInvariantTotErr.text(),
            'background': self.txtBackgd.text(),
            'contrast': self.txtContrast.text(),
            'scale': self.txtScale.text(),
            'porod': self.txtPorodCst.text(),
            'low_extrapolate': self.chkLowQ.isChecked(),
            'low_points': self.txtNptsLowQ.text(),
            'low_guinier': self.rbGuinier.isChecked(),
            'low_fit_rb': self.rbFitLowQ.isChecked(),
            'low_power_value': self.txtPowerLowQ.text(),
            'high_extrapolate': self.chkHighQ.isChecked(),
            'high_points': self.txtNptsHighQ.text(),
            'high_fit_rb': self.rbFitHighQ.isChecked(),
            'high_power_value': self.txtPowerHighQ.text(),
            'total_q_min': self.txtTotalQMin.text(),
            'total_q_max': self.txtTotalQMax.text(),
        }

    def updateFromParameters(self, params):
        """
        Called by Open Project and Open Analysis
        :param params: {param_name: value}
        :return: None
        """
        # Params should be a dictionary
        if not isinstance(params, dict):
            c_name = params.__class__.__name__
            msg = "Invariant.updateFromParameters expects a dictionary"
            raise TypeError(f"{msg}: {c_name} received")
        # Assign values to 'Invariant' tab inputs - use defaults if not found
        self.txtTotalQMin.setText(str(params.get('total_q_min', '0.0')))
        self.txtTotalQMax.setText(str(params.get('total_q_max', '0.0')))
        self.txtExtrapolQMax.setText(str(params.get('extrapolated_q_max',
                                                    Q_MAXIMUM)))
        self.txtExtrapolQMin.setText(str(params.get('extrapolated_q_min',
                                                    Q_MINIMUM)))
        self.txtVolFract.setText(str(params.get('vol_fraction', '')))
        self.txtVolFractErr.setText(str(params.get('vol_fraction_err', '')))
        self.txtSpecSurf.setText(str(params.get('specific_surface', '')))
        self.txtSpecSurfErr.setText(str(params.get('specific_surface_err', '')))
        self.txtInvariantTot.setText(str(params.get('invariant_total', '')))
        self.txtInvariantTotErr.setText(
            str(params.get('invariant_total_err', '')))
        # Assign values to 'Options' tab inputs - use defaults if not found
        self.txtBackgd.setText(str(params.get('background', '0.0')))
        self.txtScale.setText(str(params.get('scale', '1.0')))
        self.txtContrast.setText(str(params.get('contrast', '8e-06')))
        self.txtPorodCst.setText(str(params.get('porod', '0.0')))
        # Toggle extrapolation buttons to enable other inputs
        self.chkLowQ.setChecked(params.get('low_extrapolate', False))
        self.chkHighQ.setChecked(params.get('high_extrapolate', False))
        self.txtPowerLowQ.setText(
            str(params.get('low_power_value', DEFAULT_POWER_LOW)))
        self.txtNptsLowQ.setText(
            str(params.get('low_points', NPOINTS_Q_INTERP)))
        self.rbGuinier.setChecked(params.get('low_guinier', True))
        self.rbFitLowQ.setChecked(params.get('low_fit_rb', False))
        self.txtNptsHighQ.setText(
            str(params.get('high_points', NPOINTS_Q_INTERP)))
        self.rbFitHighQ.setChecked(params.get('high_fit_rb', True))
        self.txtPowerHighQ.setText(
            str(params.get('high_power_value', DEFAULT_POWER_LOW)))
        # Update once all inputs are changed
        self.updateFromModel()
        self.plotResult(self.model)

    def allowBatch(self):
        """
        Tell the caller that we don't accept multiple data instances
        """
        return False

    def allowSwap(self):
        """
        Tell the caller that we can't swap data
        """
        return False
