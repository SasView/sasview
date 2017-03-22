# global
import sys
import os
from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import QtWebKit

from twisted.internet import threads
from twisted.internet import reactor

# sas-global
from sas.sascalc.invariant import invariant
from sas.sasgui.guiframe.dataFitting import Data1D
#import GuiUtils
import sas.qtgui.GuiUtils as GuiUtils

# local
from UI.TabbedInvariantUI import Ui_tabbedInvariantUI
from InvariantDetails import DetailsDialog
from InvariantUtils import WIDGETS

# The minimum q-value to be used when extrapolating
Q_MINIMUM = 1e-5
# The maximum q-value to be used when extrapolating
Q_MAXIMUM = 10
# the ratio of maximum q value/(qmax of data) to plot the theory data
Q_MAXIMUM_PLOT = 3


class MyModel(object):
    def __init__(self):
        self._model = QtGui.QStandardItemModel(self)

    def addItem(self, item):
        item = QtGui.QStandardItem(str(item))
        self._model.appendRow(item)

class InvariantWindow(QtGui.QDialog, Ui_tabbedInvariantUI):
    # The controller which is responsible for managing signal slots connections
    # for the gui and providing an interface to the data model.
    name = "Invariant" # For displaying in the combo box
    #def __init__(self, manager=None, parent=None):
    def __init__(self, parent=None):
        #super(InvariantWindow, self).__init__(parent)
        super(InvariantWindow, self).__init__()
        self.setupUi(self)

        self.setWindowTitle("Invariant Perspective")

        # initial input params
        self._background = 0.0
        self._scale = 1.0
        self._contrast = 1.0
        self._porod = 1.0
        self._npoints_low = 10
        self._npoints_high = 10
        self._power_low = 4

        self._manager = parent
        #self._manager = manager
        self._reactor = self._manager.reactor()
        self._model_item = QtGui.QStandardItem()

        self._helpView = QtWebKit.QWebView()
        self.detailsDialog = DetailsDialog(self)

        self._low_extrapolate = False
        self._low_guinier  = True
        self._low_fit  = True
        self._high_extrapolate = False
        self._high_power_value  = False

        # no reason to have this widget resizable
        self.setFixedSize(self.minimumSizeHint())

        self.communicate = GuiUtils.Communicate()

        self._data = None
        self._path = ""

        # Mask file selector
        ###################################################
        #self._path = "cyl_400_20.txt"
        #from sas.sascalc.dataloader.loader import  Loader
        #loader = Loader()
        #try:
        #    self._data = loader.load(self._path)
        #except:
        #    raise
        ###################################################

        self.lineEdit_8.setText(str(Q_MINIMUM))
        self.lineEdit_9.setText(str(Q_MAXIMUM))

        # Let's choose the Standard Item Model.
        self.model = QtGui.QStandardItemModel(self)

        # Connect buttons to slots.
        # Needs to be done early so default values propagate properly.
        self.setupSlots()

        # Set up the model.
        self.setupModel()

        # Set up the mapper
        self.setupMapper()

    #def closeEvent(self, event):
    #    """
    #    Overwrite the default close method of QWidget
    #    """
    #    # No close on perspectives - one must always be active.
    #    event.ignore()

    def communicator(self):
        """ Getter for the communicator """
        return self.communicate

    def updateFromModel(self):
        """
        update the globals based on the data in the model
        """
        self._background = float(self.model.item(WIDGETS.W_BACKGROUND).text())
        self._contrast   = float(self.model.item(WIDGETS.W_CONTRAST).text())
        self._scale      = float(self.model.item(WIDGETS.W_SCALE).text())

        # High extrapolate
        self._low_extrapolate = ( str(self.model.item(WIDGETS.W_ENABLE_LOWQ).text()) == 'true')
        self._low_points = float(self.model.item(WIDGETS.W_NPTS_LOWQ).text())
        self._low_guinier  = ( str(self.model.item(WIDGETS.W_LOWQ_GUINIER).text()) == 'true')
        self._low_fit  = ( str(self.model.item(WIDGETS.W_LOWQ_FIT).text()) == 'true')
        self._low_power_value  = float(self.model.item(WIDGETS.W_LOWQ_POWER_VALUE).text())

        # High extrapolating
        self._high_extrapolate = ( str(self.model.item(WIDGETS.W_ENABLE_HIGHQ).text()) == 'true')
        self._high_points  = float(self.model.item(WIDGETS.W_NPTS_HIGHQ).text())
        self._high_fit  = ( str(self.model.item(WIDGETS.W_HIGHQ_FIT).text()) == 'true')
        self._high_power_value  = float(self.model.item(WIDGETS.W_HIGHQ_POWER_VALUE).text())

    def calculateInvariant(self):
        """
        Use twisted to thread the calculations away.
        """
        # Find out if extrapolation needs to be used.
        extrapolation = None
        if self._low_extrapolate  and not self._high_extrapolate:
            extrapolation = "low"
        elif not self._low_extrapolate  and self._high_extrapolate:
            extrapolation = "high"
        elif self._low_extrapolate and self._high_extrapolate:
            extrapolation = "both"
        try:
            # modify the Calculate button to indicate background process
            self.pushButton.setText("Calculating...")
            self.pushButton.setEnabled(False)
            self.style = self.pushButton.styleSheet()
            self.pushButton.setStyleSheet("background-color: rgb(255, 255, 0); color: rgb(0, 0, 0)")
            # Send the calculations to separate thread.
            d = threads.deferToThread(self.calculateThread, extrapolation)
            # Add deferred callback for call return
            d.addCallback(self.plotResult)
        except Exception as ex:
            # Set the button back to available
            self.pushButton.setEnabled(True)
            self.pushButton.setText("Calculate")
            self.pushButton.setStyleSheet(self.style)


    def plotResult(self, model):
        """
        """
        self.model = model
        self.mapper.toFirst()

        # Set the button back to available
        self.pushButton.setEnabled(True)
        self.pushButton.setText("Calculate")
        self.pushButton.setStyleSheet(self.style)

        # Send the modified model item to DE for keeping in the model
        self.communicate.updateModelFromPerspectiveSignal.emit(self._model_item)


    def calculateThread(self, extrapolation):
        """
        Perform Invariant calculations.

        TODO: Create a dictionary of results to be sent to DE on completion.
        """
        self.updateFromModel()

        qstar_low = 0.0
        qstar_low_err = 0.0
        qstar_high = 0.0
        qstar_high_err = 0.0
        qstar_total = 0.0
        qstar_total_low_err = 0.0

        # Prepare the invariant object
        inv = invariant.InvariantCalculator(data=self._data,
                                            background = self._background,
                                            scale = self._scale)

        if self._low_extrapolate:
            function_low = "power_law"
            if self._low_guinier:
                function_low = "guinier"
            if self._low_fit:
                self._low_power_value = None
            inv.set_extrapolation(range="low",
                                  npts=self._low_points,
                                  function=function_low,
                                  power=self._low_power_value)

        if self._high_extrapolate:
            function_low = "power_law"
            inv.set_extrapolation(range="high",
                                  npts=self._high_points,
                                  function=function_low,
                                  power=self._low_power_value)

        #Compute invariant
        # TODO: proper exception handling and logic -
        # display info, update lineedits, don't run extrapolations etc.
        calculation_failed = False
        try:
            qstar_total, qstar_total_error         = inv.get_qstar_with_error()
        except Exception as ex:
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
            # Display relevant information
            item = QtGui.QStandardItem("ERROR")
            self.model.setItem(WIDGETS.W_VOLUME_FRACTION, item)
            item = QtGui.QStandardItem("ERROR")
            self.model.setItem(WIDGETS.W_VOLUME_FRACTION_ERR, item)
        try:
            surface, surface_error = \
                inv.get_surface_with_error(self._contrast, self._porod)
        except Exception as ex:
            calculation_failed = True
            # Display relevant information
            item = QtGui.QStandardItem("ERROR")
            self.model.setItem(WIDGETS.W_SPECIFIC_SURFACE, item)
            item = QtGui.QStandardItem("ERROR")
            self.model.setItem(WIDGETS.W_SPECIFIC_SURFACE_ERR, item)

        if(calculation_failed):
            # TODO: NOTIFY THE GUI MANAGER!!
            self.mapper.toFirst()
            return self.model

        if self._low_extrapolate:
            # for presentation in InvariantDetails
            qstar_low, qstar_low_err = inv.get_qstar_low()
            extrapolated_data = inv.get_extra_data_low(self._low_points)
            power_low = inv.get_extrapolation_power(range='low')

            #inv.data = extrapolated_data
            #qstar_total, qstar_total_error = inv.get_qstar_with_error()

            # Plot the chart
            title = "Low-Q extrapolation"

            # Convert the data into plottable
            extrapolated_data = self._manager.createGuiData(extrapolated_data)
            extrapolated_data.name = title
            extrapolated_data.title = title

            # Add the plot to the model item
            # variant_item = QtCore.QVariant(self._plotter)
            variant_item = QtCore.QVariant(extrapolated_data)

            # This needs to run in the main thread
            reactor.callFromThread(GuiUtils.updateModelItemWithPlot,
                    self._model_item, variant_item, title)

        if self._high_extrapolate:
            # for presentation in InvariantDetails
            qmax_plot = Q_MAXIMUM_PLOT * max(self._data.x)
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

            # Add the plot to the model item
            # variant_item = QtCore.QVariant(self._plotter)
            variant_item = QtCore.QVariant(high_out_data)
            # This needs to run in the main thread
            reactor.callFromThread(GuiUtils.updateModelItemWithPlot,
                    self._model_item, variant_item, title)

        item = QtGui.QStandardItem(str(float('%.5g'% volume_fraction)))
        self.model.setItem(WIDGETS.W_VOLUME_FRACTION, item)
        item = QtGui.QStandardItem(str(float('%.5g'% volume_fraction_error)))
        self.model.setItem(WIDGETS.W_VOLUME_FRACTION_ERR, item)
        item = QtGui.QStandardItem(str(float('%.5g'% surface)))
        self.model.setItem(WIDGETS.W_SPECIFIC_SURFACE, item)
        item = QtGui.QStandardItem(str(float('%.5g'% surface_error)))
        self.model.setItem(WIDGETS.W_SPECIFIC_SURFACE_ERR, item)
        item = QtGui.QStandardItem(str(float('%.5g'% qstar_total)))
        self.model.setItem(WIDGETS.W_INVARIANT, item)
        item = QtGui.QStandardItem(str(float('%.5g'% qstar_total_error)))
        self.model.setItem(WIDGETS.W_INVARIANT_ERR, item)

        #item = QtGui.QStandardItem(str(float('%.5g'% qstar_total)))
        #self.model.setItem(WIDGETS.D_TOTAL_QSTAR, item)
        #item = QtGui.QStandardItem(str(float('%.5g'% qstar_total_err)))
        #self.model.setItem(WIDGETS.D_TOTAL_QSTAR_ERR, item)
        item = QtGui.QStandardItem(str(float('%.5g'% qstar_low)))
        self.model.setItem(WIDGETS.D_LOW_QSTAR, item)
        item = QtGui.QStandardItem(str(float('%.5g'% qstar_low_err)))
        self.model.setItem(WIDGETS.D_LOW_QSTAR_ERR, item)
        item = QtGui.QStandardItem(str(float('%.5g'% qstar_high)))
        self.model.setItem(WIDGETS.D_HIGH_QSTAR, item)
        item = QtGui.QStandardItem(str(float('%.5g'% qstar_high_err)))
        self.model.setItem(WIDGETS.D_HIGH_QSTAR_ERR, item)

        self.mapper.toFirst()

        return self.model
                
    def title(self):
        """
        Perspective name
        """
        return "Invariant panel"

    def status(self):
        """
        """
        self.detailsDialog.setModel(self.model)
        self.detailsDialog.showDialog()

    def help(self):
        """
        """
        _TreeLocation = self._manager.HELP_DIRECTORY_LOCATION + \
            "/user/sasgui/perspectives/invariant/invariant_help.html"
        self._helpView.load(QtCore.QUrl(_TreeLocation))
        self._helpView.show()

    def setupSlots(self):
        self.pushButton.clicked.connect(self.calculateInvariant)
        self.pushButton_2.clicked.connect(self.status)
        self.pushButton_3.clicked.connect(self.help)

        self.radioButton.toggled.connect(self.lowGuinierAndPowerToggle)
        self.radioButton_8.toggled.connect(self.hiFitAndFixToggle)

        self.radioButton_3.toggled.connect(self.lowFitAndFixToggle)

        # Bug workaround for QDataWidgetMapper() not reacting to checkbox clicks.
        # https://bugreports.qt.io/browse/QTBUG-1818
        self.checkBox.clicked.connect(self.setFocus)
        self.checkBox_2.clicked.connect(self.setFocus)

        self.model.itemChanged.connect(self.modelChanged)

    def modelChanged(self, item):
        """
        """
        if item.row() == WIDGETS.W_ENABLE_LOWQ:
            toggle = (str(item.text()) == 'true')
            self._low_extrapolate = toggle
            self.lowQToggle(toggle)
        elif item.row() == WIDGETS.W_ENABLE_HIGHQ:
            toggle = (str(item.text()) == 'true')
            self._high_extrapolate = toggle
            self.highQToggle(toggle)
        
    def lowGuinierAndPowerToggle(self, toggle):
        """
        """
        self._low_guinier = toggle
        toggle = not toggle
        self.lineEdit_11.setEnabled(toggle)
        self.radioButton_3.setEnabled(toggle)
        self.radioButton_4.setEnabled(toggle)
        self.lineEdit_11.setEnabled(toggle and (not self._low_fit))

    def lowFitAndFixToggle(self, toggle):
        """
        """
        self._low_fit = toggle
        toggle = not toggle
        self.lineEdit_11.setEnabled(toggle)

    def hiFitAndFixToggle(self, toggle):
        """
        """
        self.lineEdit_13.setEnabled(toggle)

    def highQToggle(self, clicked):
        """
        Disable/enable High Q extrapolation
        """
        self.radioButton_7.setEnabled(clicked)
        self.radioButton_8.setEnabled(clicked)
        self.lineEdit_12.setEnabled(clicked)
        self.lineEdit_13.setEnabled(clicked)

    def lowQToggle(self, clicked):
        """
        Disable/enable Low Q extrapolation
        """
        self.radioButton.setEnabled(clicked)
        self.radioButton_2.setEnabled(clicked)
        self.lineEdit_11.setEnabled(clicked and not self._low_fit)

        # Enable subelements
        self.radioButton_3.setEnabled(clicked and not self._low_guinier)
        self.radioButton_4.setEnabled(clicked and not self._low_guinier)
        self.lineEdit_10.setEnabled(clicked and not self._low_guinier)

    def setupModel(self):

        # filename
        item = QtGui.QStandardItem(self._path)
        self.model.setItem(WIDGETS.W_FILENAME, item)

        # add Q parameters to the model
        #qmin = min(self._data.x)
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
        
        # Dialog elements
        itemf = QtGui.QStandardItem("false")
        self.model.setItem(WIDGETS.W_ENABLE_HIGHQ, itemf)
        itemf = QtGui.QStandardItem("false")
        self.model.setItem(WIDGETS.W_ENABLE_LOWQ, itemf)

        item = QtGui.QStandardItem(str(self._npoints_low))
        self.model.setItem(WIDGETS.W_NPTS_LOWQ, item)
        item = QtGui.QStandardItem(str(self._npoints_high))
        self.model.setItem(WIDGETS.W_NPTS_HIGHQ, item)

        itemt = QtGui.QStandardItem("true")
        self.model.setItem(WIDGETS.W_LOWQ_GUINIER, itemt)

        itemt = QtGui.QStandardItem("true")
        self.model.setItem(WIDGETS.W_LOWQ_FIT, itemt)
        item = QtGui.QStandardItem(str(self._power_low))
        self.model.setItem(WIDGETS.W_LOWQ_POWER_VALUE, item)

        itemt = QtGui.QStandardItem("true")
        self.model.setItem(WIDGETS.W_HIGHQ_FIT, itemt)
        item = QtGui.QStandardItem(str(self._power_low))
        self.model.setItem(WIDGETS.W_HIGHQ_POWER_VALUE, item)


    def setupMapper(self):
        # Set up the mapper.
        self.mapper = QtGui.QDataWidgetMapper(self)
        self.mapper.setOrientation(QtCore.Qt.Vertical)
        self.mapper.setModel(self.model)

        # Set up the view on the model for testing
        # self.tableView.setModel(self.model)

        # Filename
        self.mapper.addMapping(self.lineEdit, WIDGETS.W_FILENAME)
        # Qmin/Qmax
        self.mapper.addMapping(self.lineEdit_2, WIDGETS.W_QMIN)
        self.mapper.addMapping(self.lineEdit_3, WIDGETS.W_QMAX)

        # Background
        self.mapper.addMapping(self.lineEdit_4, WIDGETS.W_BACKGROUND)
        # Scale
        self.mapper.addMapping(self.lineEdit_5, WIDGETS.W_SCALE)
        # Contrast
        self.mapper.addMapping(self.lineEdit_6, WIDGETS.W_CONTRAST)

        # Lowq/Highq items
        self.mapper.addMapping(self.checkBox, WIDGETS.W_ENABLE_LOWQ)
        self.mapper.addMapping(self.checkBox_2, WIDGETS.W_ENABLE_HIGHQ)

        self.mapper.addMapping(self.lineEdit_10, WIDGETS.W_NPTS_LOWQ)
        self.mapper.addMapping(self.radioButton, WIDGETS.W_LOWQ_GUINIER)

        self.mapper.addMapping(self.radioButton_3, WIDGETS.W_LOWQ_FIT)
        self.mapper.addMapping(self.lineEdit_11, WIDGETS.W_LOWQ_POWER_VALUE)

        self.mapper.addMapping(self.radioButton_7, WIDGETS.W_HIGHQ_FIT)
        self.mapper.addMapping(self.lineEdit_13, WIDGETS.W_HIGHQ_POWER_VALUE)
    
        # Output
        self.mapper.addMapping(self.lineEdit_14, WIDGETS.W_VOLUME_FRACTION)
        self.mapper.addMapping(self.lineEdit_15, WIDGETS.W_VOLUME_FRACTION_ERR)
        self.mapper.addMapping(self.lineEdit_16, WIDGETS.W_SPECIFIC_SURFACE)
        self.mapper.addMapping(self.lineEdit_17, WIDGETS.W_SPECIFIC_SURFACE_ERR)
        self.mapper.addMapping(self.lineEdit_19, WIDGETS.W_INVARIANT)
        self.mapper.addMapping(self.lineEdit_18, WIDGETS.W_INVARIANT_ERR)

        self.mapper.toFirst()

    def setData(self, data_item):
        """
        Obtain a QStandardItem object and dissect it to get Data1D/2D
        Pass it over to the calculator
        """
        if not isinstance(data_item, list):
            msg = "Incorrect type passed to the Invariant Perspective"
            raise AttributeError, msg

        if not isinstance(data_item[0], QtGui.QStandardItem):
            msg = "Incorrect type passed to the Invariant Perspective"
            raise AttributeError, msg

        self._model_item = data_item[0]

        # Extract data on 1st child - this is the Data1D/2D component
        data = GuiUtils.dataFromItem(self._model_item)
        self.model.item(WIDGETS.W_FILENAME).setData(QtCore.QVariant(self._model_item.text()))

        ##### DEBUG ####
        # set data in the debug tree view window
        self.treeView.setModel(self.model)

        self.calculate(data_list=[data])
        
    def calculate(self, data_list=None):
        """
        receive a list of data and compute invariant

        TODO: pass warnings/messages to log
        """
        msg = ""
        data = None
        if data_list is None:
            data_list = []
        if len(data_list) >= 1:
            if len(data_list) == 1:
                data = data_list[0]
            else:
                data_1d_list = []
                data_2d_list = []
                error_msg = ""
                # separate data into data1d and data2d list
                for data in data_list:
                    if data is not None:
                        if issubclass(data.__class__, Data1D):
                            data_1d_list.append(data)
                        else:
                            error_msg += " %s  type %s \n" % (str(data.name),
                                                              str(data.__class__.__name__))
                            data_2d_list.append(data)
                if len(data_2d_list) > 0:
                    msg = "Invariant does not support the following data types:\n"
                    msg += error_msg
                if len(data_1d_list) == 0:
                    # remake this as a qt event
                    #wx.PostEvent(self.parent, StatusEvent(status=msg, info='error'))
                    return

                # TODO: add msgbox for data choice
                #msg += "Invariant panel does not allow multiple data!\n"
                #msg += "Please select one.\n"
                #if len(data_list) > 1:
                    #from invariant_widgets import DataDialog
                    #dlg = DataDialog(data_list=data_1d_list, text=msg)
                    #if dlg.ShowModal() == wx.ID_OK:
                    #    data = dlg.get_data()
                    #else:
                    #    data = None
                    #dlg.Destroy()

            if data is None:
                msg += "invariant receives no data. \n"
                #wx.PostEvent(self.parent, StatusEvent(status=msg, info='error'))
                return
            if not issubclass(data.__class__, Data1D):
                msg += "invariant cannot be computed for data of "
                msg += "type %s\n" % (data.__class__.__name__)
                #wx.PostEvent(self.parent, StatusEvent(status=msg, info='error'))
                return
            else:
                #wx.PostEvent(self.parent, NewPlotEvent(plot=data, title=data.title))
                try:
                    self._data = data
                    self._path = "unique path"
                    self.calculateInvariant()
                except:
                    msg = "Invariant Set_data: " + str(sys.exc_value)
                    #wx.PostEvent(self.parent, StatusEvent(status=msg, info="error"))
        else:
            msg = "invariant cannot be computed for data of "
            msg += "type %s" % (data.__class__.__name__)
            #wx.PostEvent(self.parent, StatusEvent(status=msg, info='error'))

    def allowBatch(self):
        """
        Tell the caller that we don't accept multiple data instances
        """
        return False

if __name__ == "__main__":
    app = QtGui.QApplication([])
    import qt4reactor
    qt4reactor.install()
    # DO NOT move the following import to the top!
    # (unless you know what you're doing)
    from twisted.internet import reactor
    dlg = InvariantWindow(reactor)
    dlg.show()
    reactor.run()