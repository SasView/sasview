# global
import sys
import os
import logging
import copy
import webbrowser

from PyQt5 import QtCore
from PyQt5 import QtGui, QtWidgets

from twisted.internet import threads
from twisted.internet import reactor

# sas-global
from sas.sascalc.invariant import invariant
from sas.qtgui.Plotting.PlotterData import Data1D
import sas.qtgui.Utilities.GuiUtils as GuiUtils

# import sas.qtgui.Plotting.PlotHelper as PlotHelper

# local
from .UI.TabbedInvariantUI import Ui_tabbedInvariantUI
from .InvariantDetails import DetailsDialog
from .InvariantUtils import WIDGETS

# The minimum q-value to be used when extrapolating
Q_MINIMUM = 1e-5
# The maximum q-value to be used when extrapolating
Q_MAXIMUM = 10
# the ratio of maximum q value/(qmax of data) to plot the theory data
Q_MAXIMUM_PLOT = 3
# Default number of points of interpolation: high and low range
NPOINTS_Q_INTERP = 10
# Default power law for interpolation
DEFAULT_POWER_LOW = 4

# Background of line edits if settings OK or wrong
BG_WHITE = "background-color: rgb(255, 255, 255);"
BG_RED = "background-color: rgb(244, 170, 164);"

class InvariantWindow(QtWidgets.QDialog, Ui_tabbedInvariantUI):
    # The controller which is responsible for managing signal slots connections
    # for the gui and providing an interface to the data model.
    name = "Invariant"  # For displaying in the combo box in DataExplorer

    def __init__(self, parent=None):
        super(InvariantWindow, self).__init__()
        self.setupUi(self)

        self.setWindowTitle("Invariant Perspective")

        # initial input params
        self._background = 0.0
        self._scale = 1.0
        self._contrast = 1.0
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
        self._low_power_value = False
        self._low_points = NPOINTS_Q_INTERP
        self._low_power_value = DEFAULT_POWER_LOW

        self._high_extrapolate = False
        self._high_power_value = False
        self._high_fit = False
        self._high_points = NPOINTS_Q_INTERP
        self._high_power_value = DEFAULT_POWER_LOW

        # no reason to have this widget resizable
        self.resize(self.minimumSizeHint())

        self.communicate = self._manager.communicator()

        self._data = None
        self._path = ""

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

        self.txtExtrapolQMin.setText(str(Q_MINIMUM))
        self.txtExtrapolQMax.setText(str(Q_MAXIMUM))

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
        self.txtBackgd.setValidator(GuiUtils.DoubleValidator())
        self.txtContrast.setValidator(GuiUtils.DoubleValidator())
        self.txtScale.setValidator(GuiUtils.DoubleValidator())
        self.txtPorodCst.setValidator(GuiUtils.DoubleValidator())

        # validator: integer number
        self.txtNptsLowQ.setValidator(QtGui.QIntValidator())
        self.txtNptsHighQ.setValidator(QtGui.QIntValidator())
        self.txtPowerLowQ.setValidator(GuiUtils.DoubleValidator())
        self.txtPowerHighQ.setValidator(GuiUtils.DoubleValidator())

    def enabling(self):
        """ """
        self.cmdStatus.setEnabled(True)

    def setClosable(self, value=True):
        """ Allow outsiders close this widget """
        assert isinstance(value, bool)

        self._allow_close = value

    def closeEvent(self, event):
        """
        Overwrite QDialog close method to allow for custom widget close
        """
        if self._allow_close:
            # reset the closability flag
            self.setClosable(value=False)
            # Tell the MdiArea to close the container
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
        if self.model.item(WIDGETS.W_POROD_CST).text() != 'None' \
                and self.model.item(WIDGETS.W_POROD_CST).text() != '':
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

    def calculateInvariant(self):
        """ Use twisted to thread the calculations away """
        # Find out if extrapolation needs to be used.
        extrapolation = None
        if self._low_extrapolate and not self._high_extrapolate:
            extrapolation = "low"
        elif not self._low_extrapolate and self._high_extrapolate:
            extrapolation = "high"
        elif self._low_extrapolate and self._high_extrapolate:
            extrapolation = "both"

        # modify the Calculate button to indicate background process
        self.cmdCalculate.setText("Calculating...")
        self.cmdCalculate.setEnabled(False)

        # Send the calculations to separate thread.
        d = threads.deferToThread(self.calculateThread, extrapolation)

        # Add deferred callback for call return
        d.addCallback(self.deferredPlot)
        d.addErrback(self.calculationFailed)

    def calculationFailed(self, reason):
        print("calculation failed: ", reason)
        pass

    def deferredPlot(self, model):
        """
        Run the GUI/model update in the main thread
        """
        reactor.callFromThread(lambda: self.plotResult(model))

    def plotResult(self, model):
        """ Plot result of calculation """
        # Set the button back to available
        self.cmdCalculate.setEnabled(True)
        self.cmdCalculate.setText("Calculate")
        self.cmdStatus.setEnabled(True)

        self.model = model
        self.mapper.toFirst()
        self._data = GuiUtils.dataFromItem(self._model_item)

        # Send the modified model item to DE for keeping in the model
        # Currently -unused
        # self.communicate.updateModelFromPerspectiveSignal.emit(self._model_item)

        plot_data = GuiUtils.plotsFromCheckedItems(self._manager.filesWidget.model)

        self._manager.filesWidget.plotData(plot_data)

        # Update the details dialog in case it is open
        self.updateDetailsWidget(model)

    def updateDetailsWidget(self, model):
        """
        On demand update of the details widget
        """
        if self.detailsDialog.isVisible():
            self.onStatus()

    def calculateThread(self, extrapolation):
        """
        Perform Invariant calculations.
        TODO: Create a dictionary of results to be sent to DE on completion.
        """
        self.updateFromModel()
        msg = ''

        qstar_low = 0.0
        qstar_low_err = 0.0
        qstar_high = 0.0
        qstar_high_err = 0.0
        qstar_total = 0.0
        qstar_total_error = 0.0

        temp_data = copy.deepcopy(self._data)

        # Prepare the invariant object
        inv = invariant.InvariantCalculator(data=temp_data,
                                            background=self._background,
                                            scale=self._scale)
        if self._low_extrapolate:

            function_low = "power_law"
            if self._low_guinier:
                function_low = "guinier"
            if self._low_fit:
                self._low_power_value = None

            inv.set_extrapolation(range="low",
                                  npts=int(self._low_points),
                                  function=function_low,
                                  power=self._low_power_value)

        if self._high_extrapolate:
            function_low = "power_law"
            inv.set_extrapolation(range="high",
                                  npts=int(self._high_points),
                                  function=function_low,
                                  power=self._high_power_value)
        # Compute invariant
        calculation_failed = False

        try:
            qstar_total, qstar_total_error = inv.get_qstar_with_error()
        except Exception as ex:
            msg += str(ex)
            calculation_failed = True
            # Display relevant information
            item = QtGui.QStandardItem("ERROR")
            self.model.setItem(WIDGETS.W_INVARIANT, item)
            item = QtGui.QStandardItem("ERROR")
            self.model.setItem(WIDGETS.W_INVARIANT_ERR, item)

        try:
            volume_fraction, volume_fraction_error = \
                inv.get_volume_fraction_with_error(self._contrast)

        except Exception as ex:
            calculation_failed = True
            msg += str(ex)
            # Display relevant information
            item = QtGui.QStandardItem("ERROR")
            self.model.setItem(WIDGETS.W_VOLUME_FRACTION, item)
            item = QtGui.QStandardItem("ERROR")
            self.model.setItem(WIDGETS.W_VOLUME_FRACTION_ERR, item)

        if self._porod:
            try:
                surface, surface_error = \
                    inv.get_surface_with_error(self._contrast, self._porod)
            except Exception as ex:
                calculation_failed = True
                msg += str(ex)
                # Display relevant information
                item = QtGui.QStandardItem("ERROR")
                self.model.setItem(WIDGETS.W_SPECIFIC_SURFACE, item)
                item = QtGui.QStandardItem("ERROR")
                self.model.setItem(WIDGETS.W_SPECIFIC_SURFACE_ERR, item)
        else:
            surface = None

        if (calculation_failed):
            logging.warning('Calculation failed: {}'.format(msg))
            return self.model
        else:

            if self._low_extrapolate:
                # for presentation in InvariantDetails
                qstar_low, qstar_low_err = inv.get_qstar_low()
                extrapolated_data = inv.get_extra_data_low(self._low_points)
                power_low = inv.get_extrapolation_power(range='low')

                # Plot the chart
                title = "Low-Q extrapolation"

                # Convert the data into plottable
                extrapolated_data = self._manager.createGuiData(extrapolated_data)

                extrapolated_data.name = title
                extrapolated_data.title = title

                # copy labels and units of axes for plotting
                extrapolated_data._xaxis = temp_data._xaxis
                extrapolated_data._xunit = temp_data._xunit
                extrapolated_data._yaxis = temp_data._yaxis
                extrapolated_data._yunit = temp_data._yunit

                # Add the plot to the model item
                # This needs to run in the main thread
                reactor.callFromThread(GuiUtils.updateModelItemWithPlot,
                                       self._model_item,
                                       extrapolated_data,
                                       title)

            if self._high_extrapolate:
                # for presentation in InvariantDetails
                qmax_plot = Q_MAXIMUM_PLOT * max(temp_data.x)

                if qmax_plot > Q_MAXIMUM:
                    qmax_plot = Q_MAXIMUM
                qstar_high, qstar_high_err = inv.get_qstar_high()
                power_high = inv.get_extrapolation_power(range='high')
                high_out_data = inv.get_extra_data_high(q_end=qmax_plot, npts=500)

                # Plot the chart
                title = "High-Q extrapolation"

                # Convert the data into plottable
                high_out_data = self._manager.createGuiData(high_out_data)
                high_out_data.name = title
                high_out_data.title = title

                # copy labels and units of axes for plotting
                high_out_data._xaxis = temp_data._xaxis
                high_out_data._xunit = temp_data._xunit
                high_out_data._yaxis = temp_data._yaxis
                high_out_data._yunit = temp_data._yunit

                # Add the plot to the model item
                # This needs to run in the main thread
                reactor.callFromThread(GuiUtils.updateModelItemWithPlot,
                                       self._model_item, high_out_data, title)

            item = QtGui.QStandardItem(str(float('%.3g'% volume_fraction)))
            self.model.setItem(WIDGETS.W_VOLUME_FRACTION, item)
            item = QtGui.QStandardItem(str(float('%.3g'% volume_fraction_error)))
            self.model.setItem(WIDGETS.W_VOLUME_FRACTION_ERR, item)
            if surface:
                item = QtGui.QStandardItem(str(float('%.3g'% surface)))
                self.model.setItem(WIDGETS.W_SPECIFIC_SURFACE, item)
                item = QtGui.QStandardItem(str(float('%.3g'% surface_error)))
                self.model.setItem(WIDGETS.W_SPECIFIC_SURFACE_ERR, item)
            item = QtGui.QStandardItem(str(float('%.3g'% qstar_total)))
            self.model.setItem(WIDGETS.W_INVARIANT, item)
            item = QtGui.QStandardItem(str(float('%.3g'% qstar_total_error)))
            self.model.setItem(WIDGETS.W_INVARIANT_ERR, item)

            item = QtGui.QStandardItem(str(float('%.3g'% qstar_low)))
            self.model.setItem(WIDGETS.D_LOW_QSTAR, item)
            item = QtGui.QStandardItem(str(float('%.3g'% qstar_low_err)))
            self.model.setItem(WIDGETS.D_LOW_QSTAR_ERR, item)
            item = QtGui.QStandardItem(str(float('%.3g'% qstar_high)))
            self.model.setItem(WIDGETS.D_HIGH_QSTAR, item)
            item = QtGui.QStandardItem(str(float('%.3g'% qstar_high_err)))
            self.model.setItem(WIDGETS.D_HIGH_QSTAR_ERR, item)

            return self.model

    def title(self):
        """ Perspective name """
        return "Invariant panel"

    def onStatus(self):
        """
        Display Invariant Details panel when clicking on Status button
        """
        self.detailsDialog.setModel(self.model)
        self.detailsDialog.showDialog()
        self.cmdStatus.setEnabled(False)

    def onHelp(self):
        """ Display help when clicking on Help button """
        treeLocation = "/user/sasgui/perspectives/invariant/invariant_help.html"
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
        if self.txtNptsLowQ.isEnabled():
            self.txtNptsLowQ.textChanged.connect(self.checkLength)

        if self.txtNptsHighQ.isEnabled():
            self.txtNptsHighQ.textChanged.connect(self.checkLength)

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
        try:
            int_value = int(self.sender().text())
        except ValueError:
            self.sender().setStyleSheet(BG_RED)
            self.cmdCalculate.setEnabled(False)
            return

        if self._data:
            if len(self._data.x) < int_value:
                self.sender().setStyleSheet(BG_RED)
                logging.warning('The number of points must be smaller than {}'.format(len(self._data.x)))
                self.cmdCalculate.setEnabled(False)
            else:
                self.sender().setStyleSheet(BG_WHITE)
                self.cmdCalculate.setEnabled(True)
        else:
            # logging.info('no data is loaded')
            self.cmdCalculate.setEnabled(False)

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
            self.cmdCalculate.setEnabled(True)
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
            self._low_guinier = toggle

            toggle = not toggle
            self.rbPowerLawLowQ.setChecked(toggle)

            self.rbFitLowQ.toggled.connect(self.lowFitAndFixToggle)
            self.rbFitLowQ.setVisible(toggle)
            self.rbFixLowQ.setVisible(toggle)

            self.txtPowerLowQ.setEnabled(toggle and (not self._low_fit))

        else:
            self._low_guinier = not toggle

            self.rbGuinier.setChecked(not toggle)

            self.rbFitLowQ.toggled.connect(self.lowFitAndFixToggle)
            self.rbFitLowQ.setVisible(toggle)
            self.rbFixLowQ.setVisible(toggle)

            self.txtPowerLowQ.setEnabled(toggle and (not self._low_fit))

    def lowFitAndFixToggle(self, toggle):
        """ Fit and Fix radiobuttons cannot be selected at the same time """
        self._low_fit = toggle

        toggle = not toggle
        self.txtPowerLowQ.setEnabled(toggle)

    def hiFitAndFixToggle(self, toggle):
        """
        Enable editing of power exponent if Fix for high Q is checked
        Disable otherwise
        """
        self.txtPowerHighQ.setEnabled(not toggle)

    def highQToggle(self, clicked):
        """ Disable/enable High Q extrapolation """
        self.rbFitHighQ.setEnabled(clicked)
        self.rbFixHighQ.setEnabled(clicked)
        self.txtNptsHighQ.setEnabled(clicked)
        self.txtPowerHighQ.setEnabled(clicked)

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
        self.model.setItem(WIDGETS.W_FILENAME, item)

        # add Q parameters to the model
        qmin = 0.0
        item = QtGui.QStandardItem(str(qmin))
        self.model.setItem(WIDGETS.W_QMIN, item)
        qmax = 0.0
        item = QtGui.QStandardItem(str(qmax))
        self.model.setItem(WIDGETS.W_QMAX, item)

        # add custom input params
        item = QtGui.QStandardItem(str(self._background))
        self.model.setItem(WIDGETS.W_BACKGROUND, item)
        item = QtGui.QStandardItem(str(self._contrast))
        self.model.setItem(WIDGETS.W_CONTRAST, item)
        item = QtGui.QStandardItem(str(self._scale))
        self.model.setItem(WIDGETS.W_SCALE, item)
        # leave line edit empty if Porod constant not defined
        if self._porod != None:
            item = QtGui.QStandardItem(str(self._porod))
        else:
            item = QtGui.QStandardItem(str(''))
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
        self.mapper.addMapping(self.txtName, WIDGETS.W_FILENAME)

        # Qmin/Qmax
        self.mapper.addMapping(self.txtTotalQMin, WIDGETS.W_QMIN)
        self.mapper.addMapping(self.txtTotalQMax, WIDGETS.W_QMAX)

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

        # Extract data on 1st child - this is the Data1D/2D component
        data = GuiUtils.dataFromItem(self._model_item)
        self.model.item(WIDGETS.W_FILENAME).setData(self._model_item.text())
        # update GUI and model with info from loaded data
        self.updateGuiFromFile(data=data)

    def updateGuiFromFile(self, data=None):
        """
        update display in GUI and plot
        """
        self._data = data

        # plot loaded file
        if not isinstance(self._data, Data1D):
            msg = "Error(s) occurred: Invariant cannot be computed with 2D data."
            raise AttributeError(msg)

        try:
            filename = data.filename
        except:
            msg = 'No filename'
            raise ValueError(msg)
        try:
            qmin = min(self._data.x)
            qmax = max(self._data.x)
        except:
            msg = "Unable to find q min/max of \n data named %s" % \
                  data.filename
            raise ValueError(msg)

        # update model with input form files: filename, qmin, qmax
        self.model.item(WIDGETS.W_FILENAME).setText(filename)
        self.model.item(WIDGETS.W_QMIN).setText(str(qmin))
        self.model.item(WIDGETS.W_QMAX).setText(str(qmax))
        self._path = filename

        # Calculate and add to GUI: volume fraction, invariant total,
        # and specific surface if porod checked
        self.calculateInvariant()

    def allowBatch(self):
        """
        Tell the caller that we don't accept multiple data instances
        """
        return False
